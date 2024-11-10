# Installation Guide for OpenFOAM 9 with rheoTool

This guide details the step-by-step process to install OpenFOAM 9 with rheoTool on Ubuntu/WSL.

## Prerequisites

First, install the required dependencies:
```bash
sudo apt-get update
sudo apt-get install build-essential cmake flex libfl-dev bison zlib1g-dev \
    libboost-system-dev libboost-thread-dev libopenmpi-dev openmpi-bin \
    gnuplot libreadline-dev libncurses-dev libxt-dev qt5-default \
    libsm-dev libxext-dev libxrender-dev g++ gfortran gcc
```

## 1. Install OpenFOAM 9

Add OpenFOAM repository and install OpenFOAM 9:
```bash
# Add OpenFOAM repository
curl -s https://dl.openfoam.com/add-debian-repo.sh | sudo bash

# Update and install OpenFOAM 9
sudo apt-get update
sudo apt-get install openfoam9
```

### Configure OpenFOAM environment
Add OpenFOAM to your bashrc:
```bash
echo ". /opt/openfoam9/etc/bashrc" >> ~/.bashrc
source /opt/openfoam9/etc/bashrc
```

## 2. Install rheoTool

Create the necessary directories:
```bash
mkdir -p ~/OpenFOAM/fantaluca-9/applications
cd ~/OpenFOAM/fantaluca-9/applications
```

### Clone and prepare rheoTool
```bash
# Clone rheoTool (replace with your actual rheoTool acquisition method)
cp -r /path/to/rheoTool ~/OpenFOAM/fantaluca-9/applications/
```

## 3. Install and Configure PETSc

### Set up PETSc:
```bash
cd ~/OpenFOAM/fantaluca-9/ThirdParty
# Download and extract PETSc 3.16.5 (if not already present)

cd petsc-3.16.5
unset PETSC_DIR
unset PETSC_ARCH
export PETSC_DIR=$PWD
export PETSC_ARCH=arch-linux-c-opt

# Configure PETSc
./configure \
    CC=mpicc \
    CXX=mpicxx \
    FC=mpif90 \
    --with-debugging=0 \
    --with-shared-libraries=1 \
    --with-hypre=1 \
    --download-hypre=yes \
    --with-ssl=0 \
    --with-x=0 \
    COPTFLAGS='-O3' \
    CXXOPTFLAGS='-O3' \
    FOPTFLAGS='-O3'

# Build PETSc
make all
make check
```

## 4. Compile rheoTool

After PETSc is installed, compile rheoTool:
```bash
# Set up environment
source /opt/openfoam9/etc/bashrc
export PETSC_DIR=~/OpenFOAM/fantaluca-9/ThirdParty/petsc-3.16.5
export PETSC_ARCH=arch-linux-c-opt
export LD_LIBRARY_PATH=$PETSC_DIR/$PETSC_ARCH/lib:$LD_LIBRARY_PATH

# Compile rheoTool
cd ~/OpenFOAM/fantaluca-9/applications/rheoTool/of90/src
./Allwmake
```

## 5. Running Simulations

Simply run the present bash file
```bash
chmod +x run_simulation.sh
./run_simulation.sh
```

## 6. Visualizing Results

To visualize the results:
´´´bash
cd PTT_test
paraFoam
```

## Troubleshooting

If you encounter problems:

1. Check that all environment variables are correctly set:
```bash
echo $WM_PROJECT_DIR
echo $PETSC_DIR
echo $PETSC_ARCH
```

2. Verify that rheoFoam is in your PATH:
```bash
which rheoFoam
```

3. Make sure all libraries are accessible:
```bash
ldd $(which rheoFoam)
```

4. Check for compilation errors in the log files:
```bash
tail log.rheoFoam
```

## Important Notes

- Always make sure OpenFOAM environment is properly sourced before running simulations
- PETSc version 3.16.5 is required for this setup
- Keep environment variables consistent between compilation and execution
- The script assumes a specific directory structure; adjust paths if your setup differs