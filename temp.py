def parse_text(text):
    """
    Parse the input text into a dictionary of titles and their points.
    
    Args:
        text (str): Input text to parse
    
    Returns:
        dict: A dictionary where keys are titles and values are lists of points
    """
    titles_dict = {}
    lines = text.split('\n')
    current_title = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check if line is a title (contains "Year on Year" or "Quarter on Quarter")
        if "Year on Year" in line or "Quarter on Quarter" in line:
            current_title = line
            titles_dict[current_title] = []
        elif current_title is not None:
            titles_dict[current_title].append("\n"+line)
    
    return titles_dict

def merge_texts(original_text, new_text):
    """
    Merge two texts with flexible title matching.
    
    Args:
        original_text (str): The original text
        new_text (str): The new text to merge
    
    Returns:
        str: Merged text
    """
    # Parse both texts
    original_dict = parse_text(original_text)
    new_dict = parse_text(new_text)
    
    # Merge the dictionaries
    merged_dict = original_dict.copy()
    for new_title, new_points in new_dict.items():
        # Check for matching title
        matched = False
        for orig_title in merged_dict.keys():
            # Match if either "Year on Year" or "Quarter on Quarter" is in both titles
            if ("Year on Year" in new_title and "Year on Year" in orig_title) or \
               ("Quarter on Quarter" in new_title and "Quarter on Quarter" in orig_title):
                merged_dict[orig_title].extend(new_points)
                matched = True
                break
        
        # If no match found, add as a new title
        if not matched:
            merged_dict[new_title] = new_points
    
    # Reconstruct the text
    output_lines = []
    for title, points in merged_dict.items():
        output_lines.append(title)
        output_lines.extend(points)
        output_lines.append('\n')  # Add an extra newline between titles
    
    # Remove the last extra newline and join
    return '\n'.join(output_lines).rstrip()



# Example usage
original_text = """
Year on Year Sales Growth

Sales increased by 10%

Highest growth in Q4


Quarter on Quarter Profit

Profit margins improved

Significant cost reductions
"""

new_text = """
Year on Year Sales Growth

Additional market expansion

New product line launch
"""

merged_text = merge_texts(original_text, new_text)
print(merged_text)
