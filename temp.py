def parse_text(text):
    """
    Parse the text into a dictionary where each key is a title
    and each value is a list of points.
    """
    sections = {}
    # Split sections based on two consecutive newlines.
    for section in text.strip().split("\n\n"):
        lines = section.strip().splitlines()
        if not lines:
            continue
        title = lines[0].strip()  # The first line is the title.
        points = [line.strip() for line in lines[1:]]  # The rest are points.
        sections[title] = points
    return sections

def merge_texts(original_text, new_text):
    """
    Merge points from new_text into original_text based on matching titles.
    """
    # Parse both texts.
    orig_sections = parse_text(original_text)
    new_sections = parse_text(new_text)
    
    # For each title in new_sections, merge or add to original sections.
    for title, new_points in new_sections.items():
        if title in orig_sections:
            orig_sections[title].extend(new_points)
        else:
            orig_sections[title] = new_points

    # Reconstruct the merged text.
    merged_sections = []
    for title, points in orig_sections.items():
        section = title + "\n" + "\n".join(points)
        merged_sections.append(section)
    
    return "\n\n".join(merged_sections)


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

Quarter on Quarter Profit
Introduced efficiency measures
"""

merged_text = merge_texts(original_text, new_text)
print(merged_text)
