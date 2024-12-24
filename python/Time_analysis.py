from process_data import *
from geometry import *
from vorticity import *
from convergence import *
import os
import numpy as np
import matplotlib.pyplot as plt

def extract_profile(mesh_data, x_location, tolerance=0.0001):

    points = mesh_data['points']
    x, y = points[:, 0], points[:, 1]
    
    # Find points near the specified x location
    mask = np.abs(x - x_location) < tolerance
    
    if not np.any(mask):
        raise ValueError(f"No points found at x = {x_location}")
    
    # Get unique y values within a reasonable spacing
    y_values = y[mask]
    y_min, y_max = np.min(y_values), np.max(y_values)
    y_interp = np.linspace(y_min, y_max, 100)  
    
    # Interpolate each component
    U_x = np.interp(y_interp, y_values[np.argsort(y_values)], 
                    mesh_data['U'][mask, 0][np.argsort(y_values)])
    U_y = np.interp(y_interp, y_values[np.argsort(y_values)],
                    mesh_data['U'][mask, 1][np.argsort(y_values)])
    
    tau = mesh_data['tau'][mask]
    tau_xx = np.interp(y_interp, y_values[np.argsort(y_values)], 
                      tau[np.argsort(y_values), 0])
    tau_yy = np.interp(y_interp, y_values[np.argsort(y_values)],
                      tau[np.argsort(y_values), 1])
    tau_xy = np.interp(y_interp, y_values[np.argsort(y_values)],
                      tau[np.argsort(y_values), 3])
    
    return {
        'y': y_interp,  # Now returning interpolated y values
        'U_x': U_x,
        'U_y': U_y,
        'tau_xx': tau_xx,
        'tau_yy': tau_yy,
        'tau_xy': tau_xy
    }

def plot_profiles(profiles_data, x_location, save=False, prefix=''):
    
    styles = {
        't_100': {'color': 'blue', 'marker': 'o', 'linestyle': '-', 'markersize': 4, 'markevery': 10},
        't_250': {'color': 'orange', 'marker': 's', 'linestyle': '--', 'markersize': 4, 'markevery': 10},
        't_350': {'color': 'green', 'marker': '^', 'linestyle': ':', 'markersize': 4, 'markevery': 10},
        't_500': {'color': 'red', 'marker': 'D', 'linestyle': '-.', 'markersize': 4, 'markevery': 10},
        't_1000': {'color': 'purple', 'marker': 'v', 'linestyle': '--', 'markersize': 4, 'markevery': 10}
    }
    
    # Plot velocities
    fig_vel, axes_vel = plt.subplots(1, 2, figsize=(12, 5))
    
    velocity_components = {
        0: ('U_x', 'Axial Velocity'),
        1: ('U_y', 'Vertical Velocity')
    }
    
    for idx, (component, label) in velocity_components.items():
        ax = axes_vel[idx]
        for sim_name, data in profiles_data.items():
            style = styles[sim_name]
            ax.plot(data[component], data['y'],
                   label=f'Simulation {sim_name}',
                   color=style['color'],
                   marker=style['marker'],
                   linestyle=style['linestyle'],
                   markersize=style['markersize'],
                   markevery=style['markevery'])
            
        ax.set_xlabel(label)
        ax.set_ylabel('y')
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8)
    
    plt.tight_layout()
    if save:
        plt.savefig(f"{prefix}velocities_x{x_location}.png", dpi=300, bbox_inches='tight')
    plt.show()
    
    # Plot stresses
    fig_stress, axes_stress = plt.subplots(1, 2, figsize=(12, 5))
    
    stress_components = {
        0: ('tau_xx', 'Normal Stress τxx'),
        1: ('tau_yy', 'Normal Stress τyy')
    }
    
    for idx, (component, label) in stress_components.items():
        ax = axes_stress[idx]
        for sim_name, data in profiles_data.items():
            style = styles[sim_name]
            ax.plot(data[component], data['y'],
                   label=f'Simulation {sim_name}',
                   color=style['color'],
                   marker=style['marker'],
                   linestyle=style['linestyle'],
                   markersize=style['markersize'],
                   markevery=style['markevery'])
            
        ax.set_xlabel(label)
        ax.set_ylabel('y')
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8)
    
    plt.tight_layout()
    if save:
        plt.savefig(f"{prefix}stresses_x{x_location}.png", dpi=300, bbox_inches='tight')
    plt.show()

def main():

    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_path = os.path.join(base_path, 'openfoam_container', 'output',
                              'fene_p', 'expansion', 'time_variation')
    
    figures_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'figures')
    if not os.path.exists(figures_dir):
        os.makedirs(figures_dir)
        print(f"Created figures directory at: {figures_dir}")
    
    sim_files = {
        't_100': os.path.join(output_path, 't_100'),
        't_250': os.path.join(output_path, 't_250'),
        't_350': os.path.join(output_path, 't_350'),
        't_500': os.path.join(output_path, 't_500'),
        't_1000': os.path.join(output_path, 't_1000')
    }
    
    sim_data = {}
    for name, folder in sim_files.items():
        try:
            sim_data[name] = load_vtk_data(folder)
        except Exception as e:
            print(f"Failed to load {name}: {str(e)}")
    
    # Extract profiles at x = 0.2
    x_location = 0.2
    profiles_data = {}
    
    for name, data in sim_data.items():
        try:
            profiles_data[name] = extract_profile(data, x_location)
        except Exception as e:
            print(f"Failed to extract profile for {name}: {str(e)}")
    
    if profiles_data:
        plot_profiles(profiles_data, x_location, save=True, prefix='python/figures/profiles_')
    else:
        print("No profiles were successfully extracted")

if __name__ == "__main__":
    main()