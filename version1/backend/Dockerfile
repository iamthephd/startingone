FROM python:3.9-slim

WORKDIR /app

COPY backend /app/backend
COPY config /app/config
COPY data /app/data

RUN pip install --no-cache-dir flask flask-cors pandas pyyaml cx_Oracle sqlalchemy

EXPOSE 5000

ENTRYPOINT ["python", "backend/server.py"]