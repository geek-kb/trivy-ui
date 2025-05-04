#!/bin/sh
set -e

export CLUSTER_HOST="${KUBERNETES_SERVICE_HOST}"

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
