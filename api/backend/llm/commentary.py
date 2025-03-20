def get_commentary(top_contributors, file_name):
    """
    Generate commentary based on top contributors
    """
    try:
        # Example implementation
        commentary = "Analysis shows significant changes in performance metrics:\n"
        for contrib in top_contributors:
            commentary += f"- {contrib['attribute']}: {contrib['contribution']}%\n"
        return commentary
    except Exception as e:
        print(f"Error generating commentary: {str(e)}")
        return "Unable to generate commentary"

def modify_commentary(user_comment, current_commentary, selected_cells, file_name, contributing_columns, top_n):
    """
    Modify existing commentary based on user input
    """
    try:
        # Example implementation
        return f"{current_commentary}\n\nUser insights:\n{user_comment}"
    except Exception as e:
        print(f"Error modifying commentary: {str(e)}")
        return current_commentary
