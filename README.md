# Synopsis

In the framework of the ULiege course [PHYS3133](https://www.programmes.uliege.be/cocoon/20232024/en/cours/PHYS3133-1.html), this project focuses on analyzing the behavior of complex fluids. Specifically, we investigate non-Newtonian fluids using OpenFOAM simulations with a focus on channel flow with multiple obstacles.

# Environment Setup

The project now uses Docker with OpenFOAM-extend v5.0 for a more streamlined setup process. This eliminates the need for manual installation of OpenFOAM and its dependencies.

## Project Structure

```
.
├── .devContainer
├── .vscode
├── openfoam_data
│   ├── simulation
│   │   └── fene_p
│   │       ├── four_obstacle
│   │       │   ├── 0
│   │       │   ├── constant
│   │       │   ├── system
│   │       │   │   ├── blockMeshDict
│   │       │   │   ├── controlDict
│   │       │   │   ├── decomposeParDict
│   │       │   │   ├── fvSchemes
│   │       │   │   ├── fvSolution
│   │       │   │   └── sampleDict
│   │       ├── single_obstacle
│   │       └── incompressible
├── Dockerfile
├── generator_mesh.py
├── run_foam.sh
└── tutorials_tree.txt
```

## Geometry Configuration

The simulation uses a configurable channel geometry with three obstacles. The geometry parameters can be modified using the `generator_mesh.py` script, which allows customization of:

- Inlet length
- Obstacle width
- Obstacle spacing
- Channel height
- Channel depth

The script automatically updates the `blockMeshDict` file with the new parameters.

## Running Simulations

1. Ensure you are in the Docker container environment
2. Navigate to the simulation directory:
   ```bash
   cd openfoam_data
   ```
3. Make the run script executable:
   ```bash
   chmod +x run_foam.sh
   ```
4. Execute the simulation:
   ```bash
   ./run_foam.sh
   ```

The run script handles:
- Environment setup
- Progress monitoring with percentage completion
- Automatic cleanup of previous results
- VTK conversion for post-processing
- Error handling and status reporting

## Directory Structure

Each simulation case contains:

- `0/`: Initial conditions
- `constant/`: Physical properties and mesh configuration
- `system/`: Simulation control parameters
  - `blockMeshDict`: Mesh generation settings
  - `controlDict`: Time control and output settings
  - `fvSchemes`: Discretization schemes
  - `fvSolution`: Solution control parameters
- `Allrun`: Script for running the simulation
- `Allclean`: Script for cleaning previous results

## Important Notes

- Make sure the `INPUT_PATH` in `run_foam.sh` points to your simulation directory
- The default path is `/root/openfoam_data/simulation/fene_p/four_obstacle`
- All operations are now containerized, eliminating system-specific dependencies
- Results can be post-processed using ParaView or other VTK-compatible tools

## Visualization

After the simulation completes, results are automatically converted to VTK format for visualization. You can use ParaView or other VTK-compatible tools to analyze the results.