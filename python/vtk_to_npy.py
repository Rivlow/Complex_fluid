import vtk
import numpy as np
from vtk.util import numpy_support


def vtk_to_numpy(vtk_file_path, output_path):
    # Lecture du fichier VTK
    reader = vtk.vtkGenericDataObjectReader()
    reader.SetFileName(vtk_file_path)
    reader.Update()
    
    # Récupération des données
    data = reader.GetOutput()
    point_data = data.GetPointData()
    
    # Dictionnaire pour stocker toutes les variables
    variables = {}
    
    # Récupération de tous les arrays disponibles
    n_arrays = point_data.GetNumberOfArrays()
    for i in range(n_arrays):
        array_name = point_data.GetArrayName(i)
        array_data = numpy_support.vtk_to_numpy(point_data.GetArray(i))
        
        # Si les données sont structurées (comme pour StructuredPoints/ImageData)
        if isinstance(data, vtk.vtkStructuredPoints) or isinstance(data, vtk.vtkImageData):
            dimensions = data.GetDimensions()
            if array_data.shape[0] == dimensions[0] * dimensions[1] * dimensions[2]:
                array_data = array_data.reshape(dimensions)
        
        variables[array_name] = array_data
    
    # Si on a aussi des points (pour PolyData)
    if isinstance(data, vtk.vtkPolyData):
        points = data.GetPoints()
        points_data = numpy_support.vtk_to_numpy(points.GetData())
        variables['points'] = points_data
    
    # Sauvegarde en format NPY
    np.save(output_path, variables)
    
    print(f"Variables trouvées : {list(variables.keys())}")
    return variables

# Utilisation
vtk_file = r"C:\Users\lucas\Unif\complex_fluids_and_non-newtonian_flows\Projet\openfoam_container\output\fene_p\contraction\t_100\VTK\actual_19671.vtk"
output_file = r"C:\Users\lucas\Unif\complex_fluids_and_non-newtonian_flows\Projet\openfoam_container\output\fene_p\contraction\t_100"
data = vtk_to_numpy(vtk_file, output_file)