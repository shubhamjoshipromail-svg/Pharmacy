#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
EVIDENCE_DIR=$(cd "$SCRIPT_DIR/.." && pwd)
PROJECT_ROOT=$(cd "$EVIDENCE_DIR/../../../../" && pwd)
RAW_DIR="$EVIDENCE_DIR/raw_results"
LOG_DIR="$EVIDENCE_DIR/logs"
PG_BIN=${PG_BIN:?Set PG_BIN to the PostgreSQL bin directory.}
PYTHON_BIN=${PYTHON_BIN:?Set PYTHON_BIN to the evidence virtual environment Python.}
TEMP_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/rxcheck-traceability.XXXXXX")
DATA_DIR="$TEMP_ROOT/data"
PG_LOG="$TEMP_ROOT/postgres.log"
PORT=$(
  "$PYTHON_BIN" -c \
    'import socket; sock=socket.socket(); sock.bind(("127.0.0.1", 0)); print(sock.getsockname()[1]); sock.close()'
)
DB_USER=rxcheck_traceability
DB_NAME=rxcheck_traceability

mkdir -p "$RAW_DIR" "$LOG_DIR"
rm -f "$RAW_DIR/traceability_results.json" "$RAW_DIR/environment_lock.txt"
rm -f "$LOG_DIR/execution.log" "$LOG_DIR/postgres.log"

cleanup() {
  set +e
  if [[ -f "$DATA_DIR/postmaster.pid" ]]; then
    "$PG_BIN/pg_ctl" -D "$DATA_DIR" stop -m fast >/dev/null 2>&1
  fi
  if [[ -f "$PG_LOG" ]]; then
    cp "$PG_LOG" "$LOG_DIR/postgres.log"
  fi
  rm -rf "$TEMP_ROOT"
}
trap cleanup EXIT

"$PG_BIN/initdb" \
  -D "$DATA_DIR" \
  --username="$DB_USER" \
  --auth-local=trust \
  --auth-host=trust \
  --encoding=UTF8 \
  --no-locale >/dev/null
"$PG_BIN/pg_ctl" \
  -D "$DATA_DIR" \
  -l "$PG_LOG" \
  -o "-h 127.0.0.1 -p $PORT" \
  start >/dev/null
"$PG_BIN/pg_isready" -h 127.0.0.1 -p "$PORT" -U "$DB_USER" -d postgres -t 10 >/dev/null
"$PG_BIN/createdb" -h 127.0.0.1 -p "$PORT" -U "$DB_USER" "$DB_NAME"

cd "$PROJECT_ROOT"
"$PYTHON_BIN" -m pip freeze --all > "$RAW_DIR/environment_lock.txt"
set +e
DATABASE_URL="postgresql+psycopg2://${DB_USER}@127.0.0.1:${PORT}/${DB_NAME}" \
  "$PYTHON_BIN" "$SCRIPT_DIR/run_traceability_audit.py" \
    --output "$RAW_DIR/traceability_results.json" \
    2>&1 | tee "$LOG_DIR/execution.log"
STATUS=${PIPESTATUS[0]}
set -e
exit "$STATUS"
