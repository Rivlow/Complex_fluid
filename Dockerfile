# Utiliser Ubuntu 20.04 comme image de base
FROM ubuntu:20.04

# Définir les variables d'environnement pour éviter les interactions pendant l'installation
ENV DEBIAN_FRONTEND=noninteractive
ENV WM_PROJECT=foam
ENV WM_FORK=extend
ENV FOAM_INST_DIR=/opt/foam
ENV WM_PROJECT_VERSION=5.0
ENV WM_COMPILER=Gcc
ENV WM_COMPILER_TYPE=system
ENV WM_PRECISION_OPTION=DP
ENV WM_COMPILE_OPTION=Opt
ENV WM_MPLIB=SYSTEMOPENMPI

# Installation des dépendances nécessaires
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    cmake \
    flex \
    bison \
    zlib1g-dev \
    libboost-system-dev \
    libboost-thread-dev \
    libopenmpi-dev \
    openmpi-bin \
    gnuplot \
    libreadline-dev \
    libncurses-dev \
    libxt-dev \
    qtbase5-dev \
    qttools5-dev \
    libqt5opengl5-dev \
    freeglut3-dev \
    libscotch-dev \
    libcgal-dev \
    python3 \
    python3-dev \
    wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Créer le répertoire d'installation
RUN mkdir -p $FOAM_INST_DIR

# Cloner OpenFOAM-extend directement dans le bon dossier
WORKDIR $FOAM_INST_DIR
RUN git clone https://git.code.sf.net/p/foam-extend/foam-extend-5.0 foam-extend-5.0

# Configuration de l'environnement
WORKDIR $FOAM_INST_DIR/foam-extend-5.0
RUN . etc/bashrc && \
    # Compiler OpenFOAM-extend
    ./Allwmake -j$(nproc) 2>&1 | tee log.Allwmake

# Ajouter le chargement de l'environnement OpenFOAM au .bashrc
RUN echo "source $FOAM_INST_DIR/foam-extend-5.0/etc/bashrc" >> /root/.bashrc

# Définir le répertoire de travail par défaut
WORKDIR /root

# Point d'entrée par défaut
CMD ["/bin/bash"]