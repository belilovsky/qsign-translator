FROM python:3.11-slim AS builder
WORKDIR /build
COPY pyproject.toml README.md /build/
RUN pip install --user --no-cache-dir --upgrade pip

FROM python:3.11-slim AS runtime
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
COPY --from=builder /root/.local /root/.local
COPY pyproject.toml README.md /app/
COPY src /app/src
COPY data /app/data
COPY scripts /app/scripts
COPY public /app/public
RUN pip install --no-cache-dir -e ".[api,db]"
RUN groupadd -r appuser && useradd -r -g appuser appuser
USER appuser
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1
CMD ["uvicorn", "qsign_translator.main:app", "--host", "0.0.0.0", "--port", "8080"]
