import re

def parse_sections(text):
    """
    Splits the text into sections.
    A section is defined as a title line (which must contain either
    'Year on Year' or 'Quarter on Quarter') followed by one or more points.
    It ignores extra blank lines.
    Returns a list of tuples: (title, [point1, point2, ...])
    """
    # Split on one or more blank lines
    segments = [seg.strip() for seg in re.split(r'\n\s*\n', text.strip()) if seg.strip()]
    
    sections = []
    current_title = None
    current_points = []
    
    for seg in segments:
        # If the segment contains one of the key phrases, treat it as a title.
        if "Year on Year" in seg or "Quarter on Quarter" in seg:
            # If a previous section exists, add it to our list.
            if current_title is not None:
                sections.append((current_title, current_points))
            current_title = seg
            current_points = []
        else:
            # Otherwise, it's a point.
            current_points.append(seg)
    
    if current_title is not None:
        sections.append((current_title, current_points))
    return sections

def merge_texts(original_text, new_text):
    """
    Merges the new_text into original_text by matching sections with the same title.
    The order of sections is preserved based on the original text, with any additional
    (non-matching) sections from the new text appended at the end.
    """
    orig_sections = parse_sections(original_text)
    new_sections = parse_sections(new_text)
    
    # Build a dictionary from original sections: title -> points list (copying points)
    merged = {title: points[:] for title, points in orig_sections}
    order = [title for title, _ in orig_sections]
    
    # For each section from new_text, merge points if title exists; otherwise, add as new section.
    for title, points in new_sections:
        if title in merged:
            merged[title].extend(points)
        else:
            merged[title] = points
            order.append(title)
    
    # Reconstruct the merged text.
    # Each section: title on its own, then a blank line, then points separated by a newline.
    merged_sections = []
    for title in order:
        section_text = title
        if merged[title]:
            section_text += "\n\n" + "\n".join(merged[title])
        merged_sections.append(section_text)
    
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
"""

merged_text = merge_texts(original_text, new_text)
print(merged_text)
