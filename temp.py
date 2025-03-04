import streamlit as st
from io import BytesIO
from pptx import Presentation

# Function to create a PowerPoint file in memory
def create_pptx():
    prs = Presentation()
    slide_layout = prs.slide_layouts[0]  # Title slide layout
    slide = prs.slides.add_slide(slide_layout)
    title = slide.shapes.title
    subtitle = slide.placeholders[1]
    title.text = "Hello, Streamlit!"
    subtitle.text = "This is a sample PowerPoint slide."

    # Save to a BytesIO buffer
    pptx_bytes = BytesIO()
    prs.save(pptx_bytes)
    pptx_bytes.seek(0)
    return pptx_bytes

# Generate PowerPoint file
pptx_file = create_pptx()

# Download button
st.download_button(
    label="Download PowerPoint",
    data=pptx_file,
    file_name="sample_presentation.pptx",
    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
)
