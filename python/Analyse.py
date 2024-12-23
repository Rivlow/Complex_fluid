import numpy as np
import matplotlib.pyplot as plt
import pyvista as pv
from scipy.interpolate import griddata

def extract_vtk_data(vtk_file):
    # Lecture du fichier VTK
    mesh = pv.read(vtk_file)
    
    # Récupération des positions
    positions = np.array(mesh.points)
    
    # Conversion des vitesses des cellules aux points
    velocity_point = mesh.cell_data_to_point_data()
    velocities = np.array(velocity_point['U'])
    
    return positions, velocities

def plot_velocity_slice(positions, velocities, y_slice=0.0, tolerance=1e-4):
    """
    Trace la vitesse sur une tranche horizontale du canal
    
    Args:
        positions: coordonnées des points
        velocities: vecteurs vitesse
        y_slice: position y de la tranche
        tolerance: tolérance pour sélectionner les points proches de la tranche
    """
    # Sélection des points proches de la tranche
    mask = np.abs(positions[:, 1] - y_slice) < tolerance
    x_slice = positions[mask, 0]
    u_slice = velocities[mask, 0]  # vitesse x
    v_slice = velocities[mask, 1]  # vitesse y
    magnitude_slice = np.sqrt(u_slice**2 + v_slice**2)
    
    # Tri des points par position x
    sort_idx = np.argsort(x_slice)
    x_slice = x_slice[sort_idx]
    magnitude_slice = magnitude_slice[sort_idx]
    
    # Plot
    plt.figure(figsize=(12, 6))
    plt.plot(x_slice, magnitude_slice, 'b-', linewidth=2)
    plt.xlabel('x (m)')
    plt.ylabel('Magnitude de la vitesse (m/s)')
    plt.title(f'Profil de vitesse à y = {y_slice:.3f} m')
    plt.grid(True)
    plt.show()


def plot_velocity_2d_with_streamlines(positions, velocities, quiver_density=100, n_streamlines=20):
    """
    Trace le champ de vitesse avec des lignes de courant adaptatives
    """
    x = positions[:, 0]
    y = positions[:, 1]
    u = velocities[:, 0]
    v = velocities[:, 1]
    magnitude = np.sqrt(u**2 + v**2)
    
    # Création d'une grille plus fine pour une meilleure résolution
    xi = np.linspace(x.min(), x.max(), 200)
    yi = np.linspace(y.min(), y.max(), 100)
    xi_mesh, yi_mesh = np.meshgrid(xi, yi)
    
    # Interpolation avec une méthode plus robuste
    ui = griddata((x, y), u, (xi_mesh, yi_mesh), method='cubic', fill_value=0)
    vi = griddata((x, y), v, (xi_mesh, yi_mesh), method='cubic', fill_value=0)
    magnitude_i = griddata((x, y), magnitude, (xi_mesh, yi_mesh), method='cubic', fill_value=0)
    
    # Filtrage des vitesses très faibles pour réduire le bruit
    threshold = np.max(magnitude_i) * 0.01
    mask = magnitude_i < threshold
    ui[mask] = 0
    vi[mask] = 0
    
    # Plot
    fig, ax = plt.subplots(figsize=(15, 6))
    
    # Contour plot de la magnitude avec une échelle de couleur ajustée
    contour = ax.pcolormesh(xi_mesh, yi_mesh, magnitude_i, 
                           shading='auto', cmap='viridis',
                           norm=plt.Normalize(vmin=0, vmax=np.percentile(magnitude_i, 95)))
    plt.colorbar(contour, label='Magnitude de la vitesse (m/s)')
    
    # Définition des zones pour les streamlines
    x_central = (x.max() - x.min()) * 0.5 + x.min()
    x_width = (x.max() - x.min()) * 0.3
    
    # Streamlines avec densité adaptative
    for region in ['entrance', 'central', 'exit']:
        if region == 'central':
            mask_x = (xi >= x_central - x_width/2) & (xi <= x_central + x_width/2)
            density = 2.0
            linewidth = 1
        else:
            if region == 'entrance':
                mask_x = xi < x_central - x_width/2
            else:  # exit
                mask_x = xi > x_central + x_width/2
            density = 1.0
            linewidth = 0.5
            
        # Application du masque pour la région
        xi_region = xi[mask_x]
        if len(xi_region) > 0:  # Vérification que la région n'est pas vide
            ax.streamplot(xi, yi, ui, vi,
                         density=density,
                         color='white',
                         linewidth=linewidth,
                         arrowsize=1,
                         arrowstyle='->',
                         minlength=0.1)
    
    ax.set_aspect('equal')
    ax.set_xlabel('x (m)')
    ax.set_ylabel('y (m)')
    ax.set_title('Champ de vitesse avec lignes de courant adaptatives')
    
    plt.tight_layout()
    plt.show()

# Exemple d'utilisation
path = r"C:\Users\lucas\Unif\complex_fluids_and_non-newtonian_flows\Projet\openfoam_container\simulation\fene_p\contraction\actual\VTK\actual_196717.vtk"
positions, velocities = extract_vtk_data(path)

plot_velocity_2d_with_streamlines(positions, velocities, quiver_density=300)
plot_velocity_slice(positions, velocities, x_slice=0.2)