FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY agent-service/requirement.txt .

RUN pip install --no-cache-dir -r requirement.txt

# Copy the whole agents package, not just orchestrator subdirectory
COPY agent-service/agents/ ./agents/

EXPOSE 8000

CMD ["uvicorn", "agents.orchestrator.services.orchestrator_service:app", "--host", "0.0.0.0", "--port", "8000"]