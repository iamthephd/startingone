FROM python:3.9-slim

WORKDIR /app

COPY frontend /app/frontend
COPY api /app/api
COPY config /app/config

RUN pip install --no-cache-dir streamlit pandas requests

ENV API_ENDPOINT=http://backend:5000

EXPOSE 8501

ENTRYPOINT ["streamlit", "run", "frontend/app.py", "--server.port=8501", "--server.address=0.0.0.0"]