# Use a lightweight Python base image
FROM python:3.12-slim

# Install necessary dependencies
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates

# Install uvicorn and fastapi
RUN pip install --no-cache-dir fastapi uvicorn

# Set the working directory inside the container
WORKDIR /app

# Copy the application code into the container
COPY app.py /app

# Expose the port the app runs on
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

