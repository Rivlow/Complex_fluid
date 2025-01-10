from process_data import *
import os
import numpy as np
import matplotlib.pyplot as plt
from vorticity import *

def plot_velocity_contours(pos, U, n_lines=20, save_path=None):
    """
    Crée un plot des lignes de courant avec matplotlib
    """
    import matplotlib.pyplot as plt
    from scipy.interpolate import griddata
    
    # Créer une grille régulière pour l'interpolation
    x_unique = np.linspace(pos[:,0].min(), pos[:,0].max(), 200)
    y_unique = np.linspace(pos[:,1].min(), pos[:,1].max(), 100)
    X, Y = np.meshgrid(x_unique, y_unique)
    
    # Interpoler U_x et U_y sur la grille régulière
    U_x = griddata((pos[:,0], pos[:,1]), U[:,0], (X, Y), method='cubic')
    U_y = griddata((pos[:,0], pos[:,1]), U[:,1], (X, Y), method='cubic')
    
    # Créer le plot
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Tracer les streamlines
    ax.streamplot(X, Y, U_x, U_y, 
                 density=1.5,
                 color='black',
                 linewidth=0.5,
                 arrowsize=0.5)
    
    # Configurer le plot
    ax.set_aspect('equal')
    ax.grid(False)
    plt.xlabel('x')
    plt.ylabel('y')
    
    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=300)
    else:
        plt.show()

def plot_wall_pressure(pos, p, save_path=None):
    """
    Plot la distribution de pression sur les parois supérieure et inférieure
    
    Args:
        pos: positions (x,y,z)
        p: pression
        save_path: chemin pour sauvegarder l'image (optionnel)
    """
    import matplotlib.pyplot as plt
    
    y_min, y_max = pos[:,1].min(), pos[:,1].max()
    tol = 1e-6  # htreshold value
    
    bottom_wall = np.abs(pos[:,1] - y_min) < tol
    top_wall = np.abs(pos[:,1] - y_max) < tol
    
    x_bottom = pos[bottom_wall,0]
    p_bottom = p[bottom_wall]
    sort_idx = np.argsort(x_bottom)
    x_bottom = x_bottom[sort_idx]
    p_bottom = p_bottom[sort_idx]
    
    x_top = pos[top_wall,0]
    p_top = p[top_wall]
    sort_idx = np.argsort(x_top)
    x_top = x_top[sort_idx]
    p_top = p_top[sort_idx]
    
    plt.figure(figsize=(12, 6))
    
    plt.plot(x_bottom, p_bottom, 'b-o', label='lower wall', 
             markersize=6, markevery=5)  
    
    plt.plot(x_top, p_top, 'r-s', label='upper wall', 
             markersize=3, markevery=5) 
    
    plt.xlabel('Position x')
    plt.ylabel('Pression')
    plt.title('Distribution de pression sur les parois')
    plt.legend()
    plt.grid(True)
    
    if save_path:
        plt.savefig(save_path)
    else:
        plt.show()


def main():

    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_path = os.path.join(base_path, 'openfoam_container', 'output', 
                              'newtonian')

    all_data = load_vtk_data(output_path, verbose=False)
    Re_100 = all_data[1]

    pos, U, p = extractData(Re_100)

    plot_velocity_contours(pos, U, )
    plot_wall_pressure(pos, p)




if __name__ == "__main__":
    main()