def get_commentary(top_contributors):
    """Generate commentary based on top contributors"""
    # This would be implemented elsewhere
    logger.debug(f"Generating commentary based on {len(top_contributors)} contributors")
    
    # Make sure our cell references are explicitly mentioned in a consistent format
    # for the hover highlighting to work properly
    return (
        "Based on the analysis, we can observe the following trends:\n\n"
        "1. Cell Category A, Q1 shows lower than expected performance due to Factor 1 (40%), "
        "Factor 2 (35%), and Factor 3 (25%).\n\n"
        "2. Cell Category C, Q3 shows significant growth primarily driven by Factor 5 (80%), "
        "followed by Factor 4 (70%) and Factor 6 (60%).\n\n"
        "3. Cell Category E, Q4 demonstrates strong results with Factor 8 (90%) being the main contributor, "
        "supported by Factor 7 and Factor 9 (both 55%)."
    )