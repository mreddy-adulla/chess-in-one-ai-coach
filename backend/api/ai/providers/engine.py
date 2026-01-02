import httpx
import logging

logger = logging.getLogger(__name__)

class ChessEngineProvider:
    """
    Provides chess engine analysis using external APIs (Stockfish Online / Chess-API.com).
    Strictly follows Implementation Spec Section 9.
    """
    def __init__(self):
        # Priority order: stockfish.online (most reliable), then chess-api.com v2
        # We'll determine which chess-api.com version works and use only that one
        self.stockfish_online_url = "https://stockfish.online/api/s/v2.php"
        self.chess_api_v2_url = "https://chess-api.com/v2/look-up"
        self.chess_api_v1_url = "https://chess-api.com/v1/look-up"
        self.chess_api_url = None  # Will be set to working version on first successful call

    async def analyze_position(self, fen: str, fallback_on_error: bool = True):
        """
        Fetches evaluation and best move for a given FEN.
        Uses max depth and provides sufficient timeout.
        
        Args:
            fen: Position FEN string
            fallback_on_error: If True, returns default values on error instead of raising
        
        Returns:
            Dict with score, best_move, threats, depth
        """
        last_error = None
        
        # Priority 1: Try stockfish.online first (most reliable)
        # Add retry logic for transient failures
        max_retries = 2
        for attempt in range(max_retries):
            try:
                import asyncio
                # stockfish.online uses GET with query parameters
                # Max depth is 15 according to documentation
                params = {
                    "fen": fen,
                    "depth": 15  # Maximum depth for stockfish.online
                }
                
                logger.info(f"[STOCKFISH] Attempt {attempt + 1}/{max_retries} - Calling API: {self.stockfish_online_url}")
                logger.info(f"[STOCKFISH] Request method: GET")
                logger.info(f"[STOCKFISH] Request parameters: fen={fen[:50]}..., depth=15")
                logger.info(f"[STOCKFISH] Full URL: {self.stockfish_online_url}?fen={fen}&depth=15")
                
                async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0)) as client:
                    # Add asyncio timeout as additional protection
                    response = await asyncio.wait_for(
                        client.get(self.stockfish_online_url, params=params),
                        timeout=30.0
                    )
                    
                    logger.info(f"[STOCKFISH] Response status: {response.status_code} {response.reason_phrase}")
                    logger.info(f"[STOCKFISH] Response headers: {dict(response.headers)}")
                    
                    response.raise_for_status()
                    data = response.json()
                    
                    logger.info(f"[STOCKFISH] Response JSON keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                    logger.debug(f"[STOCKFISH] Full response: {data}")
                    
                    # Parse stockfish.online response format
                    # Actual response format: {'success': bool, 'evaluation': float, 'mate': int or None, 'bestmove': str, 'continuation': str}
                    best_move = ""
                    eval_score = 0.0
                    depth = 15
                    
                    # Extract bestmove - can be string like "e2e4" or "bestmove e2e4"
                    if "bestmove" in data:
                        bestmove_value = data["bestmove"]
                        if isinstance(bestmove_value, str):
                            # Handle both "e2e4" and "bestmove e2e4" formats
                            move_parts = bestmove_value.split()
                            if len(move_parts) > 1:
                                best_move = move_parts[1]  # e.g., "e2e4" from "bestmove e2e4"
                            else:
                                best_move = move_parts[0] if move_parts else ""
                        else:
                            best_move = str(bestmove_value)
                    
                    # Extract evaluation - direct field in response
                    if "evaluation" in data:
                        eval_value = data["evaluation"]
                        if isinstance(eval_value, (int, float)):
                            # Evaluation is already in pawns (not centipawns)
                            eval_score = float(eval_value)
                        elif isinstance(eval_value, str):
                            try:
                                eval_score = float(eval_value)
                            except ValueError:
                                logger.warning(f"[STOCKFISH] Could not parse evaluation: {eval_value}")
                                eval_score = 0.0
                    
                    # Extract depth from continuation or use default
                    if "continuation" in data and isinstance(data["continuation"], str):
                        # Continuation might contain depth info, but we'll use default for now
                        pass
                    
                    logger.info(f"[STOCKFISH] Parsed: best_move={best_move}, eval_score={eval_score}, depth={depth}")
                    
                    logger.info(f"Engine analysis successful from stockfish.online")
                    return {
                        "score": eval_score,
                        "best_move": best_move,
                        "threats": [],  # stockfish.online doesn't provide threats in standard format
                        "depth": depth
                    }
            except httpx.HTTPStatusError as e:
                # HTTP error responses (4xx, 5xx)
                error_type = type(e).__name__
                logger.error(f"[STOCKFISH] HTTP error (attempt {attempt + 1}/{max_retries}): {error_type}")
                logger.error(f"[STOCKFISH] Status code: {e.response.status_code}")
                logger.error(f"[STOCKFISH] Response headers: {dict(e.response.headers)}")
                try:
                    error_body = e.response.text
                    logger.error(f"[STOCKFISH] Response body: {error_body[:500]}")  # First 500 chars
                except Exception:
                    logger.error(f"[STOCKFISH] Could not read response body")
                logger.error(f"[STOCKFISH] Full error: {e}")
                last_error = e
                break  # Don't retry HTTP errors
            except (httpx.ConnectError, httpx.ReadError, httpx.RemoteProtocolError) as e:
                # Network/server errors - retry if attempts remaining
                error_type = type(e).__name__
                logger.warning(f"[STOCKFISH] Connection error (attempt {attempt + 1}/{max_retries}): {error_type}")
                logger.warning(f"[STOCKFISH] Error details: {str(e)}")
                logger.warning(f"[STOCKFISH] Error args: {e.args if hasattr(e, 'args') else 'N/A'}")
                if hasattr(e, 'request'):
                    logger.warning(f"[STOCKFISH] Failed request URL: {e.request.url if hasattr(e.request, 'url') else 'N/A'}")
                if attempt < max_retries - 1:
                    wait_time = 1.0 * (attempt + 1)
                    logger.info(f"[STOCKFISH] Retrying after {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error(f"[STOCKFISH] All retries exhausted. Last error: {error_type}: {e}")
                    last_error = e
                    break
            except (asyncio.TimeoutError, httpx.TimeoutException) as e:
                error_type = type(e).__name__
                logger.warning(f"[STOCKFISH] Timeout error (attempt {attempt + 1}/{max_retries}): {error_type}")
                logger.warning(f"[STOCKFISH] Timeout details: {str(e)}")
                if attempt < max_retries - 1:
                    wait_time = 1.0 * (attempt + 1)
                    logger.info(f"[STOCKFISH] Retrying after {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error(f"[STOCKFISH] All retries exhausted. Last timeout error: {error_type}: {e}")
                    last_error = e
                    break
            except Exception as e:
                # Other errors - log and don't retry
                error_type = type(e).__name__
                logger.error(f"[STOCKFISH] Unexpected error (attempt {attempt + 1}/{max_retries}): {error_type}")
                logger.error(f"[STOCKFISH] Error message: {str(e)}")
                logger.error(f"[STOCKFISH] Error type: {type(e)}")
                logger.error(f"[STOCKFISH] Error args: {e.args if hasattr(e, 'args') else 'N/A'}")
                import traceback
                logger.error(f"[STOCKFISH] Traceback: {traceback.format_exc()}")
                last_error = e
                break
        
        # Priority 2: Try chess-api.com (use cached working version or determine which works)
        chess_api_url = self.chess_api_url
        if not chess_api_url:
            # Determine which version works by trying v2 first with timeout protection
            import asyncio
            try:
                logger.debug(f"Testing chess-api.com v2 for FEN {fen}")
                async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=5.0)) as client:
                    payload = {"fen": fen, "depth": 18, "max_time": 5}
                    # Add asyncio timeout as additional protection
                    response = await asyncio.wait_for(
                        client.post(self.chess_api_v2_url, json=payload),
                        timeout=10.0
                    )
                    response.raise_for_status()
                    chess_api_url = self.chess_api_v2_url
                    logger.info("chess-api.com v2 is working, will use it going forward")
            except (asyncio.TimeoutError, httpx.TimeoutException) as e:
                logger.warning(f"chess-api.com v2 timed out: {e}, trying v1")
                chess_api_url = None
            except Exception as e:
                logger.warning(f"chess-api.com v2 failed: {e}, trying v1")
                chess_api_url = None
            
            if not chess_api_url:
                try:
                    logger.debug(f"Testing chess-api.com v1 for FEN {fen}")
                    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=5.0)) as client:
                        payload = {"fen": fen, "depth": 18, "max_time": 5}
                        # Add asyncio timeout as additional protection
                        response = await asyncio.wait_for(
                            client.post(self.chess_api_v1_url, json=payload),
                            timeout=10.0
                        )
                        response.raise_for_status()
                        chess_api_url = self.chess_api_v1_url
                        logger.info("chess-api.com v1 is working, will use it going forward")
                except (asyncio.TimeoutError, httpx.TimeoutException) as e:
                    logger.warning(f"chess-api.com v1 timed out: {e}")
                    chess_api_url = None
                except Exception as e2:
                    logger.warning(f"chess-api.com v1 also failed: {e2}")
                    chess_api_url = None
        
        # Try the working chess-api.com version if we have one
        if chess_api_url:
            try:
                logger.debug(f"Trying chess-api.com: {chess_api_url}")
                import asyncio
                async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0)) as client:
                    payload = {
                        "fen": fen,
                        "depth": 18, # Maximum depth supported by chess-api.com
                        "max_time": 15 # Allow sufficient time for deep analysis
                    }
                    # Add asyncio timeout as additional protection
                    response = await asyncio.wait_for(
                        client.post(chess_api_url, json=payload),
                        timeout=30.0
                    )
                    response.raise_for_status()
                    data = response.json()
                    
                    logger.info(f"[CHESS_API] Response status: {response.status_code} {response.reason_phrase}")
                    logger.info(f"[CHESS_API] Response JSON keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                    logger.debug(f"[CHESS_API] Full response: {data}")
                    
                    # Cache the working URL for future calls
                    self.chess_api_url = chess_api_url
                    
                    # Parse response - need to verify actual format
                    # Expected fields: eval (or evaluation), move (or best_move), threats, depth
                    eval_score = data.get("eval") or data.get("evaluation", 0)
                    best_move = data.get("move") or data.get("best_move", "")
                    threats = data.get("threats", [])
                    actual_depth = data.get("depth", 18)
                    
                    logger.info(f"[CHESS_API] Parsed: best_move={best_move}, eval_score={eval_score}, depth={actual_depth}, threats_count={len(threats)}")
                    
                    logger.info(f"Engine analysis successful from {chess_api_url}")
                    return {
                        "score": eval_score,
                        "best_move": best_move,
                        "threats": threats,
                        "depth": actual_depth
                    }
            except (asyncio.TimeoutError, httpx.TimeoutException) as e:
                logger.warning(f"chess-api.com analysis timed out: {e}")
                # Clear cached URL if it's no longer working
                if self.chess_api_url == chess_api_url:
                    self.chess_api_url = None
                last_error = e
            except Exception as e:
                logger.warning(f"chess-api.com analysis failed: {e}")
                # Clear cached URL if it's no longer working
                if self.chess_api_url == chess_api_url:
                    self.chess_api_url = None
                last_error = e
        
        # All API URLs failed
        logger.warning(f"All engine API endpoints failed for FEN {fen}. Last error: {last_error}")
        if fallback_on_error:
            # Return default values to allow analysis to continue
            logger.info(f"Using fallback values for position {fen}")
            return {
                "score": 0.0,  # Neutral evaluation
                "best_move": "",  # Unknown
                "threats": [],  # No threats detected
                "depth": 0
            }
        else:
            raise last_error or Exception("All engine API endpoints failed")
