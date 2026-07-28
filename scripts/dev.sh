#!/usr/bin/env bash
set -euo pipefail

# ROSTR Agent — Dev Environment Starter
DIR="$(cd "$(dirname "$0")" && pwd)"

echo "═══ ROSTR Agent — Starting Dev Environment ═══"
echo ""

# ── Backend ────────────────────────────────────────────
echo "► Starting backend (port 8080)..."
cd "$DIR"
PYTHONPATH=. .venv/bin/python backend/backend.py &
BACKEND_PID=$!
echo "  PID: $BACKEND_PID"

# Wait for health
sleep 2
if curl -sf http://localhost:8080/health > /dev/null 2>&1; then
  echo "  ✓ Backend healthy"
else
  echo "  ✗ Backend failed to start"
fi

# ── Frontend ───────────────────────────────────────────
echo "► Starting frontend (port 3000)..."
cd "$DIR/frontend"
npm run dev &
FRONTEND_PID=$!
echo "  PID: $FRONTEND_PID"

echo ""
echo "═══ ROSTR Agent is running ═══"
echo "  Backend:  http://localhost:8080"
echo "  API Docs: http://localhost:8080/docs"
echo "  Frontend: http://localhost:3000"
echo "  Health:   http://localhost:8080/health"
echo ""
echo "Press Ctrl+C to stop both."

# Trap for clean shutdown
trap "echo 'Shutting down...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM
wait
