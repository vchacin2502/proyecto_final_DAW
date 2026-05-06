# Dockerfile para Django
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# Normalize shell scripts copied from Windows and make them executable
RUN sed -i 's/\r$//' www/*.sh && chmod +x www/*.sh

# Run migrations and collect static files
ENTRYPOINT ["bash", "www/entrypoint.sh"]
