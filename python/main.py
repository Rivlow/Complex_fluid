# main.py
import os
from geometry import plot_geometry
from mesh_analysis import analyze_mesh_convergence
from convergence import compare_meshes
from stress_analysis import analyze_stress_distribution, analyze_stress_distribution_comparison

def main():
    base_path = "openfoam_container/output/fene_p/contraction/mesh_variation/all_mesh"
    x_limits = (-0.3, -0.29, -0.1, -0.001)
    
    mesh_files = {
        "fine": f"{base_path}/mesh_1_1.vtk",
        "medium_fine": f"{base_path}/mesh_3_4.vtk",
        "medium": f"{base_path}/mesh_2_3.vtk",
        "coarse": f"{base_path}/mesh_1_2.vtk"
    }
    
    # 1. Geometry visualization with coarse mesh
    print("\n=== Visualizing geometry with zones ===")
    plot_geometry(mesh_files["coarse"], x_limits)
    
    # 2. Mesh convergence analysis
    print("\n=== Analyzing mesh convergence ===")
    ordered_meshes = [
        mesh_files["coarse"],
        mesh_files["medium"],
        mesh_files["medium_fine"],
        mesh_files["fine"]
    ]
    compare_meshes(ordered_meshes, x_limits)
    
    # 3. Compare stress distributions between coarse and fine meshes
    print("\n=== Stress distribution comparison between coarse and fine meshes ===")
    analyze_stress_distribution_comparison(
        [mesh_files["coarse"], mesh_files["fine"]], 
        x_limits,
        radius=0.02
    )

if __name__ == "__main__":
    main()