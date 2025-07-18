FROM ubuntu:24.04

# Build arguments
ARG DJANGO_ENV
ARG PORT
ARG DBNAME_DEV
ARG USERNAME_DEV
ARG PASSWORD_DEV
ARG AWS_ACCESS_KEY_ID_DEV
ARG AWS_SECRET_ACCESS_KEY_DEV
ARG AWS_STORAGE_BUCKET_NAME_DEV
ARG IMAGE_NAME
ARG CONTAINER_NAME
ARG GRPC_CHANNEL_DEV

# Export as environment variables
ENV DJANGO_ENV=$DJANGO_ENV
ENV PORT=$PORT
ENV DBNAME_DEV=$DBNAME_DEV
ENV USERNAME_DEV=$USERNAME_DEV
ENV PASSWORD_DEV=$PASSWORD_DEV
ENV AWS_ACCESS_KEY_ID_DEV=$AWS_ACCESS_KEY_ID_DEV
ENV AWS_SECRET_ACCESS_KEY_DEV=$AWS_SECRET_ACCESS_KEY_DEV
ENV AWS_STORAGE_BUCKET_NAME_DEV=$AWS_STORAGE_BUCKET_NAME_DEV
ENV IMAGE_NAME=$IMAGE_NAME
ENV CONTAINER_NAME=$CONTAINER_NAME
ENV GRPC_CHANNEL_DEV=$GRPC_CHANNEL_DEV

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc libc-dev libpq-dev python3.12 python3-pip python3-venv redis-server supervisor && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt

# Create virtual environment
RUN python3 -m venv /opt/venv

# Install Python dependencies
RUN /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install -r requirements.txt \
    gunicorn

# Set virtualenv path
ENV PATH="/opt/venv/bin:$PATH"

COPY . /app

EXPOSE 8000

ENV DJANGO_SETTINGS_MODULE=SiVista_BE.settings

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

CMD ["supervisord", "-c", "/etc/supervisor/supervisord.conf"]