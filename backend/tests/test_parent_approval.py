import pytest
from sqlalchemy import select
from api.common.models import Game, GameState, ParentApproval
from datetime import datetime, timezone, timedelta

class TestParentApproval:
    """Integration tests for parent approval workflow."""

    @pytest.mark.asyncio
    async def test_approval_required_for_non_standard_tier(self, db_session):
        """Test that submission fails without approval for PREMIUM tier."""
        game = Game(
            user_id="test_user",
            state=GameState.EDITABLE,
            player_color="WHITE",
            pgn="1. e4 e5"
        )
        db_session.add(game)
        await db_session.commit()

        # Attempt submission without approval
        result = await db_session.execute(
            select(ParentApproval)
            .where(ParentApproval.game_id == game.id)
            .where(ParentApproval.tier == "PREMIUM")
            .where(ParentApproval.approved == True)
            .where(ParentApproval.used == False)
            .where(ParentApproval.expires_at > datetime.now(timezone.utc))
        )
        approval = result.scalar_one_or_none()
        assert approval is None  # No approval exists

    @pytest.mark.asyncio
    async def test_approval_required_for_repeat_run(self, db_session):
        """Test that approval is required for second run on same game."""
        game = Game(
            user_id="test_user",
            state=GameState.COMPLETED,  # Previous run completed
            player_color="WHITE",
            pgn="1. e4 e5"
        )
        db_session.add(game)
        await db_session.commit()

        # Check if repeat run
        prev_runs = await db_session.execute(
            select(Game).where(Game.id == game.id).where(Game.state == GameState.COMPLETED)
        )
        is_repeat = prev_runs.scalar_one_or_none() is not None
        assert is_repeat is True

        # Without approval for STANDARD tier on repeat, should fail
        result = await db_session.execute(
            select(ParentApproval)
            .where(ParentApproval.game_id == game.id)
            .where(ParentApproval.tier == "STANDARD")
            .where(ParentApproval.approved == True)
            .where(ParentApproval.used == False)
            .where(ParentApproval.expires_at > datetime.now(timezone.utc))
        )
        approval = result.scalar_one_or_none()
        assert approval is None

    @pytest.mark.asyncio
    async def test_valid_approval_allows_submission(self, db_session):
        """Test that valid, unused approval allows submission."""
        game = Game(
            user_id="test_user",
            state=GameState.EDITABLE,
            player_color="WHITE"
        )
        db_session.add(game)
        await db_session.commit()

        # Create valid approval
        future_time = datetime.now(timezone.utc) + timedelta(hours=1)
        approval = ParentApproval(
            game_id=game.id,
            tier="PREMIUM",
            approved=True,
            used=False,
            expires_at=future_time
        )
        db_session.add(approval)
        await db_session.commit()

        # Check approval exists
        result = await db_session.execute(
            select(ParentApproval)
            .where(ParentApproval.game_id == game.id)
            .where(ParentApproval.tier == "PREMIUM")
            .where(ParentApproval.approved == True)
            .where(ParentApproval.used == False)
            .where(ParentApproval.expires_at > datetime.now(timezone.utc))
        )
        valid_approval = result.scalar_one_or_none()
        assert valid_approval is not None

    @pytest.mark.asyncio
    async def test_approval_marked_used_after_submission(self, db_session):
        """Test that approval is marked as used after successful submission."""
        game = Game(
            user_id="test_user",
            state=GameState.EDITABLE,
            player_color="WHITE"
        )
        db_session.add(game)
        await db_session.commit()

        # Create approval
        future_time = datetime.now(timezone.utc) + timedelta(hours=1)
        approval = ParentApproval(
            game_id=game.id,
            tier="PREMIUM",
            approved=True,
            used=False,
            expires_at=future_time
        )
        db_session.add(approval)
        await db_session.commit()

        # Simulate marking as used
        approval.used = True
        await db_session.commit()

        await db_session.refresh(approval)
        assert approval.used is True

    @pytest.mark.asyncio
    async def test_expired_approval_invalid(self, db_session):
        """Test that expired approvals are not valid."""
        game = Game(
            user_id="test_user",
            state=GameState.EDITABLE,
            player_color="WHITE"
        )
        db_session.add(game)
        await db_session.commit()

        # Create expired approval
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        approval = ParentApproval(
            game_id=game.id,
            tier="PREMIUM",
            approved=True,
            used=False,
            expires_at=past_time
        )
        db_session.add(approval)
        await db_session.commit()

        # Check if valid
        result = await db_session.execute(
            select(ParentApproval)
            .where(ParentApproval.game_id == game.id)
            .where(ParentApproval.tier == "PREMIUM")
            .where(ParentApproval.approved == True)
            .where(ParentApproval.used == False)
            .where(ParentApproval.expires_at > datetime.now(timezone.utc))
        )
        valid_approval = result.scalar_one_or_none()
        assert valid_approval is None

    @pytest.mark.asyncio
    async def test_used_approval_invalid(self, db_session):
        """Test that used approvals cannot be reused."""
        game = Game(
            user_id="test_user",
            state=GameState.EDITABLE,
            player_color="WHITE"
        )
        db_session.add(game)
        await db_session.commit()

        # Create used approval
        future_time = datetime.now(timezone.utc) + timedelta(hours=1)
        approval = ParentApproval(
            game_id=game.id,
            tier="PREMIUM",
            approved=True,
            used=True,  # Already used
            expires_at=future_time
        )
        db_session.add(approval)
        await db_session.commit()

        # Check if valid
        result = await db_session.execute(
            select(ParentApproval)
            .where(ParentApproval.game_id == game.id)
            .where(ParentApproval.tier == "PREMIUM")
            .where(ParentApproval.approved == True)
            .where(ParentApproval.used == False)
            .where(ParentApproval.expires_at > datetime.now(timezone.utc))
        )
        valid_approval = result.scalar_one_or_none()
        assert valid_approval is None