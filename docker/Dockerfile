FROM python:3.11-slim AS development_build
ARG SERVICE_ENV
ENV SERVICE_ENV=${SERVICE_ENV} \
# poetry:
  POETRY_VERSION=1.3.1 \
  POETRY_VIRTUALENVS_CREATE=false \
  POETRY_CACHE_DIR='/var/cache/pypoetry' \
# send output to stdout
  PYTHONUNBUFFERED=1

RUN apt-get update \
  && apt-get install --no-install-recommends -y \
    sqlite3 pkg-config \
  && pip install "poetry==${POETRY_VERSION}" && poetry --version

# Copy only requirements, to cache them in docker layer
WORKDIR /code
COPY ./poetry.lock ./pyproject.toml /code/

# We do not want to install dev dependepcies for prod.
RUN echo "$SERVICE_ENV" \
  && poetry install \
    $(if [ "$SERVICE_ENV" = 'production' ]; then echo '--no-dev'; fi) \
    --no-interaction --no-ansi \
  # Cleaning poetry installation's cache for production:
  && if [ "$SERVICE_ENV" = 'production' ]; then rm -rf "$POETRY_CACHE_DIR"; fi

# create db objects if not exists:
RUN if [-d /var/bot_service_data/db.sqlite3]; then \
    echo "DB files exist"; \
  else \
    echo "creating DB objects"; \
    cat ./src/db.sql | sqlite3 /var/bot_service_data/db.sqlite3; \
  fi
  

COPY ./ci.sh /ci.sh
RUN chmod +x '/ci.sh'

FROM development_build as production_build

COPY . /code