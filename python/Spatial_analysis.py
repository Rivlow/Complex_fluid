from process_data import *
from geometry import *
from vorticity import *
from convergence import *
import os
import numpy as np
import matplotlib.pyplot as plt


def main():

    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_path = os.path.join(base_path, 'openfoam_container', 'output', 
                              'fene_p', 'expansion', 'mesh_variation')
    
    mesh_files = {
        'mesh_coarse': os.path.join(output_path, 'mesh_1_2'),
        'mesh_medium_low': os.path.join(output_path, 'mesh_2_3'),
        'mesh_medium_mid': os.path.join(output_path, 'mesh_3_4'),
        'mesh_medium_top': os.path.join(output_path, 'mesh_4_5'),
        'mesh_fine': os.path.join(output_path, 'mesh_1_1'),
        'mesh_best': os.path.join(output_path, 'mesh_11_10'),
    }
    

    # Plot vorticity + geometry
    expansion_bounds = (0.05, 0.3)
    best_mesh = load_vtk_data(os.path.join(output_path, 'mesh_11_10'))
    #plot_geometry(best_mesh, expansion_bounds)
    plot_vorticity_field(best_mesh['points'], best_mesh['U'], save=True, prefix='python/figures/plot_')
    
    # Convergence plots : velocity, vorticity and stress (xx, xy, yy)
    #mesh_data = load_all_meshes(mesh_files)
    #stats = plot_convergence(mesh_data, save=True, prefix='python/figures/convergence_')



if __name__ == "__main__":
    main()