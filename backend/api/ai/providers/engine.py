import httpx
import logging

logger = logging.getLogger(__name__)

class ChessEngineProvider:
    """
    Provides chess engine analysis using external APIs (Stockfish Online / Chess-API.com).
    Strictly follows Implementation Spec Section 9.
    """
    def __init__(self):
        self.api_url = "https://chess-api.com/v1/look-up"

    async def analyze_position(self, fen: str):
        """
        Fetches evaluation and best move for a given FEN.
        Uses max depth and provides sufficient timeout.
        """
        try:
            # Use max depth and give enough time as per user feedback
            async with httpx.AsyncClient(timeout=60.0) as client:
                payload = {
                    "fen": fen,
                    "depth": 25, # Maximum reasonable depth for online API
                    "max_time": 20 # 20 seconds for deep analysis
                }
                response = await client.post(self.api_url, json=payload)
                response.raise_for_status()
                data = response.json()
                
                return {
                    "score": data.get("eval", 0),
                    "best_move": data.get("move", ""),
                    "threats": data.get("threats", []),
                    "depth": data.get("depth", 25)
                }
        except Exception as e:
            logger.error(f"Engine analysis failed for FEN {fen}: {e}")
            raise
