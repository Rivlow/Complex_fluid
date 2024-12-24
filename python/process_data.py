import pyvista as pv
import numpy as np
import os

def load_vtk_data(base_folder, verbose=False):

    vtk_files = [f for f in os.listdir(base_folder) if f.endswith('.vtk')]
    if not vtk_files:
        raise FileNotFoundError(f"No VTK file found in {base_folder}")
    
    # nb : find only first vtk file !
    vtk_path = os.path.join(base_folder, vtk_files[0])
    mesh = pv.read(vtk_path)
    
    data = {'points': mesh.points}
    
    for name in mesh.point_data:
        data[name] = mesh.point_data[name]
    
    if verbose:
        print("\nLoaded VTK Data:")
        print("=" * 50)
        print(f"File: {vtk_files[0]}")
        print(f"Points: shape={mesh.points.shape}, dtype={mesh.points.dtype}")
        print("\nPoint data arrays:")
        for name in mesh.point_data:
            array = mesh.point_data[name]
            print(f"  {name}: shape={array.shape}, dtype={array.dtype}")
    
    return data


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