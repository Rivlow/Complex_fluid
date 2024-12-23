import numpy as np
import pyvista as pv
import matplotlib.pyplot as plt

def filter_significant_points(distances, values, n_bins=20):
    """
    Filter points to keep only the maximum values in each distance bin
    """
    bins = np.linspace(0, max(distances), n_bins)
    indices = np.digitize(distances, bins)
    
    filtered_distances = []
    filtered_values = []
    
    for i in range(1, len(bins)):
        mask = indices == i
        if np.any(mask):
            # Keep the maximum value in each bin
            max_idx = np.argmax(values[mask])
            bin_distances = distances[mask]
            bin_values = values[mask]
            filtered_distances.append(bin_distances[max_idx])
            filtered_values.append(bin_values[max_idx])
    
    return np.array(filtered_distances), np.array(filtered_values)

def analyze_stress_distribution_comparison(vtk_files, x_limits, radius=0.02):
    """
    Compares stress distributions between two meshes with simplified visualization
    """
    results = []
    for vtk_file in vtk_files:
        mesh = pv.read(vtk_file)
        point_data = mesh.cell_data_to_point_data()
        
        x = -mesh.points[:, 0]
        y = mesh.points[:, 1]
        
        tau = point_data['tau']
        tau_norms = np.linalg.norm(tau, axis=1)
        N1 = point_data['N1']
        
        max_tau_idx = np.argmax(tau_norms)
        max_N1_idx = np.argmax(np.abs(N1))
        
        results.append({
            'mesh_size': mesh.n_cells,
            'x': x,
            'y': y,
            'tau': tau_norms,
            'N1': np.abs(N1),
            'max_tau_pos': (x[max_tau_idx], y[max_tau_idx]),
            'max_N1_pos': (x[max_N1_idx], y[max_N1_idx]),
            'max_tau_val': tau_norms[max_tau_idx],
            'max_N1_val': np.abs(N1[max_N1_idx])
        })
    
    # Create comparison plots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    colors = ['blue', 'red']
    markers = ['o', 's']
    
    # Plot tau distributions
    for i, result in enumerate(results):
        max_pos = result['max_tau_pos']
        distances = np.sqrt((result['x'] - max_pos[0])**2 + 
                          (result['y'] - max_pos[1])**2)
        mask = distances <= radius
        
        # Filter points for distance plot
        filtered_distances, filtered_tau = filter_significant_points(
            distances[mask], result['tau'][mask])
        
        mesh_type = "Coarse" if i == 0 else "Fine"
        ax1.scatter(filtered_distances, filtered_tau,
                   alpha=0.6, c=colors[i], marker=markers[i], s=100,
                   label=f"{mesh_type} mesh ({result['mesh_size']} cells)")
        
        # Keep only points near the maximum for spatial plot
        near_max_mask = distances <= radius/2  # Reduce radius for clarity
        scatter = ax2.scatter(result['x'][near_max_mask], 
                            result['y'][near_max_mask],
                            c=result['tau'][near_max_mask], 
                            cmap='viridis',
                            marker=markers[i], 
                            alpha=0.7,
                            s=100)
        ax2.plot(max_pos[0], max_pos[1], '*', color=colors[i],
                markersize=20, label=f"{mesh_type} max")
    
    # Plot N1 distributions
    for i, result in enumerate(results):
        max_pos = result['max_N1_pos']
        distances = np.sqrt((result['x'] - max_pos[0])**2 + 
                          (result['y'] - max_pos[1])**2)
        mask = distances <= radius
        
        # Filter points for distance plot
        filtered_distances, filtered_N1 = filter_significant_points(
            distances[mask], result['N1'][mask])
        
        mesh_type = "Coarse" if i == 0 else "Fine"
        ax3.scatter(filtered_distances, filtered_N1,
                   alpha=0.6, c=colors[i], marker=markers[i], s=100,
                   label=f"{mesh_type} mesh ({result['mesh_size']} cells)")
        
        # Keep only points near the maximum for spatial plot
        near_max_mask = distances <= radius/2  # Reduce radius for clarity
        scatter = ax4.scatter(result['x'][near_max_mask], 
                            result['y'][near_max_mask],
                            c=result['N1'][near_max_mask], 
                            cmap='viridis',
                            marker=markers[i], 
                            alpha=0.7,
                            s=100)
        ax4.plot(max_pos[0], max_pos[1], '*', color=colors[i],
                markersize=20, label=f"{mesh_type} max")
    
    # Customize plots
    for ax in [ax1, ax3]:
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.set_xlabel('Distance from maximum')
        ax.legend()
        
    for ax in [ax2, ax4]:
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.set_xlabel('X Position')
        ax.set_ylabel('Y Position')
        ax.legend()
    
    ax1.set_ylabel('tau')
    ax1.set_title('Maximum tau vs Distance')
    
    ax2.set_title('Spatial Distribution of tau maxima')
    plt.colorbar(scatter, ax=ax2, label='tau')
    
    ax3.set_ylabel('N1')
    ax3.set_title('Maximum N1 vs Distance')
    
    ax4.set_title('Spatial Distribution of N1 maxima')
    plt.colorbar(scatter, ax=ax4, label='N1')
    
    plt.tight_layout()
    plt.show()
    
    # Print comparison statistics
    print("\nComparison Statistics:")
    for i, result in enumerate(results):
        mesh_type = "Coarse" if i == 0 else "Fine"
        print(f"\n{mesh_type} mesh ({result['mesh_size']} cells)")
        print(f"tau max: {result['max_tau_val']:.6f} at x={result['max_tau_pos'][0]:.6f}, y={result['max_tau_pos'][1]:.6f}")
        print(f"N1 max: {result['max_N1_val']:.6f} at x={result['max_N1_pos'][0]:.6f}, y={result['max_N1_pos'][1]:.6f}")