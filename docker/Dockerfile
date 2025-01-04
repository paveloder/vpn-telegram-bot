FROM python:3.11-slim AS development_build
ARG SERVICE_ENV
ENV SERVICE_ENV=${SERVICE_ENV} \
# poetry:
  POETRY_VERSION=1.3.1 \
  POETRY_VIRTUALENVS_CREATE=false \
  POETRY_CACHE_DIR='/var/cache/pypoetry' \
  PYTHONUNBUFFERED=1 \
# send output to stdout
  UV_PROJECT_ENVIRONMENT="/usr/local/"


RUN apt-get update \
  && apt-get install --no-install-recommends -y \
    sqlite3 pkg-config \
    curl ca-certificates

# Download the latest installer
ADD https://astral.sh/uv/install.sh /uv-installer.sh

# Run the installer then remove it
RUN sh /uv-installer.sh && rm /uv-installer.sh

# Ensure the installed binary is on the `PATH`
ENV PATH="/root/.local/bin/:$PATH"

# Copy only requirements, to cache them in docker layer
WORKDIR /code
COPY ./uv.lock ./pyproject.toml /code/

# We do not want to install dev dependepcies for prod.
RUN echo "$SERVICE_ENV" \
  && uv sync --frozen --no-cache \
  $(if [ "$SERVICE_ENV" = 'production' ]; then echo '--no-dev'; fi)

# create db objects if not exists:
RUN if [ -f /var/bot_service_data/db.sqlite3 ]; then \
    echo "DB files exist"; \
  else \
    echo "creating DB objects"; \
    cat ./src/db.sql | sqlite3 /var/bot_service_data/db.sqlite3; \
  fi
  

COPY ./ci.sh /ci.sh
RUN chmod +x '/ci.sh'

FROM development_build as production_build

COPY . /code