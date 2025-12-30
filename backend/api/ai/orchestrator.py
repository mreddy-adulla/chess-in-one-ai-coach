import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from api.common.models import Game, GameState, KeyPosition, Question
from api.common.config import settings
from api.ai.validators.orchestrator_validator import validate_analyzer_output

class AIOrchestrator:
    """
    Implements PHASE 3: AI Orchestration Pipeline.
    Strictly follows Implementation Spec v2.0 Section 8.1.
    """
    def __init__(self, db: AsyncSession, redis_client: redis.Redis):
        self.db = db
        self.redis = redis_client

    async def run_pipeline(self, game_id: int):
        # Redis lock guards AI pipeline (Implementation Spec 16)
        lock_key = f"ai_lock:{game_id}"
        async with self.redis.lock(lock_key, timeout=300):
            async with self.db.begin():
                result = await self.db.execute(select(Game).where(Game.id == game_id))
                game = result.scalar_one_or_none()
                
                if not game or game.state != GameState.SUBMITTED:
                    return # Already handled or invalid

                # Transition to COACHING
                game.state = GameState.COACHING

                # 1. Chess Situation Analyzer (Stub - internal)
                analyzer_output = await self._run_analyzer(game)
                
                # Validation occurs BEFORE persistence or exposure (Implementation Spec 9.3)
                validate_analyzer_output(analyzer_output)

                # 2. Persist 3–5 key positions
                for i, pos in enumerate(analyzer_output["key_positions"]):
                    kp = KeyPosition(
                        game_id=game_id,
                        fen=pos["fen"],
                        reason_code=pos["reason_code"],
                        engine_truth=pos["engine_truth"],
                        order=i
                    )
                    self.db.add(kp)
                    await self.db.flush()

                    # 3. Socratic Question Loop (Stub for questions generation)
                    await self._generate_socratic_questions(kp)

                # 4. Reflection & Guidance Generator (Occurs after all positions)
                # This is normally triggered after child completes questions,
                # but we initialize the structure here.
                
                await self.db.commit()

    async def _run_analyzer(self, game: Game):
        """
        Internal Analyzer - Produces 3-5 key positions.
        Implementation Spec 10.1: JSON output only, no language.
        """
        # Mocking output for Phase 3
        return {
            "key_positions": [
                {
                    "fen": "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3",
                    "reason_code": "THREAT_AWARENESS",
                    "engine_truth": {
                        "score": 0.5,
                        "best_move": "Bb5",
                        "threats": ["Nxe5"]
                    }
                }
            ]
        }

    async def _generate_socratic_questions(self, kp: KeyPosition):
        """
        Socratic Questioner - Implementation Spec 12
        """
        categories = ["OPP_INTENT", "THREAT", "CHANGE", "WORST_PIECE", "ALTERNATIVES", "REFLECTION"]
        for i, cat in enumerate(categories):
            q = Question(
                key_position_id=kp.id,
                category=cat,
                question_text=f"Stub question for {cat}",
                order=i
            )
            self.db.add(q)
