FROM python:3.11-alpine@sha256:5fb4bc53dd0180955e31e5245b648bbb24a4ac4ab03a1de81513642325220bcd

RUN apk upgrade --no-cache

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip uninstall -y setuptools wheel pip

# Copy application code
COPY . .

# Environment variables
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 TZ=Etc/UTC
EXPOSE 8000

USER 65534:65534

# Run the application
CMD ["python", "main.py"]
