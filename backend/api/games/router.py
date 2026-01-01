from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from api.common.database import get_db
from api.common.models import Game, GameState, Annotation, Question, KeyPosition, ParentApproval
from datetime import datetime, timezone
from api.auth.middleware import AuthMiddleware
from pydantic import BaseModel, Field
from api.ai.orchestrator import AIOrchestrator
import redis.asyncio as redis
from api.common.config import settings
from typing import Optional

router = APIRouter(prefix="/games", tags=["games"])

class GameSubmit(BaseModel):
    pgn: str
    tier: str = Field(default="STANDARD")

class AnnotationCreate(BaseModel):
    move_number: int
    content: str

@router.get("")
@router.get("/")
async def get_games(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Game).order_by(Game.created_at.desc()))
    return result.scalars().all()

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
    
    game = Game(
        user_id=user_id,
        state=GameState.EDITABLE,
        player_color=game_data.player_color,
        opponent_name=game_data.opponent_name,
        event=game_data.event,
        date=game_data.date,
        time_control=game_data.time_control,
        pgn=game_data.pgn
    )
    db.add(game)
    await db.flush() # Get game.id

    # If PGN is provided, extract and save existing annotations
    if game_data.pgn:
        from chess import pgn
        import io
        pgn_io = io.StringIO(game_data.pgn)
        chess_game = pgn.read_game(pgn_io)
        if chess_game:
            board = chess_game.board()
            # Annotations are on nodes (moves)
            # Traverse the game tree
            node = chess_game
            move_number = 1
            while node.variations:
                next_node = node.variation(0)
                comment = next_node.comment
                
                # Check if it's a player move
                is_player_move = False
                if game_data.player_color == 'WHITE':
                    is_player_move = board.turn == True
                else:
                    is_player_move = board.turn == False

                if comment and is_player_move:
                    # Requirement 5.1: Annotations SHALL be allowed only on player moves
                    # move_number in our system is currently used as half-move index or move pair?
                    # The table says "move_number INT". Let's use the ply (half-move) index.
                    ply = board.fullmove_number * 2 - (1 if board.turn else 0)
                    annotation = Annotation(
                        game_id=game.id,
                        move_number=ply,
                        content=comment,
                        frozen=False
                    )
                    db.add(annotation)
                
                board.push(next_node.move)
                node = next_node
                move_number += 1 

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

@router.delete("/{game_id}")
async def delete_game(game_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Game).where(Game.id == game_id))
    game = result.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    await db.delete(game)
    await db.commit()
    return {"message": "Game deleted successfully"}

@router.post("/{game_id}/submit")
async def submit_game(game_id: int, submit_data: GameSubmit, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """
    Implements PHASE 2: Game Lifecycle enforcement and PHASE 7: Parent Approval.
    EDITABLE -> SUBMITTED -> COACHING -> COMPLETED
    """
    print(f"DEBUG: submit_game called for id={game_id} with tier={submit_data.tier}")
    # Fetch game
    result = await db.execute(select(Game).where(Game.id == game_id))
    game = result.scalar_one_or_none()
    
    if not game:
        print(f"DEBUG: Game {game_id} not found")
        raise HTTPException(status_code=404, detail="Game not found")

    # Idempotency (Implementation Spec 6.2)
    if game.state == GameState.SUBMITTED:
        print(f"DEBUG: Game {game_id} already submitted")
        return {"message": "Game already submitted", "state": game.state}

    # Transition Rule: Only EDITABLE -> SUBMITTED is allowed here
    if game.state != GameState.EDITABLE:
        print(f"DEBUG: Invalid transition from {game.state} for game {game_id}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail=f"Invalid transition from {game.state} to SUBMITTED"
        )

    # PHASE 7: Parent Approval Gate (Compliance Requirement)
    # Check if this is a repeat run or a non-default tier
    # v2.1 Requirement: "Non-default tier ALWAYS requires approval", "Second AI run on same game ALWAYS requires approval"
    
    # Check for previous COMPLETED runs
    prev_runs = await db.execute(
        select(Game).where(Game.id == game_id).where(Game.state == GameState.COMPLETED)
    )
    is_repeat_run = prev_runs.scalar_one_or_none() is not None

    if submit_data.tier != "STANDARD" or is_repeat_run:
        print(f"DEBUG: Approval check needed for game {game_id}. Repeat: {is_repeat_run}, Tier: {submit_data.tier}")
        # Verify valid, unused ParentApproval exists
        now = datetime.now(timezone.utc)
        approval_result = await db.execute(
            select(ParentApproval)
            .where(ParentApproval.game_id == game_id)
            .where(ParentApproval.tier == submit_data.tier)
            .where(ParentApproval.approved == True)
            .where(ParentApproval.used == False)
            .where(ParentApproval.expires_at > now)
        )
        approval = approval_result.scalar_one_or_none()
        
        if not approval:
            print(f"DEBUG: Approval missing or invalid for game {game_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Parent approval required for {submit_data.tier} tier or repeat run"
            )
        
        # Mark approval as used
        approval.used = True
        print(f"DEBUG: Approval verified and marked as used for game {game_id}")

    # Update PGN from client submission
    game.pgn = submit_data.pgn

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
    print(f"DEBUG: Game {game_id} state updated to SUBMITTED and committed")

    # Trigger AI Pipeline asynchronously
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        orchestrator = AIOrchestrator(db, redis_client)
        background_tasks.add_task(orchestrator.run_pipeline, game_id, submit_data.tier)
        print(f"DEBUG: AI pipeline background task added for game {game_id}")
    except Exception as e:
        print(f"DEBUG: Error triggering AI pipeline for game {game_id}: {str(e)}")

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
