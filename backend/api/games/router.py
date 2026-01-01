from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from api.common.database import get_db
from api.common.models import Game, GameState, Question, KeyPosition
from api.auth.middleware import AuthMiddleware
from pydantic import BaseModel, Field
from api.ai.orchestrator import AIOrchestrator
import redis.asyncio as redis
from api.common.config import settings
from typing import Optional
from api.common.container import ServiceContainer

router = APIRouter(prefix="/games", tags=["games"])

def get_container(db: AsyncSession = Depends(get_db)) -> ServiceContainer:
    """Dependency to get service container."""
    redis_client = redis.from_url(settings.REDIS_URL)
    return ServiceContainer(db, redis_client)

class GameSubmit(BaseModel):
    pgn: str
    tier: str = Field(default="STANDARD")

class AnnotationCreate(BaseModel):
    move_number: int
    content: str

@router.get("")
@router.get("/")
async def get_games(container: ServiceContainer = Depends(get_container)):
    return await container.game_service.get_games()

class GameCreate(BaseModel):
    player_color: str
    opponent_name: Optional[str] = None
    event: Optional[str] = None
    date: Optional[datetime] = None
    time_control: Optional[str] = None
    pgn: Optional[str] = None

@router.post("")
@router.post("/")
async def create_game(request: Request, game_data: GameCreate, db: AsyncSession = Depends(get_db)):
    """
    Creates a new game. Logic moved to client-side as per ground truth.
    Backend only persists the provided data.
    """
    user = getattr(request.state, "user", {"sub": "anonymous"})

    # Ensure user_id is set from authenticated user
    user_id = user.get("sub")

    service = GameService(db)
    return await service.create_game(
        user_id=user_id,
        player_color=game_data.player_color,
        opponent_name=game_data.opponent_name,
        event=game_data.event,
        date=game_data.date,
        time_control=game_data.time_control,
        pgn=game_data.pgn
    )

@router.get("/{game_id}")
async def get_game(game_id: int, db: AsyncSession = Depends(get_db)):
    service = GameService(db)
    game = await service.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game

@router.delete("/{game_id}")
async def delete_game(game_id: int, db: AsyncSession = Depends(get_db)):
    service = GameService(db)
    if not await service.delete_game(game_id):
        raise HTTPException(status_code=404, detail="Game not found")
    return {"message": "Game deleted successfully"}

@router.post("/{game_id}/submit")
async def submit_game(game_id: int, submit_data: GameSubmit, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """
    Implements PHASE 2: Game Lifecycle enforcement and PHASE 7: Parent Approval.
    EDITABLE -> SUBMITTED -> COACHING -> COMPLETED
    """
    print(f"DEBUG: submit_game called for id={game_id} with tier={submit_data.tier}")

    service = SubmissionService(db)
    try:
        result = await service.submit_game(game_id, submit_data.pgn, submit_data.tier)
        print(f"DEBUG: Game {game_id} state updated to SUBMITTED and committed")

        # Trigger AI Pipeline asynchronously
        try:
            redis_client = redis.from_url(settings.REDIS_URL)
            orchestrator = AIOrchestrator(db, redis_client)
            background_tasks.add_task(orchestrator.run_pipeline, game_id, submit_data.tier)
            print(f"DEBUG: AI pipeline background task added for game {game_id}")
        except Exception as e:
            print(f"DEBUG: Error triggering AI pipeline for game {game_id}: {str(e)}")

        return result
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        elif "approval" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
        else:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

@router.post("/{game_id}/annotations")
async def add_annotation(game_id: int, annotation_data: AnnotationCreate, db: AsyncSession = Depends(get_db)):
    service = AnnotationService(db)
    if not await service.add_or_update_annotation(game_id, annotation_data.move_number, annotation_data.content):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot add annotations to non-editable game"
        )
    return {"message": "Annotation saved"}

@router.get("/{game_id}/next-question")
async def get_next_question(game_id: int, db: AsyncSession = Depends(get_db)):
    """
    Implements PHASE 6: Failure & Resume Logic.
    Resume continues from last unanswered question (Implementation Spec 10.2).
    """
    # Implementation logic to find first question without answer_text or skipped=False
    # ordered by key_position order and question order
    result = await db.execute(
        select(Question)
        .join(KeyPosition)
        .where(KeyPosition.game_id == game_id)
        .where(Question.answer_text == None)
        .where(Question.skipped == False)
        .order_by(KeyPosition.order, Question.order)
        .limit(1)
    )
    question = result.scalar_one_or_none()
    
    if not question:
        return {"message": "All questions completed"}
        
    return question

@router.post("/questions/{question_id}/answer")
async def answer_question(question_id: int, answer: str, db: AsyncSession = Depends(get_db)):
    from sqlalchemy.orm import selectinload
    async with db.begin():
        result = await db.execute(
            select(Question)
            .options(selectinload(Question.key_position))
            .where(Question.id == question_id)
        )
        question = result.scalar_one_or_none()
        
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
            
        # Implementation Spec 7.2: Each question accepts exactly one answer or skip
        if question.answer_text or question.skipped:
             raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Question already answered")
             
        question.answer_text = answer
        
        # Check if all questions for this game are answered
        # If so, transition to COMPLETED
        result = await db.execute(
            select(Question)
            .join(KeyPosition)
            .where(KeyPosition.game_id == question.key_position.game_id)
            .where(Question.answer_text == None)
            .where(Question.skipped == False)
        )
        remaining = result.scalars().all()
        if not remaining:
            # Transition game to COMPLETED
            await db.execute(
                update(Game)
                .where(Game.id == question.key_position.game_id)
                .values(state=GameState.COMPLETED)
            )
            print(f"DEBUG: All questions answered for game {question.key_position.game_id}. Transitioned to COMPLETED.")

        await db.commit()
        
    return {"message": "Answer recorded"}

@router.get("/{game_id}/reflection")
async def get_reflection(game_id: int, db: AsyncSession = Depends(get_db)):
    """
    Returns AI-generated reflection for the game.
    Placeholder implementation as per Phase 3 compliance.
    """
    # Fetch game to ensure it exists and is COMPLETED
    result = await db.execute(select(Game).where(Game.id == game_id))
    game = result.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # In a real scenario, this would be stored in the DB after AI pipeline finishes.
    if game.reflection:
        return game.reflection
    
    raise HTTPException(status_code=404, detail="Reflection not generated yet for this game")
