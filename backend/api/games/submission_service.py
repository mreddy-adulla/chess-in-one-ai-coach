from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from api.common.models import Game, GameState, ParentApproval
from datetime import datetime, timezone
from typing import Optional

class SubmissionService:
    """Service for game submission and state transitions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def submit_game(self, game_id: int, pgn: str, tier: str) -> dict:
        """Submit a game for AI processing."""
        # Fetch game
        result = await self.db.execute(select(Game).where(Game.id == game_id))
        game = result.scalar_one_or_none()
        if not game:
            raise ValueError("Game not found")

        # Check idempotency
        if game.state == GameState.SUBMITTED:
            return {"message": "Game already submitted", "state": game.state}

        # Validate transition
        if game.state != GameState.EDITABLE:
            raise ValueError(f"Invalid transition from {game.state} to SUBMITTED")

        # Check parent approval requirement
        if await self._requires_approval(game_id, tier):
            approval = await self._get_valid_approval(game_id, tier)
            if not approval:
                raise ValueError(f"Parent approval required for {tier} tier or repeat run")
            # Mark approval as used
            approval.used = True

        # Update PGN and freeze annotations
        game.pgn = pgn
        await self.db.execute(
            update(Annotation)
            .where(Annotation.game_id == game_id)
            .values(frozen=True)
        )

        # Transition to SUBMITTED
        game.state = GameState.SUBMITTED
        await self.db.commit()

        return {"message": "Game submitted successfully", "state": game.state}

    async def _requires_approval(self, game_id: int, tier: str) -> bool:
        """Check if submission requires parent approval."""
        if tier != "STANDARD":
            return True

        # Check for previous completed runs
        prev_runs = await self.db.execute(
            select(Game).where(Game.id == game_id).where(Game.state == GameState.COMPLETED)
        )
        return prev_runs.scalar_one_or_none() is not None

    async def _get_valid_approval(self, game_id: int, tier: str) -> Optional[ParentApproval]:
        """Get valid (unused, unexpired) parent approval."""
        now = datetime.now(timezone.utc)
        result = await self.db.execute(
            select(ParentApproval)
            .where(ParentApproval.game_id == game_id)
            .where(ParentApproval.tier == tier)
            .where(ParentApproval.approved == True)
            .where(ParentApproval.used == False)
            .where(ParentApproval.expires_at > now)
        )
        return result.scalar_one_or_none()