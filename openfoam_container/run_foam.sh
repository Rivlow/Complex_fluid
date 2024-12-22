#!/bin/bash

# Define paths
TEMPLATE_PATH="/opt/openfoam_container/simulation/fene_p/contraction/template"
ACTUAL_PATH="/opt/openfoam_container/simulation/fene_p/contraction/actual"

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

print_error() {
   echo -e "${RED}[!] Error: $1${NC}"
}

monitor_progress() {
   local sim_pid=$1
   local log_file="simulation.log"
   
   # Extract endTime value
   end_time=$(grep "^endTime" system/controlDict | awk '{print $2}' | tr -d ';')
   print_step "Total simulation time: $end_time"
   
   echo -e "\n${YELLOW}=== OpenFOAM Output ===${NC}"
   
   local last_time=""
   local last_log=""
   
   tput sc 
   echo -e "${BLUE}[*] Simulation progress: 0 / $end_time (0.0%)${NC}"

   while kill -0 $sim_pid 2>/dev/null; do

       if [ -f "$log_file" ]; then
           current_log=$(tail -n 1 "$log_file" 2>/dev/null)
           if [ "$current_log" != "$last_log" ] && [ ! -z "$current_log" ]; then
               echo -e "${YELLOW}$current_log${NC}"
               last_log=$current_log
           fi
       fi
       
       # Get latest time directory
       current_time=$(ls -d [0-9]* 2>/dev/null | sort -n | tail -n 1)
       
       if [ ! -z "$current_time" ] && [ "$current_time" != "$last_time" ]; then
           progress=$(awk "BEGIN {printf \"%.1f\", ($current_time/$end_time)*100}")
           tput rc 
           tput el 
           echo -e "${BLUE}[*] Simulation progress: $current_time / $end_time ($progress%)${NC}"
           last_time=$current_time
       fi
       sleep 0.5
   done
   
   echo -e "\n"
   print_step "Simulation completed."
   
   if [ -d "$end_time" ] && [ -f "$end_time/U" ]; then
       return 0
   else
       print_error "No results found. Simulation may have failed."
       return 1
   fi
}

# Main execution
print_header "OpenFOAM Simulation"

# Clean actual folder
print_step "Preparing simulation directory..."

# Check template exists
if [ ! -d "$TEMPLATE_PATH" ]; then
    print_error "Template directory not found: $TEMPLATE_PATH"
    cd /opt/openfoam_container
    exit 1
fi

# Remove old actual folder
if [ -d "$ACTUAL_PATH" ]; then
    print_step "Removing old simulation directory..."
    rm -rf "$ACTUAL_PATH"
fi

# Copy template to actual
print_step "Copying template to simulation directory..."
cp -r "$TEMPLATE_PATH" "$ACTUAL_PATH"

cd "$ACTUAL_PATH" 2>/dev/null || { 
    print_error "Cannot access $ACTUAL_PATH"
    cd /opt/openfoam_container
    exit 1
}

print_step "Starting OpenFOAM simulation setup..."

./Allclean > clean.log 2>&1
print_step "Cleaning completed"

print_header "Running Simulation"
print_step "Initializing simulation..."

./Allrun > simulation.log 2>&1 & allrun_pid=$!

monitor_progress $allrun_pid
status=$?

wait $allrun_pid

if [ $status -ne 0 ]; then
    print_error "Simulation failed"
    cd /opt/openfoam_container
    exit 1
fi

print_header "Post-processing"
print_step "Converting results to VTK format..."
foamToVTK > vtk.log 2>&1

print_step "All operations completed successfully."

# Return initial location
cd /opt/openfoam_container
exit 0