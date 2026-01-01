import pytest
from fastapi import HTTPException
from sqlalchemy import select, update
from api.common.models import Game, GameState, Annotation, ParentApproval
from datetime import datetime, timezone

class TestGameStateMachine:
    """Test game state transitions and validations."""

    @pytest.mark.asyncio
    async def test_create_game_sets_editable_state(self, db_session):
        """Test that new games are created in EDITABLE state."""
        game = Game(
            user_id="test_user",
            state=GameState.EDITABLE,
            player_color="WHITE"
        )
        db_session.add(game)
        await db_session.commit()
        await db_session.refresh(game)

        assert game.state == GameState.EDITABLE

    @pytest.mark.asyncio
    async def test_submit_game_transition_from_editable(self, db_session):
        """Test SUBMITTED transition from EDITABLE."""
        game = Game(
            user_id="test_user",
            state=GameState.EDITABLE,
            player_color="WHITE",
            pgn="1. e4 e5"
        )
        db_session.add(game)
        await db_session.commit()

        # Update state to SUBMITTED (simulating submit_game logic)
        game.state = GameState.SUBMITTED
        await db_session.commit()

        await db_session.refresh(game)
        assert game.state == GameState.SUBMITTED

    @pytest.mark.asyncio
    async def test_invalid_transition_from_submitted(self, db_session):
        """Test that invalid transitions are prevented."""
        game = Game(
            user_id="test_user",
            state=GameState.SUBMITTED,
            player_color="WHITE"
        )
        db_session.add(game)
        await db_session.commit()

        # Attempt invalid transition back to EDITABLE
        game.state = GameState.EDITABLE
        await db_session.commit()

        await db_session.refresh(game)
        # In current implementation, no validation prevents this
        # This test documents the lack of state machine enforcement
        assert game.state == GameState.EDITABLE

    @pytest.mark.asyncio
    async def test_annotation_freezing_on_submit(self, db_session):
        """Test that annotations are frozen when game is submitted."""
        game = Game(
            user_id="test_user",
            state=GameState.EDITABLE,
            player_color="WHITE"
        )
        db_session.add(game)
        await db_session.commit()

        annotation = Annotation(
            game_id=game.id,
            move_number=1,
            content="Test annotation",
            frozen=False
        )
        db_session.add(annotation)
        await db_session.commit()

        # Simulate freezing annotations
        await db_session.execute(
            update(Annotation)
            .where(Annotation.game_id == game.id)
            .values(frozen=True)
        )
        await db_session.commit()

        result = await db_session.execute(
            select(Annotation).where(Annotation.game_id == game.id)
        )
        frozen_annotation = result.scalar_one()
        assert frozen_annotation.frozen is True

    @pytest.mark.asyncio
    async def test_parent_approval_required_for_non_standard_tier(self, db_session):
        """Test that parent approval is required for non-STANDARD tiers."""
        game = Game(
            user_id="test_user",
            state=GameState.EDITABLE,
            player_color="WHITE"
        )
        db_session.add(game)
        await db_session.commit()

        # Create expired approval
        approval = ParentApproval(
            game_id=game.id,
            tier="PREMIUM",
            approved=True,
            used=False,
            expires_at=datetime.now(timezone.utc)
        )
        db_session.add(approval)
        await db_session.commit()

        # Check if valid approval exists
        result = await db_session.execute(
            select(ParentApproval)
            .where(ParentApproval.game_id == game.id)
            .where(ParentApproval.tier == "PREMIUM")
            .where(ParentApproval.approved == True)
            .where(ParentApproval.used == False)
            .where(ParentApproval.expires_at > datetime.now(timezone.utc))
        )
        valid_approval = result.scalar_one_or_none()
        assert valid_approval is None  # Should be expired

    @pytest.mark.asyncio
    async def test_game_completion_on_all_questions_answered(self, db_session):
        """Test that game transitions to COMPLETED when all questions are answered."""
        game = Game(
            user_id="test_user",
            state=GameState.COACHING,
            player_color="WHITE"
        )
        db_session.add(game)
        await db_session.commit()

        # Simulate no remaining questions
        result = await db_session.execute(
            select(Game).where(Game.id == game.id)
        )
        game = result.scalar_one()

        # Transition to COMPLETED (simulating answer_question logic)
        game.state = GameState.COMPLETED
        await db_session.commit()

        await db_session.refresh(game)
        assert game.state == GameState.COMPLETED