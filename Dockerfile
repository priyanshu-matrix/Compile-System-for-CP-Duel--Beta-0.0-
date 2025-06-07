FROM ubuntu:22.04

# Set environment to avoid user prompts during package install
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies, including sudo
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        g++ \
        python3 \
        openjdk-17-jdk \   
        sudo \
        make \
        build-essential \
        libcap-dev \
        pkg-config \
        asciidoc \
        libsystemd-dev \
        ca-certificates \
        libxml2-utils \
        docbook-xml \
        docbook-xsl \
        xsltproc \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user with sudo access
RUN useradd -ms /bin/bash judge && \
    echo 'judge ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

# Install isolate from source with a fallback if doc generation fails
RUN git clone https://github.com/ioi/isolate.git /tmp/isolate && \
    cd /tmp/isolate && \
    # First try with docs
    (make || \
    # If fails, try without building docs
    (sed -i 's/^all:.*$/all: isolate isolate-check-environment/' Makefile && make)) && \
    # Install without docs if needed
    (make install || cp isolate /usr/local/bin/ && mkdir -p /var/local/lib/isolate) && \
    cd / && \
    rm -rf /tmp/isolate

# Create app directory and set permissions
RUN mkdir -p /app && \
    chown -R judge:judge /app

# Switch to non-root user (optional, for safety)
USER judge

# Set working directory
WORKDIR /app

