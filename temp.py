# Use an official lightweight Python image.
FROM python:3.9-slim AS base

# Set environment variables to prevent Python buffering and enable .env support
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies if needed (e.g., for Oracle client libraries)
# RUN apt-get update && apt-get install -y libaio1

# Copy only requirements first for better caching.
COPY requirements.txt .

# Install dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of the application code.
COPY . .

# Expose the port on which the app will run (e.g., 8000)
EXPOSE 8000

# Command to run the app using uvicorn (adjust the module name as needed)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]


version: '3.8'
services:
  fastapi_app:
    build: .
    container_name: fastapi_app
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./:/app  # Mount the current directory if needed for live reload during development
    command: uvicorn main:app --host 0.0.0.0 --port 8000
