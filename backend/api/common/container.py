"""
Dependency injection container for services.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import redis.asyncio as redis
from api.ai.orchestrator import AIOrchestrator
from api.games.game_service import GameService
from api.games.annotation_service import AnnotationService
from api.games.submission_service import SubmissionService

class ServiceContainer:
    """Container for managing service dependencies."""

    def __init__(self, db: AsyncSession, redis_client: Optional[redis.Redis] = None):
        self.db = db
        self.redis_client = redis_client
        self._game_service: Optional[GameService] = None
        self._annotation_service: Optional[AnnotationService] = None
        self._submission_service: Optional[SubmissionService] = None
        self._orchestrator: Optional[AIOrchestrator] = None

    @property
    def game_service(self) -> GameService:
        """Get or create game service."""
        if self._game_service is None:
            self._game_service = GameService(self.db)
        return self._game_service

    @property
    def annotation_service(self) -> AnnotationService:
        """Get or create annotation service."""
        if self._annotation_service is None:
            self._annotation_service = AnnotationService(self.db)
        return self._annotation_service

    @property
    def submission_service(self) -> SubmissionService:
        """Get or create submission service."""
        if self._submission_service is None:
            self._submission_service = SubmissionService(self.db)
        return self._submission_service

    @property
    def orchestrator(self) -> AIOrchestrator:
        """Get or create AI orchestrator."""
        if self._orchestrator is None:
            if self.redis_client is None:
                raise ValueError("Redis client required for orchestrator")
            self._orchestrator = AIOrchestrator(self.db, self.redis_client)
        return self._orchestrator