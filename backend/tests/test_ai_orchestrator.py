import pytest
from unittest.mock import AsyncMock, MagicMock
from api.ai.orchestrator import AIOrchestrator
from api.common.models import Game, GameState

class TestAIOrchestrator:
    """Unit tests for AI orchestrator pipeline."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        mock = AsyncMock()
        # Set up async context manager for begin()
        begin_cm = MagicMock()
        begin_cm.__aenter__ = AsyncMock()
        begin_cm.__aexit__ = AsyncMock()
        mock.begin = MagicMock(return_value=begin_cm)
        return mock

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client."""
        redis = MagicMock()
        lock_mock = MagicMock()
        lock_mock.acquire = AsyncMock(return_value=True)
        lock_mock.release = AsyncMock()
        lock_mock.__aenter__ = AsyncMock(return_value=lock_mock)
        lock_mock.__aexit__ = AsyncMock()
        redis.lock = MagicMock(return_value=lock_mock)
        return redis

    @pytest.fixture
    def orchestrator(self, mock_db, mock_redis):
        """Create orchestrator with mocked dependencies."""
        return AIOrchestrator(mock_db, mock_redis)

    @pytest.mark.asyncio
    async def test_run_pipeline_updates_state_to_coaching_pre_lock(self, orchestrator, mock_db):
        """Test that game state is set to COACHING before acquiring lock."""
        # Mock game in SUBMITTED state
        mock_game = MagicMock()
        mock_game.state = GameState.SUBMITTED
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_game)
        mock_db.execute = AsyncMock(return_value=mock_result)

        await orchestrator.run_pipeline(1, "STANDARD")

        # Verify state update call
        assert mock_db.begin.called
        # The logic sets state to COACHING pre-lock
        assert mock_game.state == GameState.COACHING
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_run_pipeline_acquires_redis_lock(self, orchestrator, mock_redis):
        """Test that Redis lock is acquired for the game."""
        mock_redis.lock.return_value.__aenter__.return_value = None

        await orchestrator.run_pipeline(1, "STANDARD")

        mock_redis.lock.assert_called_with("ai_lock:1", timeout=300)

    @pytest.mark.asyncio
    async def test_run_pipeline_handles_missing_game(self, orchestrator, mock_db):
        """Test handling of non-existent game."""
        mock_db.execute.return_value.scalar_one_or_none.return_value = None

        await orchestrator.run_pipeline(999, "STANDARD")

        # Should not raise exception, just return early
        # Verify no further processing

    @pytest.mark.asyncio
    async def test_run_pipeline_processes_analyzer_output(self, orchestrator, mock_db):
        """Test that analyzer output is processed and key positions created."""
        from api.common.models import KeyPosition, Question

        # Mock game
        mock_game = MagicMock()
        mock_game.state = GameState.SUBMITTED
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_game)
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Mock analyzer output
        mock_analyzer_output = {
            "key_positions": [
                {
                    "fen": "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3",
                    "reason_code": "THREAT_AWARENESS",
                    "engine_truth": {"score": 0.5, "best_move": "Bb5", "threats": ["Nxe5"]}
                }
            ]
        }

        # Mock _run_analyzer
        orchestrator._run_analyzer = AsyncMock(return_value=mock_analyzer_output)

        # Mock _generate_socratic_questions
        orchestrator._generate_socratic_questions = AsyncMock()

        await orchestrator.run_pipeline(1, "STANDARD")

        # Verify key position creation
        assert mock_db.add.called
        # Check that KeyPosition was added
        call_args = mock_db.add.call_args_list
        assert any(isinstance(arg.args[0], KeyPosition) for arg in call_args)

    @pytest.mark.asyncio
    async def test_run_pipeline_handles_redis_connection_error(self, orchestrator, mock_redis):
        """Test graceful handling of Redis connection errors."""
        mock_redis.lock.side_effect = Exception("Redis connection failed")

        # Should not raise exception
        await orchestrator.run_pipeline(1, "STANDARD")

        # State should still be set to COACHING from pre-lock logic

    @pytest.mark.asyncio
    async def test_run_analyzer_returns_mock_output(self, orchestrator):
        """Test analyzer mock implementation."""
        mock_game = MagicMock()
        result = await orchestrator._run_analyzer(mock_game, "STANDARD")

        assert "key_positions" in result
        assert len(result["key_positions"]) == 1
        assert "fen" in result["key_positions"][0]
        assert "reason_code" in result["key_positions"][0]

    @pytest.mark.asyncio
    async def test_generate_socratic_questions_creates_questions(self, orchestrator, mock_db):
        """Test that Socratic questions are generated for key positions."""
        from api.common.models import KeyPosition

        mock_kp = MagicMock()
        mock_kp.id = 1

        await orchestrator._generate_socratic_questions(mock_kp)

        # Verify Question objects were added
        call_args = mock_db.add.call_args_list
        # Should have 6 questions for 6 categories
        question_calls = [arg for arg in call_args if hasattr(arg.args[0], 'key_position_id')]
        assert len(question_calls) == 6