FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install -r backend/requirements.txt

COPY alembic.ini ./alembic.ini
COPY backend/alembic ./backend/alembic
COPY backend/app ./backend/app
COPY backend/scripts ./backend/scripts

RUN addgroup --system app && \
    adduser --system --ingroup app app && \
    mkdir -p /app/data/documents && \
    chown -R app:app /app/data

USER app

EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
