# Dockerfile - Environnement de build pour l'ISO NextProjectOS
FROM debian:bookworm AS builder

LABEL description="NextProjectOS ISO Builder"
LABEL maintainer="NextProjectOS"

# Installation des outils de build
RUN apt-get update && apt-get install -y --no-install-recommends \
    debootstrap \
    squashfs-tools \
    xorriso \
    isolinux \
    grub-pc-bin \
    grub-common \
    mtools \
    dosfstools \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/npos

# Le répertoire /opt/npos doit être monté depuis l'hôte
# Lancement : docker run --rm -v <projet>:/opt/npos npos-builder bash scripts/build-iso.sh --non-interactive
