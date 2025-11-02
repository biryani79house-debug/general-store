#!/bin/bash
PORT=${PORT:-8000}

# Start main service
python -m uvicorn main:app --host 0.0.0.0 --port $PORT &

# Wait for service
wait
