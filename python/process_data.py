import pyvista as pv
import numpy as np
import os

def load_vtk_data(base_folder):
    for file in os.listdir(base_folder):
        if file.endswith('.vtk'):
            mesh = pv.read(os.path.join(base_folder, file))
            point_data = mesh.cell_data_to_point_data()
            
            return {
                'points': mesh.points,
                'U': point_data['U']
            }
    raise FileNotFoundError(f'No .vtk file found in {base_folder}')

def load_all_meshes(mesh_folders):
    return {
        mesh_name: load_vtk_data(folder_path)
        for mesh_name, folder_path in mesh_folders.items()
    }

def filter_expansion_zone(mesh_data, x_limits):

    x = -mesh_data['points'][:, 0]  
    x_start, x_end = x_limits[1], x_limits[2]  
    
    expansion_mask = (x >= x_start) & (x <= x_end)
    
    if not np.any(expansion_mask):
        raise ValueError(f"No points found in expansion zone between {x_start} and {x_end}")
        
    filtered_data = {}
    for key, data in mesh_data.items():
        if key == 'mesh':
            filtered_data[key] = data  
        elif isinstance(data, np.ndarray):
            filtered_data[key] = data[expansion_mask]
        else:
            filtered_data[key] = data
            
    print(f"Filtered {np.sum(expansion_mask)} points in expansion zone")
    return filtered_data