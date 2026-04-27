# Use official Python lightweight image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy and install service requirements
# NOTE: This Dockerfile expects the build context to be the project root
COPY services/prediction-service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared modules (requires project root build context)
COPY shared/ /shared/
ENV PYTHONPATH="${PYTHONPATH}:/shared"

# Copy service application code
COPY services/prediction-service/ /app/

# Expose the API port
EXPOSE 8003

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]
