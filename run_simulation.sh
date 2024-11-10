#!/bin/bash

# run_ptt_simulation.sh

# Error handling function
error_exit() {
    echo "Error: $1" >&2
    exit 1
}

# Function to detect OpenFOAM installation
detect_openfoam() {
    # Common OpenFOAM installation paths
    local paths=(
        "/opt/openfoam9"
        "/usr/lib/openfoam/openfoam*"
        "/opt/homebrew/opt/openfoam"  # for MacOS
        "/usr/local/opt/openfoam"
    )

    for path in "${paths[@]}"; do
        # Use glob expansion to find OpenFOAM directory
        for dir in $path; do
            if [ -f "$dir/etc/bashrc" ]; then
                echo "$dir"
                return 0
            fi
        done
    done

    error_exit "OpenFOAM installation not found. Please set FOAM_DIR manually."
}

# Function to detect user's OpenFOAM directory
detect_user_dir() {
    local version="9"  # Default version
    local user_name=$(whoami)
    local possible_dirs=(
        "$HOME/OpenFOAM/$user_name-$version"
        "$HOME/OpenFOAM/openfoam-$version"
        "$HOME/OpenFOAM/$version"
    )

    for dir in "${possible_dirs[@]}"; do
        if [ -d "$dir" ]; then
            echo "$dir"
            return 0
        fi
    done

    error_exit "User OpenFOAM directory not found. Please set USER_DIR manually."
}

# Path definitions with auto-detection
FOAM_DIR=$(detect_openfoam)
USER_DIR=$(detect_user_dir)
RHEOTOOL_DIR=$USER_DIR/applications/rheoTool/of90
CASE_NAME=PTT_case
TARGET_DIR="$PWD/$CASE_NAME"

# Environment configuration
echo "Configuring OpenFOAM environment..."
if [ -f "$FOAM_DIR/etc/bashrc" ]; then
    source "$FOAM_DIR/etc/bashrc" || error_exit "Failed to source OpenFOAM"
else
    error_exit "OpenFOAM bashrc not found at $FOAM_DIR/etc/bashrc"
fi

# PETSc and HYPRE configuration
echo "Configuring PETSc..."
export PETSC_DIR=$USER_DIR/ThirdParty/petsc-3.16.5
export PETSC_ARCH=arch-linux-c-opt
export LD_LIBRARY_PATH=$PETSC_DIR/$PETSC_ARCH/lib:$LD_LIBRARY_PATH

# Directory verification
echo "Checking required directories..."
[ ! -d "$RHEOTOOL_DIR" ] && error_exit "rheoTool directory not found: $RHEOTOOL_DIR"
[ ! -d "$PETSC_DIR" ] && error_exit "PETSc directory not found: $PETSC_DIR"

# Required commands verification
echo "Checking required tools..."
for cmd in rheoFoam blockMesh; do
    which $cmd > /dev/null 2>&1 || error_exit "$cmd not found in PATH"
done

# 1. Case directory preparation
echo "Preparing simulation directory..."
mkdir -p "$TARGET_DIR" || error_exit "Cannot create target directory"

# 2. Copy PTT example case
echo "Copying PTT case files..."
PTT_CASE_DIR=$RHEOTOOL_DIR/tutorials/rheoFoam/CrossSlot/PTTLog
[ ! -d "$PTT_CASE_DIR" ] && error_exit "PTT case directory not found: $PTT_CASE_DIR"

cp -r $PTT_CASE_DIR/* "$TARGET_DIR/" || error_exit "Cannot copy case files"

# 3. Move to case directory
cd "$TARGET_DIR" || error_exit "Cannot access case directory"

# 4. Check and adapt permissions
for script in Allclean Allrun; do
    if [ -f "./$script" ] && [ ! -x "./$script" ]; then
        chmod +x "./$script" || error_exit "Cannot make $script executable"
    fi
done

# 5. Clean old results
echo "Cleaning old results..."
if [ -x "./Allclean" ]; then
    ./Allclean
else
    rm -rf [0-9]* processor* postProcessing
fi

# 6. Run simulation
echo "Starting simulation..."
if [ -x "./Allrun" ]; then
    ./Allrun
else
    blockMesh || error_exit "blockMesh failed"
    setFields 2>/dev/null  # Optional, don't error if not needed
    rheoFoam || error_exit "rheoFoam failed"
fi

echo "Simulation completed successfully!"

# Display useful information
echo ""
echo "Important Information:"
echo "------------------------"
echo "Simulation directory: $TARGET_DIR"
echo "To access results: cd $TARGET_DIR"
echo "To visualize: paraFoam"

# Optional: Display system information
echo ""
echo "System Information:"
echo "------------------------"
echo "OpenFOAM path: $FOAM_DIR"
echo "User directory: $USER_DIR"
echo "RheoTool path: $RHEOTOOL_DIR"