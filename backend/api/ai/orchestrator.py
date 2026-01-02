import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from api.common.models import Game, GameState, KeyPosition, Question, Annotation
from api.common.config import settings
from api.ai.validators.orchestrator_validator import validate_analyzer_output
from api.ai.providers.engine import ChessEngineProvider
from api.ai.providers.socratic_questioner import SocraticQuestionerProvider
from api.ai.position_analyzer import PositionAnalyzer, PositionAnalysis
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
        self.position_analyzer = PositionAnalyzer()

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
                # Get the move that was played (in UCI format)
                played_move_uci = next_node.move.uci() if next_node.move else None
                
                positions.append({
                    "fen": board.fen(),
                    "move_number": full_move_number,  # Store full move number for clarity
                    "half_move_number": move_count,  # Also store half-move for reference
                    "is_player_turn": is_player_turn,
                    "played_move": played_move_uci  # Store the move that was actually played
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
        
        # Analyze positions to find key moments using advanced position analyzer
        if len(positions) == 0:
            print(f"DEBUG: No positions to analyze for game {game.id}")
            return {"key_positions": []}
        
        # Analyze all positions (or sample if too many to avoid API rate limits)
        # Sample up to 10 positions for analysis, then select the best 3-5
        max_positions_to_analyze = min(10, len(positions))
        if len(positions) > max_positions_to_analyze:
            # Sample evenly distributed positions
            step = max(1, len(positions) // max_positions_to_analyze)
            positions_to_analyze = positions[::step][:max_positions_to_analyze]
        else:
            positions_to_analyze = positions
        
        import asyncio
        import logging
        logger = logging.getLogger(__name__)
        
        # Analyze all sampled positions with engine and position analyzer
        position_analyses = []
        previous_eval = None
        
        for pos_data in positions_to_analyze:
            try:
                # Analyze position with engine (with fallback on error)
                analysis = await asyncio.wait_for(
                    self.engine.analyze_position(pos_data["fen"], fallback_on_error=True),
                    timeout=60.0  # Max 60 seconds per position
                )
                
                # Use advanced position analyzer for comprehensive analysis
                position_analysis = self.position_analyzer.analyze_position(
                    fen=pos_data["fen"],
                    move_number=pos_data["move_number"],
                    half_move_number=pos_data["half_move_number"],
                    is_player_turn=pos_data["is_player_turn"],
                    engine_analysis=analysis,
                    played_move=pos_data.get("played_move"),
                    previous_eval=previous_eval
                )
                
                position_analyses.append(position_analysis)
                previous_eval = position_analysis.eval_score
                
                logger.debug(
                    f"Position {pos_data['move_number']}: "
                    f"criticality={position_analysis.criticality_score:.1f}, "
                    f"reason={position_analysis.reason_code}, "
                    f"tactics={position_analysis.tactical_patterns}"
                )
                
            except asyncio.TimeoutError:
                logger.warning(f"Position analysis timed out for {pos_data['fen']}, skipping")
                continue
            except Exception as e:
                logger.warning(f"Error analyzing position {pos_data['fen']}: {e}")
                continue
        
        # Select the most critical positions using the analyzer's selection method
        if len(position_analyses) == 0:
            logger.warning(f"No positions successfully analyzed for game {game.id}")
            # Fallback to old method if analyzer fails completely
            return self._fallback_key_positions(positions, chess_game, game.id)
        
        selected_analyses = self.position_analyzer.select_key_positions(
            position_analyses,
            min_positions=3,
            max_positions=5
        )
        
        # Convert PositionAnalysis objects to key_positions format
        key_positions = []
        for analysis in selected_analyses:
            key_positions.append({
                "fen": analysis.fen,
                "reason_code": analysis.reason_code,
                "engine_truth": {
                    "score": analysis.eval_score,
                    "best_move": analysis.best_move,
                    "threats": analysis.threats if analysis.threats else []
                }
            })
        
        logger.info(
            f"Selected {len(key_positions)} key positions with criticality scores: "
            f"{[f'{a.criticality_score:.1f}' for a in selected_analyses]}"
        )
        
        # Ensure we have at least 1 key position (minimum for pipeline to work)
        if len(key_positions) == 0:
            logger.warning(f"No key positions selected, using fallback for game {game.id}")
            return self._fallback_key_positions(positions, chess_game, game.id)
        
        # Ensure we have 3-5 key positions (preferred)
        if len(key_positions) < 3 and len(position_analyses) > len(key_positions):
            # Add more positions from remaining analyses
            remaining = [a for a in position_analyses if a.fen not in [kp["fen"] for kp in key_positions]]
            remaining_sorted = sorted(remaining, key=lambda a: a.criticality_score, reverse=True)
            
            for analysis in remaining_sorted[:3-len(key_positions)]:
                key_positions.append({
                    "fen": analysis.fen,
                    "reason_code": analysis.reason_code,
                    "engine_truth": {
                        "score": analysis.eval_score,
                        "best_move": analysis.best_move,
                        "threats": analysis.threats if analysis.threats else []
                    }
                })
        
        if len(key_positions) > 5:
            # If we have too many, take the top 5 by criticality
            key_positions = key_positions[:5]
        
        output = {"key_positions": key_positions}
        logger.info(f"Analyzer output: {len(key_positions)} key positions found")
        return output
    
    def _fallback_key_positions(self, positions: List[Dict], chess_game, game_id: int) -> Dict:
        """
        Fallback method when advanced analyzer fails.
        Uses simple heuristics to select positions.
        """
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Using fallback key position selection for game {game_id}")
        
        if len(positions) == 0:
            # Last resort: use a position from the middle/end of the game
            import chess
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
                return {
                    "key_positions": [{
                        "fen": board.fen(),
                        "reason_code": "THREAT_AWARENESS",
                        "engine_truth": {
                            "score": 0.0,
                            "best_move": "",
                            "threats": []
                        }
                    }]
                }
            else:
                return {"key_positions": []}
        
        # Use simple distribution: take evenly spaced positions
        sample_size = min(3, len(positions))
        step = max(1, len(positions) // sample_size)
        sampled = positions[::step][:sample_size]
        
        key_positions = []
        reason_codes = ["OPP_INTENT", "THREAT_AWARENESS", "TRANSITION"]
        
        for i, pos_data in enumerate(sampled):
            key_positions.append({
                "fen": pos_data["fen"],
                "reason_code": reason_codes[i % len(reason_codes)],
                "engine_truth": {
                    "score": 0.0,
                    "best_move": "",
                    "threats": []
                }
            })
        
        return {"key_positions": key_positions}

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
