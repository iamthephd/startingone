def add_textbox_with_styled_text(slide, left, top, width, height, text, set_border=True):
    textbox = slide.shapes.add_textbox(left, top, width, height)
    
    if set_border:
        # Setting a border for the textbox
        textbox.line.color.rgb = RGBColor(0, 0, 0)  # black
        textbox.line.width = Pt(1)
    
    tf = textbox.text_frame
    tf.clear()
    tf.word_wrap = True
    
    # Start with a default font size
    default_font_size = Pt(12)
    min_font_size = Pt(6)  # Minimum readable font size
    
    def fit_text_to_box():
        # Reset the text frame
        tf.clear()
        current_font_size = default_font_size
        
        while current_font_size >= min_font_size:
            # Reset the text frame for each iteration
            tf.clear()
            
            for line in text.split('\n'):
                p = tf.add_paragraph()
                p.line_spacing = 1.0  # Ensure consistent line spacing
                
                if ':' in line:
                    parts = line.split(':', 1)
                    
                    # Bold part
                    run_bold = p.add_run()
                    run_bold.text = parts[0] + ": "
                    run_bold.font.bold = True
                    run_bold.font.underline = True
                    run_bold.font.name = 'Calibri'
                    run_bold.font.size = current_font_size
                    
                    # Normal part
                    run_normal = p.add_run()
                    run_normal.text = parts[1]
                    run_normal.font.name = 'Calibri'
                    run_normal.font.size = current_font_size
                else:
                    p.text = line
                    p.font.name = 'Calibri'
                    p.font.size = current_font_size
            
            try:
                # Explicitly check if text fits
                # This is a sanity check since the previous method might not work consistently
                if tf.text_frame.overflowing:
                    current_font_size -= Pt(1)
                    continue
                
                return  # Success, text fits
            except Exception:
                # Reduce font size and try again
                current_font_size -= Pt(1)
        
        # If we can't fit text, use the minimum font size
        if current_font_size < min_font_size:
            current_font_size = min_font_size
            # Recreate the text frame with the minimum font size
            tf.clear()
            for line in text.split('\n'):
                p = tf.add_paragraph()
                p.text = line
                p.font.size = current_font_size
    
    # Attempt to fit text
    fit_text_to_box()
    
    return textbox