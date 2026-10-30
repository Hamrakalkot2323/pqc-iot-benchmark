FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV HOME=/root
ENV OQS_INSTALL_PATH=/root/_oqs/lib

RUN apt-get update && apt-get install -y \
    python3 \
    python3-venv \
    python3-pip \
    python3-dev \
    build-essential \
    cmake \
    ninja-build \
    git \
    libssl-dev \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"


RUN pip install --no-cache-dir setuptools wheel \
    && pip install --no-cache-dir liboqs-python==0.16.0.1 cryptography \
    && python -c "import oqs, cryptography; print('liboqs version:', oqs.oqs_version()); print('cryptography version:', cryptography.__version__); print('ML-KEM-512:', 'ML-KEM-512' in oqs.get_enabled_kem_mechanisms()); print('ML-DSA-44:', 'ML-DSA-44' in oqs.get_enabled_sig_mechanisms())"


WORKDIR /app

CMD ["python", "--version"]
