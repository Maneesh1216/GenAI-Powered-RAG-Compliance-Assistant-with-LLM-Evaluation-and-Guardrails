FROM python:3.11-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONPATH=/app/src

COPY requirements.txt requirements-full.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
 && pip install --no-cache-dir fastapi "uvicorn[standard]" streamlit pydantic

COPY src/ ./src/
COPY app/ ./app/
COPY scripts/ ./scripts/
COPY eval/ ./eval/
COPY data/ ./data/

RUN python scripts/build_index.py

EXPOSE 8000 8501
CMD ["uvicorn", "compliance_assistant.api:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000"]
