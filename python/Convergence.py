import numpy as np
import pyvista as pv
import matplotlib.pyplot as plt

def safe_max(array):

    if len(array) == 0:
        return 0
    return np.max(array)

def analyze_mesh_convergence(vtk_file):

    print(f"Analyse of {vtk_file}...")
    mesh = pv.read(vtk_file)
    point_data = mesh.cell_data_to_point_data()
    
    x = mesh.points[:, 0]
    y = mesh.points[:, 1]
    print(f"Range x: [{x.min():.3f}, {x.max():.3f}]")
    print(f"Range y: [{y.min():.3f}, {y.max():.3f}]")
    
    x_mid = (x.max() + x.min()) / 2
    x_range = x.max() - x.min()
    contraction_width = x_range * 0.1
    
    entrance_mask = x < (x_mid - contraction_width/2)
    contraction_mask = (x >= (x_mid - contraction_width/2)) & (x <= (x_mid + contraction_width/2))
    exit_mask = x > (x_mid + contraction_width/2)
    
    for name, mask in [("entrance", entrance_mask), 
                      ("contraction", contraction_mask), 
                      ("exit", exit_mask)]:
        print(f"Points in the zone {name}: {np.sum(mask)}")
    
    tau = point_data['tau']
    U = point_data['U']
    N1 = point_data['N1']
    
    metrics = {}
    zones = {
        'entrance': entrance_mask,
        'contraction': contraction_mask,
        'exit': exit_mask
    }
    
    for zone_name, mask in zones.items():
        if np.any(mask):
            tau_norms = np.linalg.norm(tau[mask], axis=1)
            U_norms = np.linalg.norm(U[mask], axis=1)
            N1_values = np.abs(N1[mask])
            
            metrics[f'{zone_name}_tau_max'] = safe_max(tau_norms)
            metrics[f'{zone_name}_N1_max'] = safe_max(N1_values)
            metrics[f'{zone_name}_U_max'] = safe_max(U_norms)
        else:
            print(f"Warning: No points in the zone {zone_name}")
            metrics[f'{zone_name}_tau_max'] = 0
            metrics[f'{zone_name}_N1_max'] = 0
            metrics[f'{zone_name}_U_max'] = 0
    
    metrics['total_cells'] = mesh.n_cells
    print(f"Total numbber of cells : {metrics['total_cells']}")
    
    return metrics

def plot_convergence(ax, cell_counts, values, metric_name):

    main_color = '#1f77b4'
    fill_color = '#1f77b4'
    
    relative_errors = []
    for j in range(len(values)-1):
        if values[j] != 0:
            error = abs(values[j+1] - values[j]) / values[j] * 100
            relative_errors.append(error)
        else:
            relative_errors.append(float('nan'))
    
    ax.semilogx(cell_counts, values, 'o-', color=main_color, 
                label='Value', linewidth=2, zorder=3)
    
    margin = np.array(values) * 0.05
    ax.fill_between(cell_counts, 
                   np.array(values) - margin, 
                   np.array(values) + margin,
                   color=fill_color, alpha=0.2, zorder=2)
    
    ax.grid(True, linestyle='--', alpha=0.7, zorder=1)
    
    for j in range(len(relative_errors)):
        if not np.isnan(relative_errors[j]):

            log_x1, log_x2 = np.log10(cell_counts[j]), np.log10(cell_counts[j+1])
            mid_x = 10 ** ((log_x1 + log_x2) / 2)
            mid_y = (values[j] + values[j+1]) / 2
            
            bbox_props = dict(boxstyle="round,pad=0.3", fc="white", 
                            ec="gray", alpha=0.8)
            ax.annotate(f'{relative_errors[j]:.1f}%', 
                       xy=(mid_x, mid_y),
                       xytext=(0, 10),
                       textcoords='offset points',
                       ha='center',
                       va='bottom',
                       bbox=bbox_props,
                       zorder=4)
    
    ax.set_xlabel('Total number of cells')
    ax.set_ylabel(metric_name)
    ax.set_title(f'Convergence of {metric_name}')
    ax.margins(y=0.2)

def compare_meshes(vtk_files):

    all_metrics = []
    
    for file in vtk_files:
        try:
            metrics = analyze_mesh_convergence(file)
            all_metrics.append(metrics)
        except Exception as e:
            print(f"Error analyzing {file}: {str(e)}")
            continue
    
    if not all_metrics:
        print("No metrics could be calculated.")
        return
    
    all_metrics.sort(key=lambda x: x['total_cells'])
    cell_counts = [m['total_cells'] for m in all_metrics]
    
    metrics_to_plot = {
        'contraction_tau_max': 'Maximum Viscoelastic Stress',
        'contraction_N1_max': 'Maximum First Normal Stress Difference',
        'contraction_U_max': 'Maximum Velocity'
    }
    
    fig, axes = plt.subplots(len(metrics_to_plot), 1, 
                            figsize=(12, 4*len(metrics_to_plot)))
    if len(metrics_to_plot) == 1:
        axes = [axes]
    
    for i, (metric_key, metric_name) in enumerate(metrics_to_plot.items()):
        values = [m[metric_key] for m in all_metrics]
        plot_convergence(axes[i], cell_counts, values, metric_name)
    
    plt.tight_layout()
    plt.show()
    
    print("\nRelative errors between successive meshes:")
    for i in range(len(all_metrics)-1):
        print(f"\nBetween mesh with {all_metrics[i]['total_cells']} "
              f"and {all_metrics[i+1]['total_cells']} cells:")
        for key in all_metrics[0].keys():
            if key != 'total_cells':
                if all_metrics[i][key] != 0:
                    error = abs(all_metrics[i+1][key] - all_metrics[i][key]) / all_metrics[i][key] * 100
                    print(f"{key}: {error:.2f}%")
                else:
                    print(f"{key}: N/A (reference value = 0)")

path = "openfoam_container/output/fene_p/contraction/mesh_variation/all_mesh"
vtk_files = [
    f"{path}/mesh_1_1.vtk",
    f"{path}/mesh_3_4.vtk",
    f"{path}/mesh_2_3.vtk",
    f"{path}/mesh_1_2.vtk",
]

compare_meshes(vtk_files)