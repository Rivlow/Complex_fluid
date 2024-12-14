#!/bin/bash

# Source OpenFOAM environment
#source /opt/foam/foam-extend-5.0/etc/bashrc

# Define paths
INPUT_PATH="/root/openfoam_data/simulation/fene_p/four_obstacle"

print_header() {
    local title=$1
    local length=${#title}
    local total_length=50
    local padding=$(( (total_length - length - 2) / 2 ))
    
    echo
    printf '%*s' "$total_length" | tr ' ' '-'
    echo
    printf "%*s%s%*s\n" $padding '' "$title" $padding ''
    printf '%*s' "$total_length" | tr ' ' '-'
    echo
}

# Function to monitor simulation progress
monitor_progress() {
    # Extract endTime value
    end_time=$(grep "^endTime" system/controlDict | awk '{print $2}' | tr -d ';')
    echo "Total simulation time: $end_time"
    
    # Variable to store last displayed time
    last_time=""
    
    # Wait for simulation to actually start
    while [ ! -f "log.viscoelasticFluidFoam" ]; do
        sleep 1
    done
    
    while true; do
        # Get latest time directory
        latest_time=$(ls -d [0-9]* 2>/dev/null | sort -n | tail -n 1)
        
        if [ ! -z "$latest_time" ] && [ "$latest_time" != "$last_time" ]; then
            # Calculate percentage
            progress=$(awk "BEGIN {printf \"%.1f\", ($latest_time/$end_time)*100}")
            printf "\033[K\rSimulation progress: %s / %s (%.1f%%)" "$latest_time" "$end_time" "$progress"
            last_time=$latest_time
        fi
        
        # Check if parent process still exists
        if ! kill -0 $1 2>/dev/null; then
            if [ -f "${latest_time}/U" ]; then
                printf "\n"
                echo "Simulation completed successfully."
                return 0
            else
                printf "\n"
                echo "Simulation stopped unexpectedly."
                return 1
            fi
        fi
        
        # If endTime is reached, consider it complete
        if [ ! -z "$latest_time" ] && [ "$latest_time" = "$end_time" ]; then
            printf "\n"
            echo "Simulation reached end time successfully."
            return 0
        fi
        
        sleep 1
    done
}

# Main execution
print_header "Initialization"

# Check if input directory exists
if [ ! -d "$INPUT_PATH" ]; then
    echo "Error: Input directory $INPUT_PATH not found"
    exit 1
fi

echo "Accessing input directory..."
cd "$INPUT_PATH"

echo "Starting OpenFOAM simulation setup..."
./Allclean

print_header "Simulation"

# Run Allrun in background and get its PID
echo "Initializing simulation..."
./Allrun &
allrun_pid=$!

# Monitor progress with the PID
monitor_progress $allrun_pid
simulation_status=$?
wait $allrun_pid

print_header "Output"

# Check the final state of the simulation
if [ $simulation_status -eq 0 ]; then
    echo "Converting results to VTK format..."
    foamToVTK
    echo "Post-processing completed successfully."
else
    echo "Error during simulation. Check error messages above for details."
    exit 1
fi

# Return to openfoam_data directory
cd /root/openfoam_data
echo "All operations completed."
exit 0