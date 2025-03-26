from fastapi.responses import StreamingResponse
from io import BytesIO

# Assume ppt_bytes is a BytesIO object containing your PPT data:
ppt_bytes = BytesIO()
# ... your code that writes the PPT content into ppt_bytes ...
ppt_bytes.seek(0)

headers = {
    "Content-Disposition": "attachment; filename=presentation.ppt"
}

return StreamingResponse(
    ppt_bytes,
    media_type="application/vnd.ms-powerpoint",
    headers=headers
)
