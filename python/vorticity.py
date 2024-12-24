import numpy as np
from scipy.interpolate import griddata
from scipy.signal import find_peaks
from geometry import *
from process_data import *
from concurrent.futures import ThreadPoolExecutor

class AdaptiveVortexAnalysis:
    def __init__(self, points, U):
        self.points = points
        self.U = U
        self.geometry = get_channel_boundaries(points)
        
        # Calculate characteristic dimensions
        self.d = self.geometry['small_height']  # Inlet height
        self.D = self.geometry['large_height']  # Outlet height
        self.expansion_ratio = self.D / self.d
        
        # Adaptive parameters
        self._compute_adaptive_parameters()
        
    def _compute_adaptive_parameters(self):
        """Compute adaptive parameters based on geometry"""
        # 1. Stability margins
        self.margin = 0.02 * min(self.d, self.D)  # Scale with channel size
        
        # 2. Vortex detection parameters
        self.threshold_factor = 0.1 * (4/self.expansion_ratio)  # Adjust for expansion ratio
        
        # 3. Grid parameters
        length_scale = max(self.D, self.d)
        self.n_grid = int(400 * (self.expansion_ratio/4))  # Base grid scaled by expansion
        self.n_grid = min(800, max(200, self.n_grid))  # Keep within reasonable bounds
        
        # 4. Vortex size parameters
        self.y_tolerance = 0.01 * self.d  # Scale with inlet height

    def calculate_vorticity(self):
        """Calculate vorticity with adaptive parameters"""
        x, y = self.points[:, 0], self.points[:, 1]
        x_transition = self.geometry['transition_x']
        
        # Compute grid bounds with adaptive margins
        x_range = x.max() - x.min()
        y_range = y.max() - y.min()
        x_min = x.min() + self.margin * x_range
        x_max = x.max() - self.margin * x_range
        y_min = y.min() + self.margin * y_range
        y_max = y.max() - self.margin * y_range
        
        # Create adaptive grid
        xi = np.linspace(x_max, x_min, self.n_grid)
        yi = np.linspace(y_min, y_max, self.n_grid)
        X, Y = np.meshgrid(xi, yi)
        
        # Interpolate velocities with method selection based on position
        points_2d = np.column_stack((x, y))
        U_x = self._adaptive_interpolation(points_2d, self.U[:, 0], X, Y, x_transition)
        U_y = self._adaptive_interpolation(points_2d, self.U[:, 1], X, Y, x_transition)
        
        # Calculate derivatives with adaptive spacing
        dx = xi[1] - xi[0]
        dy = yi[1] - yi[0]
        
        dudy, dvdx = self._calculate_derivatives(U_x, U_y, dx, dy)
        vorticity = dvdx - dudy
        
        # Apply channel mask
        channel_mask = self._create_channel_mask(X, Y, x_transition)
        vorticity[~channel_mask] = 0
        
        # Interpolate back to original points
        point_vorticity = griddata((X.flatten(), Y.flatten()), 
                                 vorticity.flatten(),
                                 points_2d,
                                 method='linear')
        
        return point_vorticity, (X, Y, vorticity)

    def _adaptive_interpolation(self, points_2d, values, X, Y, x_transition):
        """Choose interpolation method based on position"""
        # Use linear interpolation near expansion, cubic elsewhere
        near_expansion = np.abs(X - x_transition) < self.d
        
        result = np.zeros_like(X)
        # Linear interpolation near expansion
        mask_linear = near_expansion
        result[mask_linear] = griddata(points_2d, values, 
                                     (X[mask_linear], Y[mask_linear]), 
                                     method='linear', 
                                     fill_value=0)
        
        # Cubic interpolation elsewhere
        mask_cubic = ~near_expansion
        result[mask_cubic] = griddata(points_2d, values, 
                                    (X[mask_cubic], Y[mask_cubic]), 
                                    method='cubic', 
                                    fill_value=0)
        
        return result

    def _calculate_derivatives(self, U_x, U_y, dx, dy):
        """Calculate derivatives with adaptive schemes"""
        dudy = np.zeros_like(U_x)
        dvdx = np.zeros_like(U_x)
        
        # Use 4th order central differences in smooth regions
        dudy[2:-2, 2:-2] = (-U_x[4:, 2:-2] + 8*U_x[3:-1, 2:-2] - 
                           8*U_x[1:-3, 2:-2] + U_x[:-4, 2:-2]) / (12*dy)
        dvdx[2:-2, 2:-2] = (-U_y[2:-2, 4:] + 8*U_y[2:-2, 3:-1] - 
                           8*U_y[2:-2, 1:-3] + U_y[2:-2, :-4]) / (12*dx)
        
        # Use 2nd order central differences near boundaries
        dudy[1:-1, [0,-1]] = (U_x[2:, [0,-1]] - U_x[:-2, [0,-1]]) / (2*dy)
        dvdx[[0,-1], 1:-1] = (U_y[[0,-1], 2:] - U_y[[0,-1], :-2]) / (2*dx)
        
        return dudy, dvdx

    def identify_vortex_centers(self):
        """Identify vortex centers with adaptive thresholding"""
        vorticity, (X, Y, vort_grid) = self.calculate_vorticity()
        
        # Adaptive threshold based on geometry
        threshold = self.threshold_factor * np.max(np.abs(vort_grid))
        
        # Enhanced peak detection
        peaks = self._find_peaks_2d(vort_grid, threshold)
        
        centers = []
        strengths = []
        for i, j in peaks:
            centers.append([X[i,j], Y[i,j]])
            strengths.append(abs(vort_grid[i,j]))
        
        # Sort by strength and take top 4
        centers = np.array(centers)
        strengths = np.array(strengths)
        if len(strengths) > 0:
            sort_idx = np.argsort(strengths)[-4:][::-1]
            centers = centers[sort_idx]
            strengths = strengths[sort_idx]
        
        return {
            'centers': centers,
            'vorticity': vorticity,
            'strengths': strengths,
            'grid_data': (X, Y, vort_grid)
        }

    def _create_channel_mask(self, X, Y, x_transition):
        """Crée un masque pour identifier les points à l'intérieur du canal"""
        return ((X >= x_transition) & (np.abs(Y) <= self.geometry['small_height']/2)) | \
               ((X < x_transition) & (np.abs(Y) <= self.geometry['large_height']/2))

    def _find_peaks_2d(self, data, threshold):
        """Enhanced 2D peak detection"""
        peaks = []
        for i in range(1, data.shape[0]-1):
            for j in range(1, data.shape[1]-1):
                if abs(data[i,j]) > threshold:
                    patch = data[i-1:i+2, j-1:j+2]
                    if abs(data[i,j]) == np.max(np.abs(patch)):
                        peaks.append((i,j))
        return peaks

    def calculate_vortex_size(self, center_point):
        """Calculate vortex size with adaptive tolerance"""
        x = self.points[:,0]
        y = self.points[:,1]
        
        # Adaptive slice selection
        horizontal_slice = np.abs(y - center_point[1]) < self.y_tolerance
        
        x_slice = x[horizontal_slice]
        u_slice = self.U[horizontal_slice,0]
        
        if len(x_slice) < 2:
            return 0.0
            
        sort_idx = np.argsort(x_slice)
        x_sorted = x_slice[sort_idx]
        u_sorted = u_slice[sort_idx]
        
        # Find zero crossings with adaptive interpolation
        zero_crossings = np.where(u_sorted[:-1] * u_sorted[1:] <= 0)[0]
        
        if len(zero_crossings) >= 2:
            # Linear interpolation for each crossing
            crossings = []
            for idx in zero_crossings:
                x0, x1 = x_sorted[idx:idx+2]
                u0, u1 = u_sorted[idx:idx+2]
                if u1 - u0 != 0:  # Avoid division by zero
                    x_cross = x0 - u0 * (x1 - x0) / (u1 - u0)
                    crossings.append(x_cross)
            
            if len(crossings) >= 2:
                return abs(crossings[-1] - crossings[0])
        
        return 0.0



def calculate_vortex_intensity(points, U, center_point):

    x = points[:,0]
    y = points[:,1]
    
    x_center, y_center = center_point
    span = max(abs(x.max() - x.min()), abs(y.max() - y.min())) * 0.2
    
    # Optimized grid creation
    n_points = 100
    x_grid = np.linspace(x_center - span, x_center + span, n_points)
    y_grid = np.linspace(y_center - span, y_center + span, n_points)
    X, Y = np.meshgrid(x_grid, y_grid)
    points_2d = np.column_stack((x, y))
    
    # Interpolate velocities in one pass
    U_x = griddata(points_2d, U[:,0], (X, Y), method='linear', fill_value=0)
    U_y = griddata(points_2d, U[:,1], (X, Y), method='linear', fill_value=0)
    
    dx = x_grid[1] - x_grid[0]
    dy = y_grid[1] - y_grid[0]
    
    # Vectorized integration using cumsum
    psi_x = -np.cumsum(U_y, axis=0) * dy
    psi_y = np.cumsum(U_x, axis=1) * dx
    
    # Compute streamfunction
    psi = (psi_x + psi_y) / 2.0
    psi -= np.mean(psi)
    
    return np.max(np.abs(psi))


def plot_vorticity_field(points, U, save, prefix):

    analyzer = AdaptiveVortexAnalysis(points, U)
    vorticity, (X, Y, vort_grid) = analyzer.calculate_vorticity()
    geometry = analyzer.geometry
    x_transition = geometry['transition_x']
    
    plt.figure(figsize=(12, 4))
    plt.pcolormesh(X, Y, vort_grid, cmap='RdBu_r', 
                  shading='auto', 
                  vmin=-10, vmax=10)
    
    # Optimized grid creation
    nx, ny = 2000, 1000
    margin_x = (X.max() - X.min()) * 0.05
    margin_y = (Y.max() - Y.min()) * 0.05
    
    x_stream = np.linspace(X.min() + margin_x, X.max() - margin_x, nx)
    y_stream = np.linspace(Y.min() + margin_y, Y.max() - margin_y, ny)
    X_stream, Y_stream = np.meshgrid(x_stream, y_stream)
    
    # Vectorized channel mask
    channel_mask = ((X_stream >= x_transition) & (np.abs(Y_stream) <= geometry['small_height']/2)) | \
                  ((X_stream < x_transition) & (np.abs(Y_stream) <= geometry['large_height']/2))
    
    # Interpolate velocities in one pass
    points_2d = np.column_stack((points[:,0], points[:,1]))
    U_x = griddata(points_2d, U[:,0], (X_stream, Y_stream))
    U_y = griddata(points_2d, U[:,1], (X_stream, Y_stream))
    U_x[~channel_mask] = np.nan
    U_y[~channel_mask] = np.nan
    
    # Optimized start points generation
    x_mesh, y_mesh = np.meshgrid(x_stream, y_stream)
    valid_x = (x_mesh >= X.min() + margin_x) & (x_mesh <= X.max() - margin_x)
    valid_y = (y_mesh >= Y.min() + margin_y) & (y_mesh <= Y.max() - margin_y)
    
    x_step = np.where((x_mesh[0] >= 0.1) & (x_mesh[0] <= 0.3), 4, 12)
    y_step = 4
    
    valid_points = valid_x & valid_y & \
                  ((x_mesh >= x_transition) & (np.abs(y_mesh) <= geometry['small_height']/2 - margin_y) | \
                   (x_mesh < x_transition) & (np.abs(y_mesh) <= geometry['large_height']/2 - margin_y))
    
    x_indices = np.arange(nx)
    y_indices = np.arange(ny)
    x_valid = x_indices[np.mod(x_indices, x_step) == 0]  
    y_valid = y_indices[np.mod(y_indices, y_step) == 0]
    
    X_start, Y_start = np.meshgrid(x_stream[x_valid], y_stream[y_valid])
    mask = valid_points[np.ix_(y_valid, x_valid)]
    start_points = np.column_stack((X_start[mask], Y_start[mask]))
    
    if len(start_points) > 0:
        plt.streamplot(x_stream, y_stream, U_x, U_y,
                      color='black',
                      linewidth=0.5,
                      arrowsize=0.5,
                      start_points=start_points)
    
    
    plt.xlabel('X Position')
    plt.ylabel('Y Position')
    plt.axis('equal')
    plt.grid(True, alpha=0.2)
    plt.tight_layout()

    if save:
        plt.savefig(f"{prefix}vorticity.png")
    plt.show()