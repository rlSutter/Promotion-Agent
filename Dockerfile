FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY agent.py .
COPY server.py .
COPY dashboard.html .
COPY .env.example .

# Create data directory for SQLite
RUN mkdir -p /app/data

# Expose port for dashboard
EXPOSE 5000

# Health check
HEALTHCHECK --interval=60s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import sqlite3; sqlite3.connect('promotion_agent.db').cursor().execute('SELECT 1')"

# Use supervisor to run both agent and server
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Install supervisor
RUN apt-get update && apt-get install -y supervisor && rm -rf /var/lib/apt/lists/*

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
