FROM python:3.12-slim-bookworm

# Update OS packages and remove cache to reduce image size
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy & install dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

# Bundle CSS for speed image build time
RUN python css_bundler.py

RUN chmod +x entrypoint.sh

RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

# Actual port is controlled by FLASK_PORT env var at runtime
EXPOSE 5000

CMD ["./entrypoint.sh"]
