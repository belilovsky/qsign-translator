FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md /app/
COPY src /app/src
COPY data /app/data
COPY scripts /app/scripts
COPY public /app/public

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -e ".[api,db]"

EXPOSE 8080

CMD ["python", "-m", "uvicorn", "qsign_translator.api:app", "--host", "0.0.0.0", "--port", "8080"]
