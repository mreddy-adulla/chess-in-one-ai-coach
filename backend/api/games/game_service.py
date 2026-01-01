from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from api.common.models import Game, GameState, Annotation
from api.common.pgn_utils import extract_annotations_from_pgn
from typing import Optional

class GameService:
    """Service for game CRUD operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_game(self, user_id: str, player_color: str,
                         opponent_name: Optional[str] = None,
                         event: Optional[str] = None,
                         date: Optional[str] = None,
                         time_control: Optional[str] = None,
                         pgn: Optional[str] = None) -> Game:
        """Create a new game."""
        game = Game(
            user_id=user_id,
            state=GameState.EDITABLE,
            player_color=player_color,
            opponent_name=opponent_name,
            event=event,
            date=date,
            time_control=time_control,
            pgn=pgn
        )
        self.db.add(game)
        await self.db.flush()

        # Extract annotations from PGN if provided
        if pgn:
            await self._extract_annotations_from_pgn(game, pgn)

        await self.db.commit()
        await self.db.refresh(game)
        return game

    async def get_game(self, game_id: int) -> Optional[Game]:
        """Get a game by ID with annotations."""
        from sqlalchemy.orm import selectinload
        result = await self.db.execute(
            select(Game)
            .options(selectinload(Game.annotations))
            .where(Game.id == game_id)
        )
        return result.scalar_one_or_none()

    async def get_games(self) -> list[Game]:
        """Get all games ordered by creation date."""
        result = await self.db.execute(select(Game).order_by(Game.created_at.desc()))
        return result.scalars().all()

    async def delete_game(self, game_id: int) -> bool:
        """Delete a game by ID."""
        result = await self.db.execute(select(Game).where(Game.id == game_id))
        game = result.scalar_one_or_none()
        if not game:
            return False
        await self.db.delete(game)
        await self.db.commit()
        return True

    async def _extract_annotations_from_pgn(self, game: Game, pgn: str):
        """Extract annotations from PGN and save them."""
        annotations = extract_annotations_from_pgn(pgn, game.id, game.player_color)
        for annotation in annotations:
            self.db.add(annotation)