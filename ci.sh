#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail

pyclean () {
  find . \
    | grep -E '(__pycache__|\.hypothesis|\.perm|\.cache|\.pytest_cache|\.ruff_cache|\.mypy_cache|\.py[cod]$)' \
    | xargs rm -rf \
  || true
}

run_ci () {
  echo '[ci started]'
  set -x

  ruff check .
  echo '[ruff finished without errors]'
  mypy .
  pytest . -p no:cacheprovider

  set +x
  echo '[ci finished]'
}

pyclean
trap pyclean EXIT INT TERM
run_ci
pyclean
trap pyclean EXIT INT TERM
