import numpy as np
import matplotlib.pyplot as plt
import pyvista as pv
import os

def find_vtk_file(folder_path):

    for file in os.listdir(folder_path):
        if file.endswith('.vtk'):
            return os.path.join(folder_path, file)
    return None

def get_channel_boundaries(points):
    x = points[:,0]
    y = points[:,1]
    
    n_bins = 50
    x_bins = np.linspace(x.max(), x.min(), n_bins)
    bin_heights = np.zeros(n_bins-1)
    bin_centers = np.zeros(n_bins-1)
    
    for i in range(len(x_bins)-1):
        mask = (x <= x_bins[i]) & (x > x_bins[i+1])
        if np.any(mask):
            y_slice = y[mask]
            bin_heights[i] = y_slice.max() - y_slice.min()
            bin_centers[i] = (x_bins[i] + x_bins[i+1])/2
    
    # Remove bins with zero height
    valid_bins = bin_heights > 0
    heights = bin_heights[valid_bins]
    x_centers = bin_centers[valid_bins]
    
    height_ratios = heights[1:] / heights[:-1]
    transition_idx = np.argmax(np.abs(height_ratios - 1))
    
    inlet_heights = heights[:transition_idx]
    outlet_heights = heights[transition_idx+1:]
    
    small_height = np.mean(inlet_heights)
    large_height = np.mean(outlet_heights)
    x_transition = x_centers[transition_idx]
    
    return {
        'small_height': small_height,
        'large_height': large_height, 
        'transition_x': x_transition,
        'expansion_ratio': large_height / small_height
    }
def get_zone_boundaries(x, y, x_start, x_end, debug=False):
    

    mask = (x >= x_start) & (x <= x_end)
    
    if not np.any(mask):
        if debug:
            print("No points found in zone!")
        return np.array([]), np.array([]), np.array([])
    
    x_zone = x[mask]
    y_zone = y[mask]
    
    sort_idx = np.argsort(x_zone)
    x_zone = x_zone[sort_idx]
    y_zone = y_zone[sort_idx]
    
    x_unique, indices = np.unique(x_zone, return_inverse=True)
    y_upper = np.zeros_like(x_unique)
    y_lower = np.zeros_like(x_unique)
    
    for i in range(len(x_unique)):
        mask_x = indices == i
        y_vals = y_zone[mask_x]
        y_upper[i] = np.max(y_vals)
        y_lower[i] = np.min(y_vals)
        
    return x_unique, y_upper, y_lower

def plot_geometry(mesh_data, expansion_bounds):
    points = mesh_data['points']
    x = points[:, 0]
    y = points[:, 1]
    
    plt.figure(figsize=(12, 4))
    plt.scatter(x, y, s=1, alpha=0.1, color='black')
    
    geometry = get_channel_boundaries(points)
    x_transition = geometry['transition_x']
    
    x_entry = expansion_bounds[1]  
    x_exit = expansion_bounds[0]  
    
    x_coords = np.linspace(x.min(), x.max(), 100)
    y_small = geometry['small_height']/2
    y_large = geometry['large_height']/2
    
    # Entry zone (x > 0.3)
    mask_entry = x_coords >= x_entry
    plt.fill_between(x_coords[mask_entry], 
                    -y_small, y_small,
                    alpha=0.2, color='blue', label='Entry zone')
    
    # Expansion zone (0.2 <= x <= 0.3)
    mask_exp = (x_coords >= x_exit) & (x_coords < x_entry)
    plt.fill_between(x_coords[mask_exp],
                    -np.interp(x_coords[mask_exp], [x_exit, x_entry], [y_large, y_small]),
                    np.interp(x_coords[mask_exp], [x_exit, x_entry], [y_large, y_small]),
                    alpha=0.2, color='green', label='Expansion zone')
    
    # Exit zone (x < 0.2)
    mask_exit = x_coords < x_exit
    plt.fill_between(x_coords[mask_exit],
                    -y_large, y_large,
                    alpha=0.2, color='red', label='Exit zone')
    
    plt.grid(True, alpha=0.3)
    plt.xlabel('X Position')
    plt.ylabel('Y Position')
    plt.title('Flow Geometry')
    plt.legend()
    plt.axis('equal')
    plt.tight_layout()
    plt.show()

