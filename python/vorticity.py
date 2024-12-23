import numpy as np
from scipy.interpolate import griddata
from scipy.signal import find_peaks
from geometry import *
from process_data import *


def calculate_vorticity(points, U):

    geometry = get_channel_boundaries(points)
    x_transition = geometry['transition_x']
    
    x = points[:,0]
    y = points[:,1]
    
    n_grid = 400 
    margin = 0.02  
    
    x_min, x_max = x.min() + margin*(x.max()-x.min()), x.max() - margin*(x.max()-x.min())
    y_min, y_max = y.min() + margin*(y.max()-y.min()), y.max() - margin*(y.max()-y.min())
    
    xi = np.linspace(x_max, x_min, n_grid)  # Right to left
    yi = np.linspace(y_min, y_max, n_grid)
    X, Y = np.meshgrid(xi, yi)
    
    U_x = griddata((x, y), U[:,0], (X, Y), method='cubic', fill_value=0)
    U_y = griddata((x, y), U[:,1], (X, Y), method='cubic', fill_value=0)
    
    dx = xi[1] - xi[0]
    dy = yi[1] - yi[0]
    
    # Central difference for interior points
    dudy = np.zeros_like(U_x)
    dvdx = np.zeros_like(U_x)
    
    # Interior points - 4th order central differences
    dudy[2:-2,2:-2] = (-U_x[4:,2:-2] + 8*U_x[3:-1,2:-2] - 8*U_x[1:-3,2:-2] + U_x[:-4,2:-2])/(12*dy)
    dvdx[2:-2,2:-2] = (-U_y[2:-2,4:] + 8*U_y[2:-2,3:-1] - 8*U_y[2:-2,1:-3] + U_y[2:-2,:-4])/(12*dx)
    
    # Edge points - 2nd order central differences
    dudy[1:-1,[0,-1]] = (U_x[2:,[0,-1]] - U_x[:-2,[0,-1]])/(2*dy)
    dvdx[[0,-1],1:-1] = (U_y[[0,-1],2:] - U_y[[0,-1],:-2])/(2*dx)
    
    vorticity = dvdx - dudy
    
    channel_mask = ((X >= x_transition) & (np.abs(Y) <= geometry['small_height']/2)) | \
                  ((X < x_transition) & (np.abs(Y) <= geometry['large_height']/2))
    vorticity[~channel_mask] = 0
    
    point_vorticity = griddata((X.flatten(), Y.flatten()), 
                             vorticity.flatten(),
                             (x, y),
                             method='cubic',
                             fill_value=0)
    
    return point_vorticity, (X, Y, vorticity), geometry

def analyze_vorticity_field(points, U, debug=True):
    """
    Analyze the vorticity field and return key metrics.
    
    Parameters:
    -----------
    points : array-like
        Point coordinates
    U : array-like
        Velocity field
    debug : bool
        Whether to print debug information
        
    Returns:
    --------
    dict with analysis results
    """
    vorticity, grid_data, geometry = calculate_vorticity(points, U, debug)
    
    results = {
        'geometry': geometry,
        'statistics': {
            'max_magnitude': np.max(np.abs(vorticity)),
            'mean_magnitude': np.mean(np.abs(vorticity)),
            'std': np.std(vorticity)
        },
        'vorticity': vorticity,
        'grid_data': grid_data
    }
    
    if debug:
        print("\nVorticity statistics:")
        for key, value in results['statistics'].items():
            print(f"{key}: {value:.3e}")
            
    return results

def identify_vortex_centers(points, U):
    vorticity, (X, Y, vort_grid), geometry = calculate_vorticity(points, U)
    
    # Find local extrema in vorticity field
    peaks = []
    threshold = 0.1 * np.max(np.abs(vort_grid))
    
    for j in range(1, vort_grid.shape[0]-1):
        for i in range(1, vort_grid.shape[1]-1):
            if abs(vort_grid[j,i]) > threshold:
                neighborhood = vort_grid[j-1:j+2, i-1:i+2]
                if abs(vort_grid[j,i]) == np.max(np.abs(neighborhood)):
                    peaks.append((X[j,i], Y[j,i], abs(vort_grid[j,i])))
    
    # Sort by strength and take top 4
    peaks.sort(key=lambda x: x[2], reverse=True)
    peaks = peaks[:4]
    
    centers = np.array([[p[0], p[1]] for p in peaks])
    strengths = np.array([p[2] for p in peaks])
    
    return {
        'centers': centers,
        'vorticity': vorticity,
        'strengths': strengths,
        'grid_data': (X, Y, vort_grid)
    }

def calculate_vortex_size(points, U, center_point):
    """Calculate dimensionless vortex size X_r = x_r/d"""
    x = points[:,0]
    y = points[:,1]
    
    y_center = center_point[1]
    y_tolerance = (y.max() - y.min()) * 0.01
    horizontal_slice = np.abs(y - y_center) < y_tolerance
    
    x_slice = x[horizontal_slice]
    u_slice = U[horizontal_slice,0]
    
    # Sort points
    sort_idx = np.argsort(x_slice)
    x_sorted = x_slice[sort_idx]
    u_sorted = u_slice[sort_idx]
    
    # Find zero crossings
    zero_crossings = np.where(np.diff(np.signbit(u_sorted)))[0]
    
    if len(zero_crossings) >= 2:
        # Get first and last crossing
        x_start = x_sorted[zero_crossings[0]]
        x_end = x_sorted[zero_crossings[-1]]
        length = abs(x_end - x_start)
        
        # Note: should divide by d (characteristic length) 
        # to get dimensionless X_r
        return length
    
    return 0.0

def calculate_vortex_intensity(points, U, center_point):

    x = points[:,0]
    y = points[:,1]
    
    # Create regular grid around vortex center
    x_center, y_center = center_point
    span = max(abs(x.max() - x.min()), abs(y.max() - y.min())) * 0.2
    
    # Make grid more dense close to vortex center
    n_points = 100
    x_grid = np.linspace(x_center - span, x_center + span, n_points)
    y_grid = np.linspace(y_center - span, y_center + span, n_points)
    X, Y = np.meshgrid(x_grid, y_grid)
    
    # Interpolate velocities with linear method instead of cubic
    # to avoid potential instabilities
    U_x = griddata((x, y), U[:,0], (X, Y), method='linear', fill_value=0)
    U_y = griddata((x, y), U[:,1], (X, Y), method='linear', fill_value=0)
    
    # Calculate streamfunction using trapezoidal integration
    dx = x_grid[1] - x_grid[0]
    dy = y_grid[1] - y_grid[0]
    
    psi = np.zeros_like(X)
    
    # Integrate in both directions and take average
    psi_x = np.zeros_like(X)
    psi_y = np.zeros_like(X)
    
    # Integrate dψ/dx = -v
    for i in range(n_points):
        psi_x[:,i] = -np.cumsum(U_y[:,i]) * dy
        
    # Integrate dψ/dy = u
    for j in range(n_points):
        psi_y[j,:] = np.cumsum(U_x[j,:]) * dx
        
    # Average both integrations
    psi = (psi_x + psi_y) / 2.0
    
    # Remove mean to ensure consistent reference level
    psi = psi - np.mean(psi)
    
    return np.max(np.abs(psi))

def calculate_vortex_metrics(vortex_data, points, U, d=1.0, Q_inlet=1.0):

    metrics = []
    
    for i, center in enumerate(vortex_data['centers']):
        X_r = calculate_vortex_size(points, U, center) / d
        psi_r = calculate_vortex_intensity(points, U, center) / Q_inlet
        
        metrics.append({
            'X_r': X_r,
            'psi_r': psi_r,
            'center': center,
            'strength': vortex_data['strengths'][i]
        })
    
    return metrics

def plot_vorticity_field(points, U):

    vorticity, (X, Y, vort_grid), geometry = calculate_vorticity(points, U)
    x_transition = geometry['transition_x']
    
    plt.figure(figsize=(12, 4))
    plt.pcolormesh(X, Y, vort_grid, cmap='RdBu_r', 
                  shading='auto', 
                  vmin=-30, vmax=30)
    
    # Create uniform grid for streamplot
    nx, ny = 100, 50
    
    x_min, x_max = np.min(X), np.max(X)
    y_min, y_max = np.min(Y), np.max(Y)
    
    # Add margins
    margin_x = (x_max - x_min) * 0.05  
    margin_y = (y_max - y_min) * 0.05
    
    x_stream = np.linspace(x_min + margin_x, x_max - margin_x, nx)
    y_stream = np.linspace(y_min + margin_y, y_max - margin_y, ny)
    X_stream, Y_stream = np.meshgrid(x_stream, y_stream)
    
    # Channel mask
    channel_mask = ((X_stream >= x_transition) & (np.abs(Y_stream) <= geometry['small_height']/2)) | \
                  ((X_stream < x_transition) & (np.abs(Y_stream) <= geometry['large_height']/2))
    
    # Interpolate velocities
    U_x = griddata((points[:,0], points[:,1]), U[:,0], (X_stream, Y_stream))
    U_y = griddata((points[:,0], points[:,1]), U[:,1], (X_stream, Y_stream))
    U_x[~channel_mask] = np.nan
    U_y[~channel_mask] = np.nan
    
    x_step_exp = 4
    x_step_straight = 8
    y_step = 4
    
    start_points = []
    x_bounds = (x_min + margin_x, x_max - margin_x)
    y_bounds = (y_min + margin_y, y_max - margin_y)
    
    for i in range(0, len(x_stream)):
        x = x_stream[i]
        if x < x_bounds[0] or x > x_bounds[1]:
            continue
            
        step = x_step_exp if 0.1 <= x <= 0.3 else x_step_straight
        
        if i % step != 0:
            continue
            
        for j in range(0, len(y_stream), y_step):
            y = y_stream[j]
            if y < y_bounds[0] or y > y_bounds[1]:
                continue
                
            if ((x >= x_transition and abs(y) <= geometry['small_height']/2 - margin_y) or
                (x < x_transition and abs(y) <= geometry['large_height']/2 - margin_y)):
                start_points.append([x, y])
    
    start_points = np.array(start_points)
    
    if len(start_points) > 0:  # Only plot if we have valid start points
        plt.streamplot(x_stream, y_stream, U_x, U_y,
                      color='black',
                      linewidth=0.5,
                      arrowsize=0.5,
                      start_points=start_points)
    
    # Add colorbar
    cbar = plt.colorbar(fraction=0.02, pad=0.04)
    cbar.set_label('Vorticity', rotation=270, labelpad=10)
    
    plt.xlabel('X Position')
    plt.ylabel('Y Position')
    plt.title('Vorticity Field with Streamlines')
    plt.axis('equal')
    plt.grid(True, alpha=0.2)
    plt.tight_layout()
    plt.show()