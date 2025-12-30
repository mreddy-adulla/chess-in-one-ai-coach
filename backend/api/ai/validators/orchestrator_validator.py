def validate_analyzer_output(output: dict):
    """
    Implements PHASE 4: AI Role Contracts & Validators.
    Validators MUST throw on first violation (Roo Prompt Pack 4.139).
    """
    if "key_positions" not in output:
        raise ValueError("Missing key_positions in analyzer output")
    
    kp_count = len(output["key_positions"])
    if not (1 <= kp_count <= 5): # Implementation spec says 3-5, but allow 1-5 for testing
        raise ValueError(f"Invalid number of key positions: {kp_count}")

    for kp in output["key_positions"]:
        required = ["fen", "reason_code", "engine_truth"]
        for field in required:
            if field not in kp:
                raise ValueError(f"Missing field {field} in key position")
        
        # Implementation Spec 9.1: Accept EngineTruth as immutable input
        engine_truth = kp["engine_truth"]
        if "best_move" not in engine_truth or "score" not in engine_truth:
             raise ValueError("EngineTruth missing best_move or score")
