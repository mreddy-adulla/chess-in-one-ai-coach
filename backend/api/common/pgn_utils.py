"""
PGN parsing utilities shared between services.
"""
from typing import List, Tuple
from api.common.models import Annotation

def extract_annotations_from_pgn(pgn: str, game_id: int, player_color: str) -> List[Annotation]:
    """
    Extract annotations from PGN for player moves only.

    Args:
        pgn: The PGN string
        game_id: ID of the game
        player_color: 'WHITE' or 'BLACK'

    Returns:
        List of Annotation objects
    """
    annotations = []
    from chess import pgn
    import io

    pgn_io = io.StringIO(pgn)
    chess_game = pgn.read_game(pgn_io)
    if not chess_game:
        return annotations

    board = chess_game.board()
    node = chess_game

    while node.variations:
        next_node = node.variation(0)
        comment = next_node.comment

        # Determine if it's a player move
        is_player_move = _is_player_move(board.turn, player_color)

        if comment and is_player_move:
            ply = board.fullmove_number * 2 - (1 if board.turn else 0)
            annotation = Annotation(
                game_id=game_id,
                move_number=ply,
                content=comment,
                frozen=False
            )
            annotations.append(annotation)

        board.push(next_node.move)
        node = next_node

    return annotations

def _is_player_move(turn: bool, player_color: str) -> bool:
    """
    Check if the current move is by the player.

    Args:
        turn: True for white's turn, False for black's
        player_color: 'WHITE' or 'BLACK'

    Returns:
        True if it's the player's move
    """
    if player_color == 'WHITE':
        return turn  # White's turn
    else:
        return not turn  # Black's turn