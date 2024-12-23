import numpy as np
import pyvista as pv
import matplotlib.pyplot as plt

def analyze_stress_distribution(vtk_file, x_limits, radius=0.02):
    mesh = pv.read(vtk_file)
    point_data = mesh.cell_data_to_point_data()
    
    x = -mesh.points[:, 0]
    y = mesh.points[:, 1]
    
    tau = point_data['tau']
    tau_norms = np.linalg.norm(tau, axis=1)
    N1 = point_data['N1']
    
    max_tau_idx = np.argmax(tau_norms)
    max_N1_idx = np.argmax(np.abs(N1))
    
    max_tau_pos = np.array([x[max_tau_idx], y[max_tau_idx]])
    max_N1_pos = np.array([x[max_N1_idx], y[max_N1_idx]])
    
    def analyze_region(center, field, field_name):
        distances = np.sqrt((x - center[0])**2 + (y - center[1])**2)
        mask = distances <= radius
        
        if not np.any(mask):
            print(f"No points found within radius for {field_name}")
            return
        
        dist_masked = distances[mask]
        field_masked = field[mask]
        sort_idx = np.argsort(dist_masked)
        
        plt.figure(figsize=(10, 5))
        
        plt.subplot(121)
        plt.scatter(dist_masked[sort_idx], field_masked[sort_idx], alpha=0.5, s=20)
        plt.xlabel('Distance from maximum')
        plt.ylabel(field_name)
        plt.title(f'{field_name} vs Distance from Maximum')
        plt.grid(True)
        
        plt.subplot(122)
        plt.scatter(x[mask], y[mask], c=field[mask], cmap='viridis', alpha=0.5)
        plt.colorbar(label=field_name)
        plt.plot(center[0], center[1], 'r*', markersize=15, label='Maximum')
        plt.xlabel('X Position')
        plt.ylabel('Y Position')
        plt.title(f'Spatial Distribution of {field_name}')
        plt.legend()
        plt.grid(True)
        
        plt.tight_layout()
        plt.show()
        
        print(f"\nStatistics for {field_name} in region:")
        print(f"Maximum value: {np.max(field_masked):.6f}")
        print(f"Mean value: {np.mean(field_masked):.6f}")
        print(f"Standard deviation: {np.std(field_masked):.6f}")
        print(f"Number of points in region: {np.sum(mask)}")
    
    print("\nAnalyzing tau distribution:")
    analyze_region(max_tau_pos, tau_norms, 'tau')
    
    print("\nAnalyzing N1 distribution:")
    analyze_region(max_N1_pos, np.abs(N1), 'N1')
    
    print("\nPosition of maxima:")
    print(f"tau max position: x={max_tau_pos[0]:.3f}, y={max_tau_pos[1]:.3f}")
    print(f"N1 max position: x={max_N1_pos[0]:.3f}, y={max_N1_pos[1]:.3f}")
    
    return max_tau_pos, max_N1_pos

def analyze_stress_distribution_comparison(vtk_files, x_limits, radius=0.02):
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
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    colors = ['blue', 'red']
    markers = ['o', 's']
    
    # Plot tau distributions
    for i, result in enumerate(results):
        max_pos = result['max_tau_pos']
        distances = np.sqrt((result['x'] - max_pos[0])**2 + 
                          (result['y'] - max_pos[1])**2)
        mask = distances <= radius
        
        ax1.scatter(distances[mask], result['tau'][mask], 
                   alpha=0.3, c=colors[i], marker=markers[i],
                   label=f"Mesh size: {result['mesh_size']}")
        
        scatter = ax2.scatter(result['x'][mask], result['y'][mask],
                            c=result['tau'][mask], cmap='viridis',
                            marker=markers[i], alpha=0.5)
        ax2.plot(max_pos[0], max_pos[1], '*', color=colors[i],
                markersize=15, label=f"Max ({result['mesh_size']} cells)")
    
    # Plot N1 distributions
    for i, result in enumerate(results):
        max_pos = result['max_N1_pos']
        distances = np.sqrt((result['x'] - max_pos[0])**2 + 
                          (result['y'] - max_pos[1])**2)
        mask = distances <= radius
        
        ax3.scatter(distances[mask], result['N1'][mask],
                   alpha=0.3, c=colors[i], marker=markers[i],
                   label=f"Mesh size: {result['mesh_size']}")
        
        scatter = ax4.scatter(result['x'][mask], result['y'][mask],
                            c=result['N1'][mask], cmap='viridis',
                            marker=markers[i], alpha=0.5)
        ax4.plot(max_pos[0], max_pos[1], '*', color=colors[i],
                markersize=15, label=f"Max ({result['mesh_size']} cells)")
    
    ax1.set_xlabel('Distance from maximum')
    ax1.set_ylabel('tau')
    ax1.set_title('tau vs Distance from Maximum')
    ax1.grid(True)
    ax1.legend()
    
    ax2.set_xlabel('X Position')
    ax2.set_ylabel('Y Position')
    ax2.set_title('Spatial Distribution of tau')
    plt.colorbar(scatter, ax=ax2, label='tau')
    ax2.grid(True)
    ax2.legend()
    
    ax3.set_xlabel('Distance from maximum')
    ax3.set_ylabel('N1')
    ax3.set_title('N1 vs Distance from Maximum')
    ax3.grid(True)
    ax3.legend()
    
    ax4.set_xlabel('X Position')
    ax4.set_ylabel('Y Position')
    ax4.set_title('Spatial Distribution of N1')
    plt.colorbar(scatter, ax=ax4, label='N1')
    ax4.grid(True)
    ax4.legend()
    
    plt.tight_layout()
    plt.show()
    
    # Print comparison statistics
    print("\nComparison Statistics:")
    for result in results:
        print(f"\nMesh size: {result['mesh_size']} cells")
        print(f"tau max: {result['max_tau_val']:.6f} at x={result['max_tau_pos'][0]:.6f}, y={result['max_tau_pos'][1]:.6f}")
        print(f"N1 max: {result['max_N1_val']:.6f} at x={result['max_N1_pos'][0]:.6f}, y={result['max_N1_pos'][1]:.6f}")
