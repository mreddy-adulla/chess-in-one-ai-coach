from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from api.common.database import get_db
from api.common.models import Game, GameState, Question, KeyPosition
from pydantic import BaseModel
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/questions", tags=["questions"])

class QuestionAnswer(BaseModel):
    content: str = ""
    skipped: bool = False

@router.post("/{question_id}/answer")
async def answer_question(question_id: int, answer_data: QuestionAnswer, db: AsyncSession = Depends(get_db)):
    logger.info(f"[ANSWER_QUESTION] Starting answer_question for question_id={question_id}, skipped={answer_data.skipped}, answer_length={len(answer_data.content) if answer_data.content else 0}")
    
    async with db.begin():
        result = await db.execute(
            select(Question)
            .options(selectinload(Question.key_position))
            .where(Question.id == question_id)
        )
        question = result.scalar_one_or_none()
        
        if not question:
            logger.error(f"[ANSWER_QUESTION] Question {question_id} not found")
            raise HTTPException(status_code=404, detail="Question not found")
        
        logger.info(f"[ANSWER_QUESTION] Found question {question_id} for key_position {question.key_position_id}")
            
        # Implementation Spec 7.2: Each question accepts exactly one answer or skip
        if question.answer_text or question.skipped:
            logger.warning(f"[ANSWER_QUESTION] Question {question_id} already answered (answer_text={bool(question.answer_text)}, skipped={question.skipped})")
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Question already answered")
        
        if answer_data.skipped:
            question.skipped = True
            logger.info(f"[ANSWER_QUESTION] Marked question {question_id} as skipped")
        else:
            question.answer_text = answer_data.content
            logger.info(f"[ANSWER_QUESTION] Set answer_text for question {question_id}")
        
        # Check if all questions for this game are answered
        # If so, transition to COMPLETED
        game_id = question.key_position.game_id
        logger.info(f"[ANSWER_QUESTION] Checking remaining questions for game {game_id}")
        
        result = await db.execute(
            select(Question)
            .join(KeyPosition)
            .where(KeyPosition.game_id == game_id)
            .where(Question.answer_text == None)
            .where(Question.skipped == False)
        )
        remaining = result.scalars().all()
        remaining_count = len(remaining)
        logger.info(f"[ANSWER_QUESTION] Game {game_id} has {remaining_count} remaining unanswered questions")
        
        if not remaining:
            logger.info(f"[ANSWER_QUESTION] All questions answered for game {game_id}. Generating reflection...")
            # All questions answered - generate reflection and transition to COMPLETED
            try:
                await _generate_reflection_from_answers(db, game_id)
                logger.info(f"[ANSWER_QUESTION] Reflection generated successfully for game {game_id}")
            except Exception as e:
                logger.error(f"[ANSWER_QUESTION] Failed to generate reflection for game {game_id}: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                raise
            
            # Transition game to COMPLETED
            await db.execute(
                update(Game)
                .where(Game.id == game_id)
                .values(state=GameState.COMPLETED)
            )
            logger.info(f"[ANSWER_QUESTION] Game {game_id} transitioned to COMPLETED state")
        else:
            logger.info(f"[ANSWER_QUESTION] Game {game_id} still has {remaining_count} unanswered questions. Not generating reflection yet.")

        await db.commit()
        logger.info(f"[ANSWER_QUESTION] Committed answer for question {question_id}")
        
    return {"message": "Answer recorded"}


async def _generate_reflection_from_answers(db: AsyncSession, game_id: int):
    """
    Generate reflection based on user's answers to questions using AI.
    Implementation Spec: Reflection Generator contract.
    """
    logger.info(f"[GENERATE_REFLECTION] Starting reflection generation for game {game_id}")
    
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
    # Fetch game object again to update it
    game_result = await db.execute(select(Game).where(Game.id == game_id))
    game = game_result.scalar_one_or_none()
    if game:
        game.reflection = reflection
        await db.flush()
        logger.info(f"[GENERATE_REFLECTION] Successfully stored reflection for game {game_id}. Reflection type: {type(reflection)}")
    else:
        logger.error(f"[GENERATE_REFLECTION] Game {game_id} not found when storing reflection")

