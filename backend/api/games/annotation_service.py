from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from api.common.models import Annotation, Game, GameState
from typing import Optional

class AnnotationService:
    """Service for annotation management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_or_update_annotation(self, game_id: int, move_number: int, content: str) -> bool:
        """Add or update an annotation for a game move."""
        # Check game state
        result = await self.db.execute(select(Game).where(Game.id == game_id))
        game = result.scalar_one_or_none()
        if not game or game.state != GameState.EDITABLE:
            return False

        # Check if annotation exists
        result = await self.db.execute(
            select(Annotation)
            .where(Annotation.game_id == game_id)
            .where(Annotation.move_number == move_number)
        )
        annotation = result.scalar_one_or_none()

        if annotation:
            annotation.content = content
        else:
            annotation = Annotation(
                game_id=game_id,
                move_number=move_number,
                content=content
            )
            self.db.add(annotation)

        await self.db.commit()
        return True

    async def freeze_annotations(self, game_id: int):
        """Freeze all annotations for a game."""
        await self.db.execute(
            update(Annotation)
            .where(Annotation.game_id == game_id)
            .values(frozen=True)
        )
        await self.db.commit()