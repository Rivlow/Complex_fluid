#!/bin/bash

# Define paths
TEMPLATE_PATH="/opt/openfoam_container/simulation/newtonian/template"
ACTUAL_PATH="/opt/openfoam_container/simulation/newtonian/actual"

# Start time measurement
start_time=$(date +%s)

# Color definitions
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_header() {
    local title=$1
    local length=${#title}
    local total_length=70
    local padding=$(( (total_length - length - 2) / 2 ))
    
    echo -e "\n${BLUE}"
    printf '%*s' "$total_length" | tr ' ' '='
    echo
    printf "%*s%s%*s\n" $padding '' "$title" $padding ''
    printf '%*s' "$total_length" | tr ' ' '='
    echo -e "${NC}"
}

print_step() {
    echo -e "${GREEN}[+] $1${NC}"
}

monitor_progress() {
    local sim_pid=$1
    local log_file="simulation.log"
    
    # Extract endTime value
    end_time=$(grep "^endTime" system/controlDict | awk '{print $2}' | tr -d ';')
    print_step "Total simulation time: $end_time"
    
    echo -e "\n${YELLOW}=== OpenFOAM Output ===${NC}"
    
    local last_log=""
    while kill -0 $sim_pid 2>/dev/null; do
        if [ -f "$log_file" ]; then
            current_log=$(tail -n 1 "$log_file" 2>/dev/null)
            if [ "$current_log" != "$last_log" ] && [ ! -z "$current_log" ]; then
                echo -e "${YELLOW}$current_log${NC}"
                last_log=$current_log
            fi
        fi
        sleep 0.5
    done
    
    echo -e "\n"
    print_step "Simulation completed."
}

# Main execution
print_header "OpenFOAM Simulation"

print_step "Preparing simulation directory..."

# Remove old actual folder if exists and copy template
if [ -d "$ACTUAL_PATH" ]; then
    print_step "Removing old simulation directory..."
    rm -rf "$ACTUAL_PATH"
fi

print_step "Copying template to simulation directory..."
cp -r "$TEMPLATE_PATH" "$ACTUAL_PATH"

cd "$ACTUAL_PATH"

print_step "Starting OpenFOAM simulation setup..."

./Allclean > clean.log 2>&1
print_step "Cleaning completed"

print_header "Running Simulation"
print_step "Initializing simulation..."

./Allrun > simulation.log 2>&1 &
allrun_pid=$!

monitor_progress $allrun_pid

wait $allrun_pid

print_header "Post-processing"
print_step "Converting results to VTK format..."
foamToVTK > vtk.log 2>&1

print_step "All operations completed successfully."

# Calculate total execution time
end_time=$(date +%s)
total_time=$((end_time - start_time))
hours=$((total_time / 3600))
minutes=$(( (total_time % 3600) / 60 ))
seconds=$((total_time % 60))

print_header "Execution Summary"
echo -e "${GREEN}Total execution time: ${hours}h ${minutes}m ${seconds}s${NC}"

cd /opt/openfoam_container
exit 0