from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from api.common.database import get_db
from api.common.models import Game, GameState, Question, KeyPosition, Annotation
from api.auth.middleware import AuthMiddleware
from pydantic import BaseModel, Field
from api.ai.orchestrator import AIOrchestrator
from api.games.game_service import GameService
from api.games.submission_service import SubmissionService
from api.games.annotation_service import AnnotationService
import redis.asyncio as redis
from api.common.config import settings
from typing import Optional
from datetime import datetime
from api.common.container import ServiceContainer
import asyncio

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

class QuestionAnswer(BaseModel):
    content: str = ""
    skipped: bool = False

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
    import logging
    logger = logging.getLogger(__name__)
    
    user = getattr(request.state, "user", {"sub": "anonymous"})

    # Ensure user_id is set from authenticated user
    user_id = user.get("sub")
    logger.info(f"[CREATE_GAME] Creating game for user_id={user_id}, player_color={game_data.player_color}")

    service = GameService(db)
    game = await service.create_game(
        user_id=user_id,
        player_color=game_data.player_color,
        opponent_name=game_data.opponent_name,
        event=game_data.event,
        date=game_data.date,
        time_control=game_data.time_control,
        pgn=game_data.pgn
    )
    logger.info(f"[CREATE_GAME] Created game with id={game.id}, state={game.state}")
    return game

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
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"[SUBMIT_GAME] Starting submission for game_id={game_id}, tier={submit_data.tier}")

    service = SubmissionService(db)
    try:
        result = await service.submit_game(game_id, submit_data.pgn, submit_data.tier)
        logger.info(f"[SUBMIT_GAME] Game {game_id} state updated to SUBMITTED and committed")

        # Trigger AI Pipeline asynchronously
        # Try to connect to Redis, but continue even if it fails
        redis_client = None
        try:
            redis_client = redis.from_url(settings.REDIS_URL)
            # Test connection with a short timeout
            await asyncio.wait_for(redis_client.ping(), timeout=1.0)
            print(f"DEBUG: Redis connection successful")
        except Exception as e:
            print(f"WARNING: Redis connection failed, pipeline will run without locking: {str(e)}")
            # Set to None - LockManager will handle this gracefully
            redis_client = None
        
        try:
            # Create orchestrator - it will handle None redis_client via LockManager
            orchestrator = AIOrchestrator(db, redis_client)
            background_tasks.add_task(orchestrator.run_pipeline, game_id, submit_data.tier)
            print(f"DEBUG: AI pipeline background task added for game {game_id}")
        except Exception as e:
            print(f"ERROR: Failed to create orchestrator for game {game_id}: {str(e)}")
            import traceback
            traceback.print_exc()

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
    Returns question with key position info and related annotation.
    """
    from sqlalchemy.orm import selectinload
    
    # Implementation logic to find first question without answer_text or skipped=False
    # ordered by key_position order and question order
    result = await db.execute(
        select(Question)
        .join(KeyPosition)
        .options(selectinload(Question.key_position))
        .where(KeyPosition.game_id == game_id)
        .where(Question.answer_text == None)
        .where(Question.skipped == False)
        .order_by(KeyPosition.order, Question.order)
        .limit(1)
    )
    question = result.scalar_one_or_none()
    
    if not question:
        return {"message": "All questions completed"}
    
    # Find annotation at the move corresponding to this key position
    # Since KeyPosition has FEN but not move_number, we'll try to find annotations
    # near this position. For now, we'll return the key position's FEN
    # and let the frontend handle displaying it
    
    # Try to find any annotation that might be related to this position
    # We'll use the key_position's order as a hint for move_number
    # (This is a simplification - in a full implementation, we'd map FEN to move_number)
    annotation_result = await db.execute(
        select(Annotation)
        .where(Annotation.game_id == game_id)
        .where(Annotation.move_number >= question.key_position.order * 2)  # Rough estimate
        .where(Annotation.move_number < (question.key_position.order + 1) * 2)
        .limit(1)
    )
    annotation = annotation_result.scalar_one_or_none()
    
    # Build response with question, key position, and annotation
    response = {
        "id": question.id,
        "key_position_id": question.key_position_id,
        "category": question.category,
        "question_text": question.question_text,
        "order": question.order,
        "fen": question.key_position.fen,
        "original_annotation": annotation.content if annotation else None
    }
    
    return response

# Endpoint moved to backend/api/questions/router.py
# The answer_question endpoint is now at POST /questions/{question_id}/answer

async def _generate_reflection_from_answers(db: AsyncSession, game_id: int):
    """
    Generate reflection based on user's answers to questions using AI.
    Implementation Spec: Reflection Generator contract.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"[GENERATE_REFLECTION] Starting reflection generation for game {game_id}")
    
    from sqlalchemy.orm import selectinload
    from api.ai.providers.reflection_generator import ReflectionGeneratorProvider
    
    # Fetch game first to ensure it exists
    game_result = await db.execute(select(Game).where(Game.id == game_id))
    game = game_result.scalar_one_or_none()
    
    if not game:
        logger.error(f"[GENERATE_REFLECTION] Game {game_id} not found when generating reflection")
        raise ValueError(f"Game {game_id} not found")
    
    logger.info(f"[GENERATE_REFLECTION] Found game {game_id} with state {game.state}, player_color={game.player_color}")
    
    # Fetch all questions with answers for this game
    result = await db.execute(
        select(Question)
        .join(KeyPosition)
        .options(selectinload(Question.key_position))
        .where(KeyPosition.game_id == game_id)
        .where(Question.answer_text != None)
        .order_by(KeyPosition.order, Question.order)
    )
    answered_questions = result.scalars().all()
    logger.info(f"[GENERATE_REFLECTION] Found {len(answered_questions)} answered questions for game {game_id}")
    
    if not answered_questions:
        logger.warning(f"[GENERATE_REFLECTION] No answered questions found for game {game_id}. Will generate template reflection.")
    
    # Fetch all questions (including skipped) to get total count
    all_questions_result = await db.execute(
        select(Question)
        .join(KeyPosition)
        .where(KeyPosition.game_id == game_id)
    )
    all_questions = all_questions_result.scalars().all()
    total_questions = len(all_questions)
    skipped_count = sum(1 for q in all_questions if q.skipped)
    logger.info(f"[GENERATE_REFLECTION] Total questions: {total_questions}, Skipped: {skipped_count}")
    
    # Collect answers by category
    answers_by_category = {}
    for q in answered_questions:
        if q.category not in answers_by_category:
            answers_by_category[q.category] = []
        if q.answer_text:
            answers_by_category[q.category].append(q.answer_text)
    
    logger.info(f"[GENERATE_REFLECTION] Answers by category: {list(answers_by_category.keys())}")
    
    # Generate reflection using AI provider
    try:
        logger.info(f"[GENERATE_REFLECTION] Attempting to generate AI reflection for game {game_id}")
        provider = ReflectionGeneratorProvider()
        reflection = await provider.generate_reflection(
            answers_by_category=answers_by_category,
            player_color=game.player_color,
            total_questions=total_questions,
            skipped_count=skipped_count
        )
        logger.info(f"[GENERATE_REFLECTION] Successfully generated AI reflection for game {game_id}. Reflection keys: {list(reflection.keys())}")
    except Exception as e:
        logger.error(f"[GENERATE_REFLECTION] Failed to generate AI reflection for game {game_id}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        # Fallback to template
        logger.info(f"[GENERATE_REFLECTION] Falling back to template reflection for game {game_id}")
        provider = ReflectionGeneratorProvider()
        reflection = provider._generate_template_reflection(
            answers_by_category, game.player_color, total_questions, skipped_count
        )
        logger.info(f"[GENERATE_REFLECTION] Generated template reflection for game {game_id}")
    
    # Store reflection in game
    logger.info(f"[GENERATE_REFLECTION] Storing reflection in game {game_id}")
    game.reflection = reflection
    logger.info(f"[GENERATE_REFLECTION] Successfully stored reflection for game {game_id}. Reflection type: {type(reflection)}")

@router.get("/ai-tiers")
async def get_ai_tiers():
    """
    Returns available AI provider tiers for game submission.
    """
    return ["STANDARD", "GEMINI", "VERTEX", "CHATGPT"]

@router.get("/{game_id}/reflection")
async def get_reflection(game_id: int, db: AsyncSession = Depends(get_db)):
    """
    Returns AI-generated reflection for the game.
    Only available after all questions are answered and game is COMPLETED.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"[GET_REFLECTION] Request for reflection on game {game_id}")
    
    # Fetch game to ensure it exists
    result = await db.execute(select(Game).where(Game.id == game_id))
    game = result.scalar_one_or_none()
    if not game:
        logger.error(f"[GET_REFLECTION] Game {game_id} not found")
        raise HTTPException(status_code=404, detail="Game not found")
    
    logger.info(f"[GET_REFLECTION] Found game {game_id} with state {game.state}, has_reflection={game.reflection is not None}")

    # Check if game is in COMPLETED state
    if game.state != GameState.COMPLETED:
        logger.info(f"[GET_REFLECTION] Game {game_id} is in state {game.state}, not COMPLETED. Checking if analyzer has finished...")
        
        # First, check if analyzer has finished by checking if key positions exist
        from sqlalchemy import func
        key_positions_result = await db.execute(
            select(func.count(KeyPosition.id))
            .where(KeyPosition.game_id == game_id)
        )
        key_positions_count = key_positions_result.scalar_one()
        logger.info(f"[GET_REFLECTION] Game {game_id} has {key_positions_count} key positions")
        
        # If no key positions exist, analyzer hasn't finished yet
        if key_positions_count == 0:
            logger.warning(f"[GET_REFLECTION] Reflection not available for game {game_id}: Analysis still in progress")
            raise HTTPException(
                status_code=400,
                detail="Reflection not available yet. The game analysis is still in progress. Please wait a moment and try again."
            )
        
        # Check if there are unanswered questions
        unanswered_result = await db.execute(
            select(func.count(Question.id))
            .join(KeyPosition)
            .where(KeyPosition.game_id == game_id)
            .where(Question.answer_text == None)
            .where(Question.skipped == False)
        )
        unanswered_count = unanswered_result.scalar_one()
        logger.info(f"[GET_REFLECTION] Game {game_id} has {unanswered_count} unanswered questions")
        
        if unanswered_count > 0:
            logger.warning(f"[GET_REFLECTION] Reflection not available for game {game_id}: {unanswered_count} questions remaining")
            raise HTTPException(
                status_code=400, 
                detail=f"Reflection not available yet. Please answer all {unanswered_count} remaining questions first."
            )
        else:
            # All questions answered but state not COMPLETED yet - generate reflection and complete
            logger.info(f"[GET_REFLECTION] All questions answered for game {game_id} but state is {game.state}. Generating reflection...")
            try:
                # Generate reflection with timeout protection
                import asyncio
                try:
                    reflection_task = _generate_reflection_from_answers(db, game_id)
                    await asyncio.wait_for(reflection_task, timeout=60.0)  # 60 second timeout
                except asyncio.TimeoutError:
                    logger.error(f"[GET_REFLECTION] Reflection generation timed out for game {game_id}")
                    # Use template reflection as fallback
                    from api.ai.providers.reflection_generator import ReflectionGeneratorProvider
                    provider = ReflectionGeneratorProvider()
                    # Get basic info for template
                    from sqlalchemy import func
                    all_q_result = await db.execute(
                        select(func.count(Question.id))
                        .join(KeyPosition)
                        .where(KeyPosition.game_id == game_id)
                    )
                    total_q = all_q_result.scalar_one() or 0
                    skipped_q_result = await db.execute(
                        select(func.count(Question.id))
                        .join(KeyPosition)
                        .where(KeyPosition.game_id == game_id)
                        .where(Question.skipped == True)
                    )
                    skipped_q = skipped_q_result.scalar_one() or 0
                    reflection = provider._generate_template_reflection(
                        {}, game.player_color, total_q, skipped_q
                    )
                    game.reflection = reflection
                else:
                    # Reflection generated successfully
                    pass
                
                # Transition to COMPLETED
                await db.execute(
                    update(Game)
                    .where(Game.id == game_id)
                    .values(state=GameState.COMPLETED)
                )
                await db.commit()
                # Refresh game to get updated reflection
                await db.refresh(game)
                logger.info(f"[GET_REFLECTION] Generated reflection and transitioned game {game_id} to COMPLETED")
            except Exception as e:
                logger.error(f"[GET_REFLECTION] Failed to generate reflection for game {game_id}: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                await db.rollback()
                # Try to use template reflection as last resort
                try:
                    from api.ai.providers.reflection_generator import ReflectionGeneratorProvider
                    provider = ReflectionGeneratorProvider()
                    from sqlalchemy import func
                    all_q_result = await db.execute(
                        select(func.count(Question.id))
                        .join(KeyPosition)
                        .where(KeyPosition.game_id == game_id)
                    )
                    total_q = all_q_result.scalar_one() or 0
                    skipped_q_result = await db.execute(
                        select(func.count(Question.id))
                        .join(KeyPosition)
                        .where(KeyPosition.game_id == game_id)
                        .where(Question.skipped == True)
                    )
                    skipped_q = skipped_q_result.scalar_one() or 0
                    reflection = provider._generate_template_reflection(
                        {}, game.player_color, total_q, skipped_q
                    )
                    game.reflection = reflection
                    await db.execute(
                        update(Game)
                        .where(Game.id == game_id)
                        .values(state=GameState.COMPLETED, reflection=reflection)
                    )
                    await db.commit()
                    await db.refresh(game)
                    logger.info(f"[GET_REFLECTION] Used template reflection as fallback for game {game_id}")
                except Exception as fallback_error:
                    logger.error(f"[GET_REFLECTION] Even template reflection failed: {fallback_error}")
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to generate reflection. Please try again."
                    )

    # Check if reflection exists
    if not game.reflection:
        logger.warning(f"[GET_REFLECTION] Game {game_id} is COMPLETED but has no reflection. Attempting to generate...")
        try:
            await _generate_reflection_from_answers(db, game_id)
            await db.commit()
            # Refresh game to get updated reflection
            await db.refresh(game)
            logger.info(f"[GET_REFLECTION] Generated reflection for completed game {game_id}")
        except Exception as e:
            logger.error(f"[GET_REFLECTION] Failed to generate reflection for completed game {game_id}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500,
                detail="Reflection generation failed. Please contact support."
            )

    if game.reflection:
        logger.info(f"[GET_REFLECTION] Returning reflection for game {game_id}")
        return game.reflection

    logger.error(f"[GET_REFLECTION] Game {game_id} has no reflection after all attempts")
    raise HTTPException(
        status_code=500,
        detail="Reflection not available for this game"
    )
