import matplotlib.pyplot as plt
import numpy as np
from mesh_analysis import analyze_mesh_convergence

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

def compare_meshes(vtk_files, x_limits):
    all_metrics = []
    
    for file in vtk_files:
        try:
            metrics = analyze_mesh_convergence(file, x_limits)
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
        'expansion_tau_max': 'Maximum Viscoelastic Stress',
        'expansion_N1_max': 'Maximum First Normal Stress Difference',
        'expansion_U_max': 'Maximum Velocity'
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