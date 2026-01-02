"""
Advanced Position Analyzer for Critical Position Detection

This module provides sophisticated analysis of chess positions to identify
critical moments that are most valuable for coaching. It goes beyond simple
evaluation changes to detect tactical patterns, move quality, and positional
transitions.
"""

import chess
import chess.pgn
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PositionAnalysis:
    """Comprehensive analysis of a chess position."""
    fen: str
    move_number: int
    half_move_number: int
    is_player_turn: bool
    played_move: Optional[str]  # The move that was actually played (if available)
    
    # Engine analysis
    eval_score: float
    best_move: str
    threats: List[str]
    depth: int
    
    # Positional features
    material_balance: float  # Positive = player advantage, negative = opponent advantage
    tactical_patterns: List[str]  # e.g., ["fork", "pin", "skewer"]
    king_safety_score: float  # Lower = more vulnerable
    piece_activity_score: float  # Higher = more active pieces
    
    # Criticality metrics
    criticality_score: float  # Overall criticality (0-100)
    reason_code: str  # OPP_INTENT, THREAT_AWARENESS, or TRANSITION
    move_quality_score: float  # How good was the played move vs best move (0-1)


class PositionAnalyzer:
    """
    Analyzes chess positions to identify critical moments for coaching.
    """
    
    # Material values (in pawns)
    PIECE_VALUES = {
        chess.PAWN: 1.0,
        chess.KNIGHT: 3.0,
        chess.BISHOP: 3.2,
        chess.ROOK: 5.0,
        chess.QUEEN: 9.0,
        chess.KING: 0.0  # Not counted in material
    }
    
    def __init__(self):
        pass
    
    def analyze_position(
        self,
        fen: str,
        move_number: int,
        half_move_number: int,
        is_player_turn: bool,
        engine_analysis: Dict,
        played_move: Optional[str] = None,
        previous_eval: Optional[float] = None
    ) -> PositionAnalysis:
        """
        Perform comprehensive analysis of a position.
        
        Args:
            fen: Position FEN string
            move_number: Full move number
            half_move_number: Half-move (ply) number
            is_player_turn: Whether it's the player's turn
            engine_analysis: Dict with score, best_move, threats, depth
            played_move: The move that was actually played (in UCI format, e.g., "e2e4")
            previous_eval: Evaluation from previous position (for transition detection)
        
        Returns:
            PositionAnalysis object with comprehensive analysis
        """
        board = chess.Board(fen)
        
        # Extract engine data
        eval_score = engine_analysis.get("score", 0.0)
        best_move = engine_analysis.get("best_move", "")
        threats = engine_analysis.get("threats", [])
        depth = engine_analysis.get("depth", 0)
        
        # Analyze positional features
        material_balance = self._calculate_material_balance(board, is_player_turn)
        tactical_patterns = self._detect_tactical_patterns(board, is_player_turn)
        king_safety_score = self._assess_king_safety(board, is_player_turn)
        piece_activity_score = self._assess_piece_activity(board, is_player_turn)
        
        # Analyze move quality (if we know what was played)
        move_quality_score = self._analyze_move_quality(
            board, played_move, best_move, eval_score, is_player_turn
        )
        
        # Calculate criticality score
        criticality_score = self._calculate_criticality_score(
            eval_score=eval_score,
            previous_eval=previous_eval,
            material_balance=material_balance,
            tactical_patterns=tactical_patterns,
            king_safety_score=king_safety_score,
            move_quality_score=move_quality_score,
            threats=threats,
            depth=depth
        )
        
        # Determine reason code
        reason_code = self._determine_reason_code(
            eval_score=eval_score,
            previous_eval=previous_eval,
            tactical_patterns=tactical_patterns,
            threats=threats,
            move_quality_score=move_quality_score,
            material_balance=material_balance
        )
        
        return PositionAnalysis(
            fen=fen,
            move_number=move_number,
            half_move_number=half_move_number,
            is_player_turn=is_player_turn,
            played_move=played_move,
            eval_score=eval_score,
            best_move=best_move,
            threats=threats,
            depth=depth,
            material_balance=material_balance,
            tactical_patterns=tactical_patterns,
            king_safety_score=king_safety_score,
            piece_activity_score=piece_activity_score,
            criticality_score=criticality_score,
            reason_code=reason_code,
            move_quality_score=move_quality_score
        )
    
    def _calculate_material_balance(self, board: chess.Board, is_player_turn: bool) -> float:
        """
        Calculate material balance from player's perspective.
        Positive = player has more material, negative = opponent has more.
        """
        player_material = 0.0
        opponent_material = 0.0
        
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece is None:
                continue
            
            value = self.PIECE_VALUES.get(piece.piece_type, 0.0)
            
            if (piece.color == chess.WHITE and is_player_turn) or \
               (piece.color == chess.BLACK and not is_player_turn):
                player_material += value
            else:
                opponent_material += value
        
        return player_material - opponent_material
    
    def _detect_tactical_patterns(self, board: chess.Board, is_player_turn: bool) -> List[str]:
        """
        Detect tactical patterns in the position.
        Returns list of patterns like ["fork", "pin", "skewer", "discovered_attack"]
        """
        patterns = []
        
        # Get the side to move
        side_to_move = chess.WHITE if is_player_turn else chess.BLACK
        opponent = not side_to_move
        
        # Check for forks (piece attacking two or more pieces)
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece is None or piece.color != side_to_move:
                continue
            
            # Get all squares this piece attacks
            attacks = board.attacks(square)
            attacked_pieces = []
            
            for attacked_square in attacks:
                attacked_piece = board.piece_at(attacked_square)
                if attacked_piece and attacked_piece.color == opponent:
                    attacked_pieces.append(attacked_piece)
            
            if len(attacked_pieces) >= 2:
                # Check if it's a fork (attacking multiple valuable pieces)
                valuable_targets = sum(1 for p in attacked_pieces if self.PIECE_VALUES.get(p.piece_type, 0) >= 3.0)
                if valuable_targets >= 2:
                    patterns.append("fork")
        
        # Check for pins
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece is None or piece.color != opponent:
                continue
            
            # Check if this piece is pinned
            if self._is_pinned(board, square, opponent):
                patterns.append("pin")
        
        # Check for skewers (similar to pins but attacking a valuable piece)
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece is None or piece.color != opponent:
                continue
            
            if self._is_skewered(board, square, opponent):
                patterns.append("skewer")
        
        # Check for discovered attacks
        if self._has_discovered_attack(board, side_to_move):
            patterns.append("discovered_attack")
        
        return list(set(patterns))  # Remove duplicates
    
    def _is_pinned(self, board: chess.Board, square: int, color: chess.Color) -> bool:
        """Check if a piece is pinned."""
        # Use chess library's built-in pin detection
        try:
            # Check if the piece is pinned to the king
            king_square = board.king(color)
            if king_square is None:
                return False
            
            # A piece is pinned if it cannot move without exposing the king to check
            piece = board.piece_at(square)
            if piece is None or piece.piece_type == chess.KING:
                return False
            
            # Check if removing this piece exposes the king
            board_copy = board.copy()
            board_copy.remove_piece_at(square)
            
            # If king is now in check, the piece was pinned
            return board_copy.is_check()
        except Exception:
            return False
    
    def _is_skewered(self, board: chess.Board, square: int, color: chess.Color) -> bool:
        """Check if a piece is skewered (attacked through a less valuable piece)."""
        # A skewer is like a pin, but the valuable piece is in front
        piece = board.piece_at(square)
        if piece is None:
            return False
        
        piece_value = self.PIECE_VALUES.get(piece.piece_type, 0)
        if piece_value < 3.0:  # Only valuable pieces can be skewered
            return False
        
        # Check if this piece is attacked and there's a less valuable piece behind it
        # This is a simplified check - a full implementation would check the line of attack
        if board.is_attacked_by(not color, square):
            # Check if there's a less valuable piece on the same line
            # For now, use pin detection as a proxy
            return self._is_pinned(board, square, color)
        
        return False
    
    def _has_discovered_attack(self, board: chess.Board, color: chess.Color) -> bool:
        """Check if there's a discovered attack opportunity."""
        # A discovered attack occurs when moving a piece reveals an attack
        # This is a simplified check - look for pieces that can move to reveal attacks
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece is None or piece.color != color:
                continue
            
            # Get legal moves for this piece
            for move in board.legal_moves:
                if move.from_square == square:
                    # Check if moving this piece reveals an attack
                    board_copy = board.copy()
                    board_copy.push(move)
                    
                    # Check if we now attack something valuable
                    for target_square in chess.SQUARES:
                        target_piece = board_copy.piece_at(target_square)
                        if target_piece and target_piece.color != color:
                            if board_copy.is_attacked_by(color, target_square):
                                target_value = self.PIECE_VALUES.get(target_piece.piece_type, 0)
                                if target_value >= 3.0:
                                    return True
        
        return False
    
    def _assess_king_safety(self, board: chess.Board, is_player_turn: bool) -> float:
        """
        Assess king safety. Lower score = more vulnerable.
        Returns a score from 0-100, where 100 is perfectly safe.
        """
        side_to_move = chess.WHITE if is_player_turn else chess.BLACK
        king_square = board.king(side_to_move)
        
        if king_square is None:
            return 0.0
        
        safety_score = 100.0
        
        # Check if king is in check
        if board.is_check():
            safety_score -= 30.0
        
        # Count attackers around the king
        attackers = board.attackers(not side_to_move, king_square)
        safety_score -= len(attackers) * 10.0
        
        # Check pawn shield (pawns protecting the king)
        king_rank = chess.square_rank(king_square)
        king_file = chess.square_file(king_square)
        
        pawn_shield = 0
        for file_offset in [-1, 0, 1]:
            file = king_file + file_offset
            if 0 <= file < 8:
                if side_to_move == chess.WHITE:
                    # Check rank in front of king
                    shield_square = chess.square(file, king_rank - 1)
                else:
                    shield_square = chess.square(file, king_rank + 1)
                
                if 0 <= shield_square < 64:
                    piece = board.piece_at(shield_square)
                    if piece and piece.piece_type == chess.PAWN and piece.color == side_to_move:
                        pawn_shield += 1
        
        safety_score += pawn_shield * 5.0
        
        return max(0.0, min(100.0, safety_score))
    
    def _assess_piece_activity(self, board: chess.Board, is_player_turn: bool) -> float:
        """
        Assess piece activity. Higher score = more active pieces.
        Returns a score from 0-100.
        """
        side_to_move = chess.WHITE if is_player_turn else chess.BLACK
        activity_score = 0.0
        piece_count = 0
        
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece is None or piece.color != side_to_move:
                continue
            
            piece_count += 1
            # Count squares this piece attacks
            attacks = board.attacks(square)
            activity_score += len(attacks)
        
        if piece_count == 0:
            return 0.0
        
        # Normalize to 0-100 scale
        avg_activity = activity_score / piece_count
        normalized = min(100.0, (avg_activity / 8.0) * 100.0)  # 8 is max possible for a piece
        
        return normalized
    
    def _analyze_move_quality(
        self,
        board: chess.Board,
        played_move: Optional[str],
        best_move: str,
        eval_score: float,
        is_player_turn: bool
    ) -> float:
        """
        Analyze the quality of the played move compared to the best move.
        Returns a score from 0-1, where 1 = best move, 0 = worst move.
        """
        if not played_move or not best_move:
            return 0.5  # Unknown quality
        
        # If played move is the best move, it's perfect
        if played_move.lower() == best_move.lower():
            return 1.0
        
        # Try to evaluate the position after the played move
        try:
            # Parse the played move
            move = chess.Move.from_uci(played_move)
            if move not in board.legal_moves:
                return 0.0  # Illegal move
            
            # Make the move and evaluate (simplified - would need engine for accurate comparison)
            board_copy = board.copy()
            board_copy.push(move)
            
            # For now, use a heuristic: if the move is legal and not obviously bad, give it some credit
            # In a full implementation, we'd compare engine evaluations of both moves
            return 0.6  # Default: decent but not best
        except (ValueError, AttributeError):
            return 0.5  # Can't parse move
    
    def _calculate_criticality_score(
        self,
        eval_score: float,
        previous_eval: Optional[float],
        material_balance: float,
        tactical_patterns: List[str],
        king_safety_score: float,
        move_quality_score: float,
        threats: List[str],
        depth: int
    ) -> float:
        """
        Calculate overall criticality score (0-100).
        Higher score = more critical position for coaching.
        """
        score = 0.0
        
        # 1. Evaluation swing (transition) - up to 30 points
        if previous_eval is not None:
            eval_change = abs(eval_score - previous_eval)
            if eval_change > 0.5:
                score += min(30.0, eval_change * 15.0)  # Scale: 0.5 change = 7.5 points, 2.0 change = 30 points
        
        # 2. Tactical patterns - up to 25 points
        if tactical_patterns:
            score += min(25.0, len(tactical_patterns) * 8.0)
        
        # 3. Threats detected - up to 20 points
        if threats:
            score += min(20.0, len(threats) * 5.0)
        
        # 4. King safety issues - up to 15 points
        if king_safety_score < 50.0:
            score += (50.0 - king_safety_score) / 50.0 * 15.0
        
        # 5. Move quality (suboptimal moves are more critical) - up to 10 points
        if move_quality_score < 0.7:
            score += (0.7 - move_quality_score) / 0.7 * 10.0
        
        # 6. Large evaluation imbalance - up to 10 points
        if abs(eval_score) > 1.0:
            score += min(10.0, (abs(eval_score) - 1.0) * 5.0)
        
        # 7. Material imbalance - up to 5 points
        if abs(material_balance) > 2.0:
            score += min(5.0, (abs(material_balance) - 2.0) * 1.0)
        
        return min(100.0, score)
    
    def _determine_reason_code(
        self,
        eval_score: float,
        previous_eval: Optional[float],
        tactical_patterns: List[str],
        threats: List[str],
        move_quality_score: float,
        material_balance: float
    ) -> str:
        """
        Determine the most appropriate reason code for this position.
        """
        # Priority 1: Tactical patterns (forks, pins, etc.) -> THREAT_AWARENESS
        if tactical_patterns:
            return "THREAT_AWARENESS"
        
        # Priority 2: Threats detected -> THREAT_AWARENESS
        if threats:
            return "THREAT_AWARENESS"
        
        # Priority 3: Significant evaluation change -> TRANSITION
        if previous_eval is not None:
            eval_change = abs(eval_score - previous_eval)
            if eval_change > 0.5:
                return "TRANSITION"
        
        # Priority 4: Large evaluation imbalance (missed opponent plan) -> OPP_INTENT
        if abs(eval_score) > 1.0:
            return "OPP_INTENT"
        
        # Priority 5: Poor move quality (likely missed something) -> OPP_INTENT
        if move_quality_score < 0.6:
            return "OPP_INTENT"
        
        # Default: THREAT_AWARENESS
        return "THREAT_AWARENESS"
    
    def rank_positions(self, analyses: List[PositionAnalysis]) -> List[PositionAnalysis]:
        """
        Rank positions by criticality score (highest first).
        """
        return sorted(analyses, key=lambda a: a.criticality_score, reverse=True)
    
    def select_key_positions(
        self,
        analyses: List[PositionAnalysis],
        min_positions: int = 3,
        max_positions: int = 5
    ) -> List[PositionAnalysis]:
        """
        Select the most critical positions for coaching.
        Ensures diversity by avoiding positions that are too close together.
        """
        if len(analyses) == 0:
            return []
        
        # Rank by criticality
        ranked = self.rank_positions(analyses)
        
        # Select top positions, but ensure some diversity in move numbers
        selected = []
        used_move_numbers = set()
        
        for analysis in ranked:
            if len(selected) >= max_positions:
                break
            
            # Avoid selecting positions too close together (within 3 moves)
            too_close = any(
                abs(analysis.move_number - used_move) < 3
                for used_move in used_move_numbers
            )
            
            if not too_close or len(selected) < min_positions:
                selected.append(analysis)
                used_move_numbers.add(analysis.move_number)
        
        # If we don't have enough, fill with remaining high-scoring positions
        if len(selected) < min_positions:
            for analysis in ranked:
                if analysis not in selected:
                    selected.append(analysis)
                    if len(selected) >= min_positions:
                        break
        
        return selected[:max_positions]

