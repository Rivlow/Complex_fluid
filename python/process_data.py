import pyvista as pv
import numpy as np
import os

def load_vtk_data(base_folder, verbose=False):
    # Récupérer tous les fichiers VTK
    vtk_files = [f for f in os.listdir(base_folder) if f.endswith('.vtk')]
    if not vtk_files:
        raise FileNotFoundError(f"No VTK file found in {base_folder}")
    
    # Liste pour stocker les données de tous les fichiers
    all_data = []
    
    # Traiter chaque fichier VTK
    for vtk_file in vtk_files:
        vtk_path = os.path.join(base_folder, vtk_file)
        mesh = pv.read(vtk_path)
        
        # Créer le dictionnaire de données exactement comme avant
        data = {'points': mesh.points}
        
        for name in mesh.point_data:
            data[name] = mesh.point_data[name]
            
        # Ajouter à la liste
        all_data.append(data)
        
        if verbose:
            print(f"\nLoaded VTK Data for {vtk_file}:")
            print("=" * 50)
            print(f"Points: shape={mesh.points.shape}, dtype={mesh.points.dtype}")
            print("\nPoint data arrays:")
            for name in mesh.point_data:
                array = mesh.point_data[name]
                print(f"  {name}: shape={array.shape}, dtype={array.dtype}")
    
    return all_data


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

def extractData(vtk_data):
    
    try:
        pos = vtk_data['points']
        U = vtk_data['U']
        p = vtk_data['p']
        
        return pos, U, p
        
    except KeyError as e:
        raise KeyError(f"Missing data field: {e}. Required fields are 'points', 'U', and 'p'")

