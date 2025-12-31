from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from api.common.database import get_db
from api.common.models import Game, GameState, Annotation, Question, KeyPosition
from datetime import datetime
from api.auth.middleware import AuthMiddleware
from pydantic import BaseModel
from api.ai.orchestrator import AIOrchestrator
import redis.asyncio as redis
from api.common.config import settings

router = APIRouter(prefix="/games", tags=["games"])

class GameSubmit(BaseModel):
    pgn: str

class AnnotationCreate(BaseModel):
    move_number: int
    content: str

@router.get("")
@router.get("/")
async def get_games(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Game).order_by(Game.created_at.desc()))
    return result.scalars().all()

@router.post("")
@router.post("/")
async def create_game(request: Request, game_data: dict, db: AsyncSession = Depends(get_db)):
    """
    Creates a new game. Logic moved to client-side as per ground truth.
    Backend only persists the provided data.
    """
    user = getattr(request.state, "user", {"sub": "anonymous"})
    
    # Ensure user_id is set from authenticated user
    game_data["user_id"] = user.get("sub")
    
    # Convert date string if present (client should send ISO format)
    if "date" in game_data and isinstance(game_data["date"], str):
        try:
            game_data["date"] = datetime.fromisoformat(game_data["date"].replace('Z', '+00:00'))
        except ValueError:
            pass # Keep as string or handle error
            
    game = Game(**game_data)
    db.add(game)
    await db.commit()
    await db.refresh(game)
    return game

@router.get("/{game_id}")
async def get_game(game_id: int, db: AsyncSession = Depends(get_db)):
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Game)
        .options(selectinload(Game.annotations))
        .where(Game.id == game_id)
    )
    game = result.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game

@router.post("/{game_id}/submit")
async def submit_game(game_id: int, submit_data: GameSubmit, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """
    Implements PHASE 2: Game Lifecycle enforcement.
    EDITABLE -> SUBMITTED -> COACHING -> COMPLETED
    """
    # Fetch game
    result = await db.execute(select(Game).where(Game.id == game_id))
    game = result.scalar_one_or_none()
    
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    # Update PGN from client submission
    game.pgn = submit_data.pgn

    # Idempotency (Implementation Spec 6.2)
    if game.state == GameState.SUBMITTED:
        return {"message": "Game already submitted", "state": game.state}

    # Transition Rule: Only EDITABLE -> SUBMITTED is allowed here
    if game.state != GameState.EDITABLE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail=f"Invalid transition from {game.state} to SUBMITTED"
        )

    # 1. Freeze all annotations (Implementation Spec 7.1)
    await db.execute(
        update(Annotation)
        .where(Annotation.game_id == game_id)
        .values(frozen=True)
    )

    # 2. Update state to SUBMITTED
    game.state = GameState.SUBMITTED
    
    # State transition + side effects occur in single transaction (Implementation Spec 7.3)
    await db.commit()

    # Trigger AI Pipeline asynchronously
    redis_client = redis.from_url(settings.REDIS_URL)
    orchestrator = AIOrchestrator(db, redis_client)
    background_tasks.add_task(orchestrator.run_pipeline, game_id)

    return {"message": "Game submitted successfully", "state": game.state}

@router.post("/{game_id}/annotations")
async def add_annotation(game_id: int, annotation_data: AnnotationCreate, db: AsyncSession = Depends(get_db)):
    async with db.begin():
        result = await db.execute(select(Game).where(Game.id == game_id))
        game = result.scalar_one_or_none()
        
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        # Writable only when game state = EDITABLE (Implementation Spec 7.1)
        if game.state != GameState.EDITABLE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Cannot add annotations to non-editable game"
            )
            
        # Check if annotation exists for this move
        result = await db.execute(
            select(Annotation)
            .where(Annotation.game_id == game_id)
            .where(Annotation.move_number == annotation_data.move_number)
        )
        annotation = result.scalar_one_or_none()
        
        if annotation:
            annotation.content = annotation_data.content
        else:
            annotation = Annotation(
                game_id=game_id,
                move_number=annotation_data.move_number,
                content=annotation_data.content
            )
            db.add(annotation)
        
        await db.commit()
        
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
    async with db.begin():
        result = await db.execute(select(Question).where(Question.id == question_id))
        question = result.scalar_one_or_none()
        
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
            
        # Implementation Spec 7.2: Each question accepts exactly one answer or skip
        if question.answer_text or question.skipped:
             raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Question already answered")
             
        question.answer_text = answer
        await db.commit()
        
    return {"message": "Answer recorded"}
