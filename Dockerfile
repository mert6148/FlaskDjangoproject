# Dockerfile for FlaskDjango project
FROM python:3.11-slim

# Proje dizini
WORKDIR /app

# sistem bağımlılıkları
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# requirements
COPY auth/Flask-Django_python/requirements.txt /app/requirements.txt
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip
RUN pip install -r /app/requirements.txt

# kod kopyala
COPY . /app

# ortam değişkenleri
ENV FLASK_APP=auth/main.py
ENV FLASK_ENV=development
ENV MODE=flask

EXPOSE 5000 8000 9000

# başlatma komutu
CMD ["python", "frontend_integration.py"]
