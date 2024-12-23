import numpy as np
import matplotlib.pyplot as plt
import pyvista as pv


def get_zone_boundaries(x, y, x_start, x_end):
    """Get upper and lower y boundaries for a zone between x_start and x_end"""
    mask = (x >= x_start) & (x <= x_end)
    if not np.any(mask):
        return [], []
    
    x_zone = x[mask]
    y_zone = y[mask]
    
    sort_idx = np.argsort(x_zone)
    x_zone = x_zone[sort_idx]
    y_zone = y_zone[sort_idx]
    
    x_unique = np.unique(x_zone)
    y_upper = []
    y_lower = []
    
    for x_pos in x_unique:
        mask_x = x_zone == x_pos
        y_upper.append(np.max(y_zone[mask_x]))
        y_lower.append(np.min(y_zone[mask_x]))
    
    return x_unique, np.array(y_upper), np.array(y_lower)

def plot_geometry(vtk_file, x_limits):
    mesh = pv.read(vtk_file)
    points = mesh.points
    x = -points[:, 0]
    y = points[:, 1]
    
    plt.figure(figsize=(12, 6))
    
    colors = {
        'entrance': 'blue',
        'expansion': 'red',
        'exit': 'green'
    }
    
    x_entrance_end, x_expansion_start, x_expansion_end, x_exit_start = x_limits
    
    for zone_name, (start, end) in [
        ('entrance', (x.min(), x_expansion_start)),
        ('expansion', (x_expansion_start, x_expansion_end)),
        ('exit', (x_expansion_end, x.max()))
    ]:
        x_zone, y_upper, y_lower = get_zone_boundaries(x, y, start, end)
        plt.fill_between(x_zone, y_lower, y_upper,
                        color=colors[zone_name], alpha=0.3, label=f'{zone_name} zone')
    
    plt.scatter(x, y, s=1, alpha=0.1, color='black')
    plt.grid(True)
    plt.xlabel('X Position')
    plt.ylabel('Y Position')
    plt.title('Geometry Visualization with Zones')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    print(f"Domain bounds:")
    print(f"X: [{x.min():.3f}, {x.max():.3f}]")
    print(f"Y: [{y.min():.3f}, {y.max():.3f}]")
    
    plt.tight_layout()
    plt.show()