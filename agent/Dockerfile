FROM --platform=linux/arm64 ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-cache --no-dev

COPY src/ ./src/

EXPOSE 8080

CMD ["uv", "run", "python", "-m", "confee_agent.main"]
