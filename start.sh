#!/bin/bash
PORT=${PORT:-8000}
WEBHOOK_PORT=${WEBHOOK_PORT:-8001}

# Install Chrome for Selenium (only if not already installed)
if ! command -v google-chrome >/dev/null 2>&1; then
    echo "Installing Chrome for Selenium..."
    chmod +x chrome-install.sh
    ./chrome-install.sh
fi

# Start webhook service in background
python webhook_service.py &
WEBHOOK_PID=$!

# Give webhook service time to start
sleep 5

# Start main service
python -m uvicorn main:app --host 0.0.0.0 --port $PORT &

# Wait for both services
wait
