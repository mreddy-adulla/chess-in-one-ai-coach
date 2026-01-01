"""
Custom exception classes for the application.
"""

class ChessCoachError(Exception):
    """Base exception for Chess-in-One AI Coach."""
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.status_code = status_code

class GameNotFoundError(ChessCoachError):
    """Raised when a game is not found."""
    def __init__(self, game_id: int):
        super().__init__(f"Game with id {game_id} not found", 404)

class InvalidGameStateError(ChessCoachError):
    """Raised when game state transition is invalid."""
    def __init__(self, current_state: str, attempted_action: str):
        super().__init__(
            f"Invalid state transition from {current_state} for action: {attempted_action}",
            409
        )

class ParentApprovalRequiredError(ChessCoachError):
    """Raised when parent approval is required but not provided."""
    def __init__(self, reason: str):
        super().__init__(f"Parent approval required: {reason}", 403)

class LockAcquisitionError(ChessCoachError):
    """Raised when Redis lock cannot be acquired."""
    def __init__(self, lock_key: str):
        super().__init__(f"Could not acquire lock for {lock_key}", 503)

class ValidationError(ChessCoachError):
    """Raised when input validation fails."""
    def __init__(self, field: str, message: str):
        super().__init__(f"Validation error for {field}: {message}", 400)