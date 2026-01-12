FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

ENV UV_PROJECT_ENVIRONMENT="/venv"

RUN uv venv /venv

ENV PATH="/venv/bin:$PATH"

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

COPY . .

RUN uv sync --frozen

CMD ["bash", "-c", "alembic upgrade head && fastapi run app/main.py --port 8000 --host 0.0.0.0"]