# Use Ubuntu 22.04 as the base image
FROM ubuntu:22.04

# Set environment variables to avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive
ENV QT_QPA_PLATFORM=offscreen

# Update and install necessary dependencies including Python 3.10
RUN apt-get update && apt-get install -y \
    wget \
    python3.10 \
    python3-pip \
    libqt5widgets5 \
    libqt5gui5 \
    libqt5core5a \
    libqt5network5 \
    libqt5printsupport5 \
    libqt5designer5 \
    libqt5multimedia5 \
    libqt5multimediawidgets5 \
    libqt5opengl5 \
    libqt5sql5 \
    libqt5xml5 \
    libqt5xmlpatterns5 \
    libgit2-1.1 \
    libruby3.0 \
    && apt-get clean

# Download and install KLayout
RUN wget https://www.klayout.org/downloads/Ubuntu-22/klayout_0.29.5-1_amd64.deb \
    && dpkg -i klayout_0.29.5-1_amd64.deb \
    && apt-get install -f -y \
    && rm klayout_0.29.5-1_amd64.deb

WORKDIR  /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 50051

CMD ["python3", "grpc_server.py"]
