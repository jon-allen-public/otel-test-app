# Use an official Python image
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Copy the application code
COPY . /app/

# Set PYTHONPATH to include the src directory
ENV PYTHONPATH=/app/src

# Install dependencies, then install OTel auto-instrumentation packages matching
# what's actually installed (Flask, Celery, Redis, ...)
RUN pip install --no-cache-dir -r requirements.txt && opentelemetry-bootstrap -a install

# Expose the port the app runs on
EXPOSE 8080

# Command to run the Flask app
CMD ["opentelemetry-instrument", "gunicorn", "-c", "src/gunicorn_config.py", "src.main:app"]