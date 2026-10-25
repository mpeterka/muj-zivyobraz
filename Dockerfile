FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip uninstall -y setuptools wheel pip

# Copy application code
COPY . .

# Environment variables
ENV PYTHONUNBUFFERED=1
EXPOSE 8000

# Run the application
CMD ["python", "main.py"]
