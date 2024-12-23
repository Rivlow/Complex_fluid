import numpy as np
import pyvista as pv

def safe_max(array):
    if len(array) == 0:
        return 0
    return np.max(array)

def analyze_mesh_convergence(vtk_file, x_limits):
    mesh = pv.read(vtk_file)
    point_data = mesh.cell_data_to_point_data()
    
    x = mesh.points[:, 0]
    y = mesh.points[:, 1]
    
    x_entrance_end, x_expansion_start, x_expansion_end, x_exit_start = [-x for x in x_limits]
    
    entrance_mask = x > x_entrance_end
    expansion_mask = (x <= x_expansion_start) & (x >= x_expansion_end)
    exit_mask = x < x_exit_start
    
    for name, mask in [("entrance", entrance_mask), 
                      ("expansion", expansion_mask), 
                      ("exit", exit_mask)]:
        print(f"Points in {name} zone: {np.sum(mask)}")
    
    tau = point_data['tau']
    U = point_data['U']
    N1 = point_data['N1']
    
    metrics = {}
    zones = {
        'entrance': entrance_mask,
        'expansion': expansion_mask,
        'exit': exit_mask
    }
    
    for zone_name, mask in zones.items():
        if np.any(mask):
            metrics[f'{zone_name}_tau_max'] = safe_max(np.linalg.norm(tau[mask], axis=1))
            metrics[f'{zone_name}_N1_max'] = safe_max(np.abs(N1[mask]))
            metrics[f'{zone_name}_U_max'] = safe_max(np.linalg.norm(U[mask], axis=1))
        else:
            print(f"Warning: No points in {zone_name} zone")
            metrics[f'{zone_name}_tau_max'] = metrics[f'{zone_name}_N1_max'] = metrics[f'{zone_name}_U_max'] = 0
    
    metrics['total_cells'] = mesh.n_cells
    print(f"Total number of cells: {metrics['total_cells']}")
    
    return metrics