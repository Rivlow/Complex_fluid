import numpy as np
import matplotlib.pyplot as plt
from vorticity import *

def richardson_extrapolation(phi1, phi2, phi3, h1, h2, h3):
 
    eps = 1e-10  # avoid divisin by 0
    if abs(phi2 - phi1) < eps:
        return float('inf'), phi3, float('nan')
        
    ratio = (phi3 - phi2)/(phi2 - phi1)
    if ratio <= 0:  # Non-monotonic convergence
        return float('inf'), phi3, float('nan')
    
    # Calculate observed order using non-uniform mesh ratios
    r21 = h2/h1
    r32 = h3/h2
    
    try:
        # Iterative method to find p
        p_old = 1.0  # Initial guess
        for _ in range(20):  # Max iterations
            F = np.log((phi3 - phi2)/(phi2 - phi1)) + p_old*np.log(r21/r32)
            dF = np.log(r21/r32)
            p_new = p_old - F/dF
            
            if abs(p_new - p_old) < 1e-6:
                p = p_new
                break   
            p_old = p_new
        else:
            return float('inf'), phi3, float('nan')
    except:
        return float('inf'), phi3, float('nan')
    
    # Protect against non-physical values
    if p > 10:  # p > 10 suggests something's wrong
        return float('inf'), phi3, float('nan')
    
    # Calculate extrapolated value
    phi_exact = phi3 + (phi3 - phi2)/(r32**p - 1)
    
    # Calculate GCI (Grid Convergence Index)
    Fs = 1.25  # Safety factor for three grids
    if abs(phi1) < eps:
        GCI = float('nan')
    else:
        GCI = Fs * abs((phi2 - phi1)/(r21**p - 1)) / abs(phi1) * 100 
    
    return p, phi_exact, GCI

def calculate_vortex_metrics(vortex_data, points, U, d=1.0, Q_inlet=1.0):
    """
    Calcule les métriques pour chaque vortex identifié en utilisant le traitement parallèle.
    
    Parameters:
    -----------
    vortex_data : dict
        Dictionnaire contenant les centres des vortex et leurs forces
    points : array
        Coordonnées des points
    U : array
        Champ de vitesse
    d : float
        Dimension caractéristique
    Q_inlet : float
        Débit d'entrée de référence
        
    Returns:
    --------
    list[dict]
        Liste des métriques pour chaque vortex
    """
    analyzer = AdaptiveVortexAnalysis(points, U)
    
    def process_vortex(args):
        center, points, U, d, Q_inlet = args
        # Utilise les méthodes de la classe AdaptiveVortexAnalysis
        X_r = analyzer.calculate_vortex_size(center) / d
        psi_r = calculate_vortex_intensity(points, U, center) / Q_inlet
        return {'X_r': X_r, 'psi_r': psi_r, 'center': center}
    
    # Prépare les arguments pour le traitement parallèle
    args = [(center, points, U, d, Q_inlet) 
            for center in vortex_data['centers']]
    
    # Traite les vortex en parallèle
    with ThreadPoolExecutor(max_workers=4) as executor:
        metrics = list(executor.map(process_vortex, args))
    
    # Ajoute les forces aux métriques
    for metric, strength in zip(metrics, vortex_data['strengths']):
        metric['strength'] = strength
    
    return metrics

def analyze_mesh_convergence(mesh_data_dict):
    results = []
    mesh_sequence = ['mesh_coarse', 'mesh_medium_mid', 'mesh_best']
    
    print("\nMesh information:")
    print("-" * 50)
    for name in mesh_sequence:
        n_elements = len(mesh_data_dict[name]['points'])
        h = 1.0/np.sqrt(n_elements)
        print(f"{name:15s}: {n_elements:8d} elements (h = {h:.6f})")
    print("-" * 50)
    
    # Characteristic mesh sizes (h = 1/sqrt(N))
    h1 = 1.0/np.sqrt(len(mesh_data_dict['mesh_coarse']['points']))
    h2 = 1.0/np.sqrt(len(mesh_data_dict['mesh_medium_mid']['points']))
    h3 = 1.0/np.sqrt(len(mesh_data_dict['mesh_best']['points']))
    
    r21 = h2/h1
    r32 = h3/h2
    print(f"\nRefinement ratios: r21 = {r21:.3f}, r32 = {r32:.3f}")
    
    # Initialize analyzers for each mesh
    analyzers = {}
    metrics_by_mesh = {}
    
    for mesh_name in mesh_sequence:
        data = mesh_data_dict[mesh_name]
        # Create analyzer instance for this mesh
        analyzers[mesh_name] = AdaptiveVortexAnalysis(data['points'], data['U'])
        # Get vortex data using the analyzer
        vortex_data = analyzers[mesh_name].identify_vortex_centers()
        # Calculate metrics
        metrics = calculate_vortex_metrics(vortex_data, data['points'], data['U'])
        metrics_by_mesh[mesh_name] = metrics
    
    # Convergence for each vortex metric
    for j in range(min(len(metrics_by_mesh['mesh_coarse']), 4)):  # Up to 4 vortices
        try:
            # 1) Vortex size
            phi1 = metrics_by_mesh['mesh_coarse'][j]['X_r']
            phi2 = metrics_by_mesh['mesh_medium_mid'][j]['X_r']
            phi3 = metrics_by_mesh['mesh_best'][j]['X_r']
            
            p, phi_exact, GCI = richardson_extrapolation(phi1, phi2, phi3, h1, h2, h3)
            
            results.append({
                'vortex_id': j+1,
                'metric': 'X_r',
                'values': [phi1, phi2, phi3],
                'mesh_sizes': [h1, h2, h3],
                'order': p,
                'extrapolated': phi_exact,
                'GCI': GCI
            })
            
            # 2) Vortex intensity
            phi1 = metrics_by_mesh['mesh_coarse'][j]['psi_r']
            phi2 = metrics_by_mesh['mesh_medium_mid'][j]['psi_r']
            phi3 = metrics_by_mesh['mesh_best'][j]['psi_r']
            
            p, phi_exact, GCI = richardson_extrapolation(phi1, phi2, phi3, h1, h2, h3)
            
            results.append({
                'vortex_id': j+1,
                'metric': 'psi_r',
                'values': [phi1, phi2, phi3],
                'mesh_sizes': [h1, h2, h3],
                'order': p,
                'extrapolated': phi_exact,
                'GCI': GCI
            })
            
        except Exception as e:
            print(f"Error analyzing vortex {j+1}: {str(e)}")
            continue
    
    return results



def print_convergence_results(results, output_file=None):
    """
    Print convergence analysis results to both console and optionally to a file
    
    Parameters:
    -----------
    results : list
        List of convergence results dictionaries
    output_file : str, optional
        Path to output file. If provided, results are also written to this file
    """
    # Function to write formatted output to both console and file
    def write_output(file_obj, text):
        print(text)
        if file_obj:
            file_obj.write(text + '\n')
    
    # Open file if path provided
    f = open(output_file, 'w') if output_file else None
    
    try:
        # Group results by vortex_id
        vortex_ids = sorted(set(r['vortex_id'] for r in results))
        
        header = "\nConvergence Analysis Results"
        separator = "-" * 80
        column_headers = f"{'Vortex':^10} {'Metric':^10} {'Order':^10} {'Extrap':^12} {'GCI (%)':^10}"
        
        write_output(f, header)
        write_output(f, separator)
        write_output(f, column_headers)
        write_output(f, separator)
        
        # Print results for each result entry
        for result in results:
            row = (f"{result['vortex_id']:^10d} "
                  f"{result['metric']:^10s} "
                  f"{result['order']:^10.3f} "
                  f"{result['extrapolated']:^12.3f} "
                  f"{result['GCI']:^10.2f}")
            write_output(f, row)
    
    finally:
        if f:
            f.close()
            

def plot_convergence(mesh_data_dict, save, prefix):
   
    mesh_sizes = [len(data['points']) for data in mesh_data_dict.values()]
    
    # 1. Velocity Convergence
    vel_stats = {'mean': [], 'max': []}
    for data in mesh_data_dict.values():
        U = data['U']
        vel_mag = np.sqrt(np.sum(U**2, axis=1))
        vel_stats['mean'].append(np.mean(vel_mag))
        vel_stats['max'].append(np.max(vel_mag))
    
    plt.figure(figsize=(10, 6))
    plt.plot(mesh_sizes, vel_stats['mean'], 'bo-', label='Mean velocity')
    plt.plot(mesh_sizes, vel_stats['max'], 'rs-', label='Max velocity')
    plt.xlabel('Number of Mesh Elements')
    plt.ylabel('Velocity Magnitude')
    plt.xscale('log')
    plt.yscale('log')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.title('Velocity Convergence')
    plt.tight_layout()
    if save:
        plt.savefig(f'{prefix}velocity.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # 2. Vorticity Convergence
    plt.figure(figsize=(10, 6))
    vort_stats = {'mean': [], 'max': []}
    for data in mesh_data_dict.values():
        analyzer = AdaptiveVortexAnalysis(points, U)
        vorticity, (X, Y, vort_grid) = analyzer.calculate_vorticity()
        vort_stats['mean'].append(np.mean(np.abs(vorticity)))
        vort_stats['max'].append(np.max(np.abs(vorticity)))
    
    plt.plot(mesh_sizes, vort_stats['mean'], 'bo-', label='Mean vorticity')
    plt.plot(mesh_sizes, vort_stats['max'], 'rs-', label='Max vorticity')
    plt.xlabel('Number of Mesh Elements')
    plt.ylabel('Vorticity Magnitude')
    plt.xscale('log')
    plt.yscale('log')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.title('Vorticity Convergence')
    plt.tight_layout()
    if save:
        plt.savefig(f'{prefix}vorticity.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # 3. Stress Convergence
    plt.figure(figsize=(10, 6))
    stress_stats = {
        'normal_stress_xx': {'l2_norm': []},
        'normal_stress_yy': {'l2_norm': []},
        'shear_stress_xy': {'l2_norm': [], 'wall_stress': []}
    }
    
    for data in mesh_data_dict.values():
        points = data['points']
        x, y = points[:,0], points[:,1]
        tau = data['tau']
        
        tau_xx = tau[:,0]
        tau_yy = tau[:,1]
        tau_xy = tau[:,3]
        
        geometry = get_channel_boundaries(points)
        
        stress_stats['normal_stress_xx']['l2_norm'].append(np.sqrt(np.mean(tau_xx**2)))
        stress_stats['normal_stress_yy']['l2_norm'].append(np.sqrt(np.mean(tau_yy**2)))
        stress_stats['shear_stress_xy']['l2_norm'].append(np.sqrt(np.mean(tau_xy**2)))
        
        margin = 0.1 * geometry['small_height']
        wall_points = np.abs(np.abs(y) - geometry['large_height']/2) < margin
        stress_stats['shear_stress_xy']['wall_stress'].append(np.mean(np.abs(tau_xy[wall_points])))
    
    styles = {
        'normal_stress_xx': {'color': 'blue', 'marker': 'o', 'label': 'τxx L2 norm'},
        'normal_stress_yy': {'color': 'red', 'marker': 's', 'label': 'τyy L2 norm'},
        'shear_stress_xy': {
            'l2_norm': {'color': 'green', 'marker': '^', 'label': 'τxy L2 norm'},
            'wall_stress': {'color': 'green', 'marker': 'D', 'label': 'τxy wall stress'}
        }
    }
    
    for component, metrics in stress_stats.items():
        if component != 'shear_stress_xy':
            plt.plot(mesh_sizes, metrics['l2_norm'], 
                    marker=styles[component]['marker'],
                    color=styles[component]['color'],
                    label=styles[component]['label'])
        else:
            plt.plot(mesh_sizes, metrics['l2_norm'],
                    marker=styles[component]['l2_norm']['marker'],
                    color=styles[component]['l2_norm']['color'],
                    label=styles[component]['l2_norm']['label'])
            plt.plot(mesh_sizes, metrics['wall_stress'],
                    marker=styles[component]['wall_stress']['marker'],
                    color=styles[component]['wall_stress']['color'],
                    label=styles[component]['wall_stress']['label'])
    
    plt.xlabel('Number of Mesh Elements')
    plt.ylabel('Stress Metrics')
    plt.xscale('log')
    plt.yscale('log')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.title('Stress Convergence')
    plt.tight_layout()
    if save:
        plt.savefig(f'{prefix}stress.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    return {'velocity': vel_stats, 
            'vorticity': vort_stats, 
            'stress': stress_stats}