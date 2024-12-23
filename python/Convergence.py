import numpy as np
import matplotlib.pyplot as plt
from vorticity import *
import pyvista as pv

def analyze_mesh_convergence(mesh_data):
    results = {}
    
    for mesh_name, data in mesh_data.items():
        print(f"\nAnalyzing {mesh_name}:")
        try:
            
            vorticity, grid_data, geometry = calculate_vorticity(data['points'], data['U'])
            
            results[mesh_name] = {
                'vorticity_max': np.max(np.abs(vorticity)),
                'vorticity_mean': np.mean(np.abs(vorticity)),
                'geometry': geometry,
                'grid_data': grid_data
            }
            
            print(f"Max vorticity magnitude: {results[mesh_name]['vorticity_max']:.3e}")
            print(f"Mean vorticity magnitude: {results[mesh_name]['vorticity_mean']:.3e}")
            
        except Exception as e:
            print(f"Error analyzing {mesh_name}: {str(e)}")
            continue
    
    return results

def plot_convergence_metrics(results):
    mesh_names = list(results.keys())
    mesh_numbers = range(len(mesh_names))
    metrics = ['vorticity_max', 'vorticity_mean']
    
    plt.figure(figsize=(12, 6))
    for metric in metrics:
        values = [results[mesh][metric] for mesh in mesh_names]
        plt.plot(mesh_numbers, values, 'o-', label=metric.replace('_', ' ').title())
    
    plt.xlabel('Mesh Refinement Level')
    plt.ylabel('Value')
    plt.title('Convergence of Vorticity Metrics')
    plt.xticks(mesh_numbers, mesh_names, rotation=45)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

