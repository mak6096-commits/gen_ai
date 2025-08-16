# Use Python 3.10 slim image for better compatibility
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY minimal_app.py .

# Expose port (Cloud Run will set PORT env var)
EXPOSE 8007

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8007

# Run the application
CMD ["python", "minimal_app.py"]
