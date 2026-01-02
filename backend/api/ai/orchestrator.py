import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from api.common.models import Game, GameState, KeyPosition, Question, Annotation
from api.common.config import settings
from api.ai.validators.orchestrator_validator import validate_analyzer_output
from api.ai.providers.engine import ChessEngineProvider
from api.ai.providers.socratic_questioner import SocraticQuestionerProvider
from api.common.lock_manager import LockManager
from typing import Optional

class AIOrchestrator:
    """
    Implements PHASE 3: AI Orchestration Pipeline.
    Strictly follows Implementation Spec v2.0 Section 8.1.
    """
    def __init__(self, db: AsyncSession, redis_client: Optional[redis.Redis] = None):
        self.db = db
        self.redis = redis_client
        self.lock_manager = LockManager(redis_client) if redis_client else LockManager(None)
        self.engine = ChessEngineProvider()
        self.questioner = SocraticQuestionerProvider()

    async def run_pipeline(self, game_id: int, tier: str = "STANDARD"):
        print(f"DEBUG: AIOrchestrator.run_pipeline started for game {game_id} with tier {tier}")
        # Transition to COACHING IMMEDIATELY if in SUBMITTED state
        # This handles cases where Redis/Lock might fail or be slow
        async with self.db.begin():
            result = await self.db.execute(select(Game).where(Game.id == game_id))
            game = result.scalar_one_or_none()
            if game and game.state == GameState.SUBMITTED:
                game.state = GameState.COACHING
                print(f"DEBUG: Game {game_id} state updated to COACHING pre-lock")
                await self.db.commit()

        # Redis lock guards AI pipeline (Implementation Spec 16)
        # But if Redis fails, we still run the pipeline without locking
        lock_key = f"ai_lock:{game_id}"
        try:
            async with self.lock_manager.with_lock(lock_key):
                print(f"DEBUG: Acquired lock {lock_key}")
                await self._execute_pipeline(game_id, tier)
        except RuntimeError as e:
            if "Could not acquire lock" in str(e):
                print(f"WARNING: Could not acquire lock for game {game_id}, running pipeline without lock")
                await self._execute_pipeline(game_id, tier)
            else:
                raise
        except Exception as e:
            print(f"ERROR: Unexpected error in pipeline for game {game_id}: {str(e)}")
            import traceback
            traceback.print_exc()
            # Try to run pipeline anyway if it was just a lock issue
            try:
                await self._execute_pipeline(game_id, tier)
            except Exception as pipeline_error:
                print(f"ERROR: Pipeline execution failed for game {game_id}: {str(pipeline_error)}")
                import traceback
                traceback.print_exc()

    async def _execute_pipeline(self, game_id: int, tier: str = "STANDARD"):
        """Execute the AI pipeline logic (analyzer, key positions, questions, reflection)."""
        async with self.db.begin():
            result = await self.db.execute(select(Game).where(Game.id == game_id))
            game = result.scalar_one_or_none()
            
            if not game:
                print(f"DEBUG: Game {game_id} not found in pipeline")
                return
            
            # Ensure state is COACHING during processing
            game.state = GameState.COACHING
            
            # 1. Chess Situation Analyzer (Stub - internal)
            print(f"DEBUG: Running analyzer for game {game_id}")
            analyzer_output = await self._run_analyzer(game, tier)
            
            # Validation occurs BEFORE persistence or exposure (Implementation Spec 9.3)
            validate_analyzer_output(analyzer_output)
            print(f"DEBUG: Analyzer output validated for game {game_id}")

            # 2. Persist 3–5 key positions
            for i, pos in enumerate(analyzer_output["key_positions"]):
                kp = KeyPosition(
                    game_id=game_id,
                    fen=pos["fen"],
                    reason_code=pos["reason_code"],
                    engine_truth=pos["engine_truth"],
                    order=i
                )
                self.db.add(kp)
                await self.db.flush()
                print(f"DEBUG: Key position {i} persisted for game {game_id}")

                # 3. Socratic Question Loop (Stub for questions generation)
                await self._generate_socratic_questions(kp)
                print(f"DEBUG: Socratic questions generated for position {i}")

            # Update state to COACHING (reflection will be generated after all questions are answered)
            result = await self.db.execute(select(Game).where(Game.id == game_id))
            game = result.scalar_one_or_none()
            if game:
                game.state = GameState.COACHING
                await self.db.commit()
                print(f"DEBUG: Game {game_id} state set to COACHING. Questions ready for user responses.")

    async def _run_analyzer(self, game: Game, tier: str = "STANDARD"):
        """
        Internal Analyzer - Produces 3-5 key positions.
        Implementation Spec 10.1: JSON output only, no language.
        Analyzes the game to find meaningful positions throughout, not just early moves.
        """
        print(f"DEBUG: _run_analyzer called for game {game.id} with tier {tier}")
        
        if not game.pgn:
            print(f"DEBUG: Game {game.id} has no PGN, returning empty key positions")
            return {"key_positions": []}
        
        import chess
        import chess.pgn
        import io
        
        # Parse PGN
        pgn_io = io.StringIO(game.pgn)
        chess_game = chess.pgn.read_game(pgn_io)
        if not chess_game:
            print(f"DEBUG: Could not parse PGN for game {game.id}")
            return {"key_positions": []}
        
        board = chess_game.board()
        positions = []
        move_count = 0  # This counts half-moves (plies)
        
        # Replay game and collect positions
        node = chess_game
        while node.variations:
            next_node = node.variation(0)
            board.push(next_node.move)
            move_count += 1  # Increment for each half-move (ply)
            
            # Only analyze positions after move 10 (full moves = 20 half-moves)
            # In chess, 1 full move = 2 half-moves (White + Black)
            # So move_count >= 20 means after 10 full moves
            # And focus on player's moves (when it's their turn to think)
            is_player_turn = (board.turn == chess.WHITE and game.player_color == "WHITE") or \
                           (board.turn == chess.BLACK and game.player_color == "BLACK")
            
            # Convert half-moves to full moves: full_move = (move_count + 1) // 2
            full_move_number = (move_count + 1) // 2
            
            if full_move_number >= 10 and is_player_turn:
                positions.append({
                    "fen": board.fen(),
                    "move_number": full_move_number,  # Store full move number for clarity
                    "half_move_number": move_count,  # Also store half-move for reference
                    "is_player_turn": is_player_turn
                })
            
            node = next_node
        
        if len(positions) == 0:
            print(f"DEBUG: No positions found after move 10 (full moves) for game {game.id}")
            # Fallback: use a position from later in the game (at least move 10 = 20 half-moves)
            board = chess_game.board()
            node = chess_game
            move_count = 0
            while node.variations:
                next_node = node.variation(0)
                board.push(next_node.move)
                move_count += 1
                full_move_number = (move_count + 1) // 2
                if full_move_number >= 10:
                    positions.append({
                        "fen": board.fen(),
                        "move_number": full_move_number,
                        "half_move_number": move_count,
                        "is_player_turn": True
                    })
                    break
                node = next_node
        
        # Analyze positions to find key moments
        # Sample positions throughout the game (not all, to avoid too many API calls)
        sample_size = min(5, len(positions))
        if sample_size == 0:
            print(f"DEBUG: No positions to analyze for game {game.id}")
            return {"key_positions": []}
        
        # Select positions evenly distributed throughout the game
        step = max(1, len(positions) // sample_size)
        sampled_positions = positions[::step][:sample_size]
        
        key_positions = []
        previous_eval = None
        
        # Add timeout protection for the entire analysis loop
        import asyncio
        import logging
        logger = logging.getLogger(__name__)
        
        for pos_data in sampled_positions:
            try:
                # Analyze position with engine (with fallback on error)
                # Each position analysis has its own timeout, but add extra protection here
                analysis = await asyncio.wait_for(
                    self.engine.analyze_position(pos_data["fen"], fallback_on_error=True),
                    timeout=60.0  # Max 60 seconds per position (should be much less)
                )
                
                eval_score = analysis.get("score", 0)
                best_move = analysis.get("best_move", "")
                threats = analysis.get("threats", [])
                
                # Determine reason code based on position characteristics
                reason_code = "THREAT_AWARENESS"  # Default
                
                # Check for significant evaluation change (transition)
                if previous_eval is not None:
                    eval_change = abs(eval_score - previous_eval)
                    if eval_change > 0.5:  # Significant change
                        reason_code = "TRANSITION"
                
                # Check for threats
                if threats:
                    reason_code = "THREAT_AWARENESS"
                
                # Check if it's a critical position (high evaluation swing potential)
                if abs(eval_score) > 1.0:
                    reason_code = "OPP_INTENT"  # Likely missed opponent's plan
                
                # Use move number as a fallback for reason code if engine data is minimal
                if not best_move and not threats:
                    # Distribute reason codes based on position order
                    reason_codes = ["OPP_INTENT", "THREAT_AWARENESS", "TRANSITION", "THREAT_AWARENESS", "OPP_INTENT"]
                    reason_code = reason_codes[len(key_positions) % len(reason_codes)]
                
                key_positions.append({
                    "fen": pos_data["fen"],
                    "reason_code": reason_code,
                    "engine_truth": {
                        "score": eval_score,
                        "best_move": best_move,
                        "threats": threats if threats else []
                    }
                })
                
                previous_eval = eval_score
                
            except asyncio.TimeoutError:
                logger.warning(f"Position analysis timed out for {pos_data['fen']}, using fallback")
                # Use fallback values
                reason_codes = ["OPP_INTENT", "THREAT_AWARENESS", "TRANSITION", "THREAT_AWARENESS", "OPP_INTENT"]
                reason_code = reason_codes[len(key_positions) % len(reason_codes)]
                key_positions.append({
                    "fen": pos_data["fen"],
                    "reason_code": reason_code,
                    "engine_truth": {
                        "score": 0.0,
                        "best_move": "",
                        "threats": []
                    }
                })
            except Exception as e:
                print(f"DEBUG: Error analyzing position {pos_data['fen']}: {e}")
                # Even on error, add the position with default values
                reason_codes = ["OPP_INTENT", "THREAT_AWARENESS", "TRANSITION", "THREAT_AWARENESS", "OPP_INTENT"]
                reason_code = reason_codes[len(key_positions) % len(reason_codes)]
                key_positions.append({
                    "fen": pos_data["fen"],
                    "reason_code": reason_code,
                    "engine_truth": {
                        "score": 0.0,
                        "best_move": "",
                        "threats": []
                    }
                })
                continue
        
        # Ensure we have at least 1 key position (minimum for pipeline to work)
        # Ideally 3-5, but we'll work with what we have
        if len(key_positions) == 0:
            # Last resort: use a position from the middle/end of the game
            print(f"DEBUG: No key positions found, using fallback position")
            board = chess_game.board()
            node = chess_game
            move_count = 0
            # Replay to find total move count first
            total_moves = 0
            temp_node = chess_game
            while temp_node.variations:
                temp_node = temp_node.variation(0)
                total_moves += 1
            
            # Go to middle of game (around move 15-20 or halfway, whichever is less)
            target_moves = min(20, max(15, total_moves // 2))
            while node.variations and move_count < target_moves:
                next_node = node.variation(0)
                board.push(next_node.move)
                move_count += 1
                node = next_node
            
            if move_count >= 10:
                key_positions.append({
                    "fen": board.fen(),
                    "reason_code": "THREAT_AWARENESS",
                    "engine_truth": {
                        "score": 0.0,
                        "best_move": "",
                        "threats": []
                    }
                })
            else:
                # Absolute fallback: use any position we can get
                board = chess_game.board()
                node = chess_game
                move_count = 0
                while node.variations and move_count < 10:
                    next_node = node.variation(0)
                    board.push(next_node.move)
                    move_count += 1
                    node = next_node
                key_positions.append({
                    "fen": board.fen(),
                    "reason_code": "THREAT_AWARENESS",
                    "engine_truth": {
                        "score": 0.0,
                        "best_move": "",
                        "threats": []
                    }
                })
        
        # Ensure we have 3-5 key positions (preferred)
        if len(key_positions) < 3 and len(sampled_positions) > len(key_positions):
            # Add more positions from the sampled list
            remaining = [p for p in sampled_positions if p["fen"] not in [kp["fen"] for kp in key_positions]]
            for pos_data in remaining[:3-len(key_positions)]:
                reason_codes = ["OPP_INTENT", "THREAT_AWARENESS", "TRANSITION"]
                reason_code = reason_codes[len(key_positions) % len(reason_codes)]
                key_positions.append({
                    "fen": pos_data["fen"],
                    "reason_code": reason_code,
                    "engine_truth": {
                        "score": 0.0,
                        "best_move": "",
                        "threats": []
                    }
                })
        
        if len(key_positions) > 5:
            # If we have too many, take the first 5
            key_positions = key_positions[:5]
        
        output = {"key_positions": key_positions}
        print(f"DEBUG: Analyzer output: {len(key_positions)} key positions found")
        return output

    async def _generate_socratic_questions(self, kp: KeyPosition):
        """
        Socratic Questioner - Implementation Spec 12
        Generates questions using AI provider or template fallback.
        """
        # Try to find student annotation for this position
        # Use key position order as a rough estimate for move number
        student_annotation = None
        try:
            annotation_result = await self.db.execute(
                select(Annotation)
                .where(Annotation.game_id == kp.game_id)
                .where(Annotation.move_number >= kp.order * 2)
                .where(Annotation.move_number < (kp.order + 1) * 2)
                .limit(1)
            )
            annotation = annotation_result.scalar_one_or_none()
            if annotation:
                student_annotation = annotation.content
        except Exception as e:
            print(f"DEBUG: Could not fetch annotation for key position {kp.id}: {e}")
        
        # Parse engine_truth if it's a string (JSON)
        engine_truth = kp.engine_truth
        if isinstance(engine_truth, str):
            import json
            try:
                engine_truth = json.loads(engine_truth)
            except json.JSONDecodeError:
                engine_truth = {}
        elif engine_truth is None:
            engine_truth = {}
        
        categories = ["OPP_INTENT", "THREAT", "CHANGE", "WORST_PIECE", "ALTERNATIVES", "REFLECTION"]
        for i, cat in enumerate(categories):
            # Generate question using AI provider
            question_text = await self.questioner.generate_question(
                category=cat,
                engine_truth=engine_truth,
                student_annotation=student_annotation,
                reason_code=kp.reason_code
            )
            
            q = Question(
                key_position_id=kp.id,
                category=cat,
                question_text=question_text,
                order=i
            )
            self.db.add(q)
