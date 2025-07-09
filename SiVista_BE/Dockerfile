FROM ubuntu:24.04

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Update the package list and install dependencies in one go
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc libc-dev libpq-dev python3.12 python3-pip python3-venv redis-server supervisor && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt

# Create a virtual environment
RUN python3 -m venv /opt/venv

# Activate virtual environment and install dependencies
RUN /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install -r requirements.txt

# Make sure the virtualenv binaries are on PATH
ENV PATH="/opt/venv/bin:$PATH"

COPY . /app

EXPOSE 8000

ENV DJANGO_SETTINGS_MODULE=SiVista_BE.settings

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

CMD ["supervisord", "-c", "/etc/supervisor/supervisord.conf"]