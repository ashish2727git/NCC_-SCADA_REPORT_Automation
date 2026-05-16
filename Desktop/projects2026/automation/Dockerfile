FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY Nexus_Control_Tower/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install curl
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Copy app source
COPY Nexus_Control_Tower/ .

# Ensure directory exists
RUN mkdir -p artifacts

EXPOSE 80

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "80"]
