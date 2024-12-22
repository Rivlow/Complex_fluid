import os

class GeometryGenerator:
    def __init__(self, inlet_length, obstacle_width, obstacle_spacing, 
                 channel_height, channel_depth, convertToMeters=0.0032):
        # Dimensions de base (avant conversion)
        self.inlet_length = inlet_length
        self.obstacle_width = obstacle_width
        self.obstacle_spacing = obstacle_spacing
        self.channel_height = channel_height
        self.channel_depth = channel_depth
        self.convertToMeters = convertToMeters
        
        # Constants from original geometry
        self.GRADING_RATIO = 0.0002
        self.VERTICAL_GRADING = 3.333
        
        # Fixed y-coordinates from blockMeshDict
        self.symmetry_y = 1.5  # Fixed bottom y-coordinate
        self.mid_height = 2.0  # Fixed middle y-coordinate
        self.top_height = 3.0  # Fixed top y-coordinate
        
        # Calculate real positions (scaled by convertToMeters)
        self.calculate_real_positions()

    def calculate_real_positions(self):
        """Calculate actual positions scaled by convertToMeters"""
        self.scaled_positions = {
            'y': {
                'symmetry': self.symmetry_y * self.convertToMeters,
                'middle': self.mid_height * self.convertToMeters,
                'top': self.top_height * self.convertToMeters
            },
            'z': {
                'middle': (self.channel_depth / 2) * self.convertToMeters
            }
        }
        
    def generate_mesh_points(self):
        """Generate mesh vertices with exact coordinates from blockMeshDict"""
        vertices = []
        
        # Define exact x positions as in blockMeshDict
        x_positions = {
            'inlet': {'start': 0.0, 'end': 5.0},
            'obs1': {'start': 8.0, 'end': 9.0},
            'obs2': {'start': 12.0, 'end': 13.0},
            'obs3': {'start': 16.0, 'end': 17.0},
            'outlet': {'start': 20.0, 'end': 25.0}
        }
        
        y_coords = [self.symmetry_y, self.mid_height, self.top_height]
        
        # Generate points for z = 0 and z = channel_depth
        for z in [0, self.channel_depth]:
            for section in ['inlet', 'obs1', 'obs2', 'obs3', 'outlet']:
                for y in y_coords:
                    vertices.extend([
                        (x_positions[section]['start'], y, z),
                        (x_positions[section]['end'], y, z)
                    ])
        
        return vertices

    def format_vertices_section(self):
        """Generate the vertices section with exact OpenFOAM formatting"""
        vertices = self.generate_mesh_points()
        
        lines = ["vertices", "("]
        for i, (x, y, z) in enumerate(vertices):
            line = f"    ({x:.1f} {y:.1f} {z:.1f})        // {i}"
            lines.append(line)
        lines.append(");")
        
        return "\n".join(lines)

    def calculate_sampling_positions(self):
        """Calculate exact sampling positions matching the actual mesh"""
        return {
            'before_obs1': {
                'x037': 7.0 * self.convertToMeters,
                'x05': 6.0 * self.convertToMeters,
                'x1': 5.5 * self.convertToMeters
            },
            'at_obs2': 12.0 * self.convertToMeters,
            'after_obs2': {
                'x05': 13.5 * self.convertToMeters,
                'x1': 15.0 * self.convertToMeters
            }
        }

    def update_sample_dict(self, filepath):
        """Update sample points in sampleDict file with scaled coordinates"""
        positions = self.calculate_sampling_positions()
        scaled = self.scaled_positions
        
        content = f"""/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\\\      /  F ield         | foam-extend: Open Source CFD                    |
|  \\\\    /   O peration     | Version:     5.0                                |
|   \\\\  /    A nd           | Web:         http://www.foam-extend.org         |
|    \\\\/     M anipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    location    "system";
    object      sampleDict;
}}

// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

interpolationScheme cellPoint;
setFormat     raw;

sets
(
    fig7_x_037
    {{
        type        uniform;
        axis        y;
        start       ({positions['before_obs1']['x037']} {scaled['y']['symmetry']} {scaled['z']['middle']});
        end         ({positions['before_obs1']['x037']} {scaled['y']['top']} {scaled['z']['middle']});
        nPoints     100;
    }}

    fig7_x_05
    {{
        type        uniform;
        axis        y;
        start       ({positions['before_obs1']['x05']} {scaled['y']['symmetry']} {scaled['z']['middle']});
        end         ({positions['before_obs1']['x05']} {scaled['y']['top']} {scaled['z']['middle']});
        nPoints     100;
    }}

    fig7_x_1
    {{
        type        uniform;
        axis        y;
        start       ({positions['before_obs1']['x1']} {scaled['y']['symmetry']} {scaled['z']['middle']});
        end         ({positions['before_obs1']['x1']} {scaled['y']['top']} {scaled['z']['middle']});
        nPoints     100;
    }}

    fig7_x_2
    {{
        type        uniform;
        axis        y;
        start       ({positions['at_obs2']} {scaled['y']['symmetry']} {scaled['z']['middle']});
        end         ({positions['at_obs2']} {scaled['y']['top']} {scaled['z']['middle']});
        nPoints     100;
    }}

    fig10_x_05
    {{
        type        uniform;
        axis        y;
        start       ({positions['after_obs2']['x05']} {scaled['y']['symmetry']} {scaled['z']['middle']});
        end         ({positions['after_obs2']['x05']} {scaled['y']['top']} {scaled['z']['middle']});
        nPoints     100;
    }}

    fig10_x_1
    {{
        type        uniform;
        axis        y;
        start       ({positions['after_obs2']['x1']} {scaled['y']['symmetry']} {scaled['z']['middle']});
        end         ({positions['after_obs2']['x1']} {scaled['y']['top']} {scaled['z']['middle']});
        nPoints     100;
    }}

    fig11_y_0
    {{
        type        uniform;
        axis        x;
        start       ({positions['before_obs1']['x1']} {scaled['y']['symmetry']} {scaled['z']['middle']});
        end         ({positions['after_obs2']['x1']} {scaled['y']['symmetry']} {scaled['z']['middle']});
        nPoints     100;
    }}

    fig11_y_04
    {{
        type        uniform;
        axis        x;
        start       ({positions['before_obs1']['x1']} {scaled['y']['middle']} {scaled['z']['middle']});
        end         ({positions['after_obs2']['x1']} {scaled['y']['middle']} {scaled['z']['middle']});
        nPoints     100;
    }}

    fig11_y_1
    {{
        type        uniform;
        axis        x;
        start       ({positions['before_obs1']['x1']} {scaled['y']['top']} {scaled['z']['middle']});
        end         ({positions['after_obs2']['x1']} {scaled['y']['top']} {scaled['z']['middle']});
        nPoints     100;
    }}
);

surfaceFormat null;

surfaces ();

fields
(
    N1
    N2
    tau
    U
    p
);

// ************************************************************************* //"""

        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w') as file:
                file.write(content)
            print(f"Successfully updated {filepath}")
        except Exception as e:
            print(f"Error updating sample dict: {e}")

    def update_blockmesh_file(self, filepath):
        """Update vertices in blockMeshDict file"""
        try:
            with open(filepath, 'r') as file:
                content = file.read()
            
            start = content.find("vertices")
            if start == -1:
                raise Exception("Could not find vertices section")
            
            end = content.find(");", start)
            if end == -1:
                raise Exception("Could not find end of vertices section")
            end += 2
            
            new_vertices = self.format_vertices_section()
            new_content = content[:start] + new_vertices + content[end:]
            
            with open(filepath, 'w') as file:
                file.write(new_content)
            
            print(f"Successfully updated vertices in {filepath}")
            
        except Exception as e:
            print(f"Error updating file: {e}")

def main():
    base_path = "openfoam_data/simulation/fene_p/four_obstacle"
    
    geometry = GeometryGenerator(
        inlet_length=5,
        obstacle_width=1,
        obstacle_spacing=3,
        channel_height=3,
        channel_depth=0.1,
        convertToMeters=0.0032  # Important: ajout du facteur d'échelle
    )
    
    # Construction des chemins complets
    blockMeshPath = os.path.join(base_path, "system", "blockMeshDict")
    sampleDictPath = os.path.join(base_path, "system", "sampleDict")
    
    # Mise à jour des fichiers
    geometry.update_blockmesh_file(blockMeshPath)
    geometry.update_sample_dict(sampleDictPath)

if __name__ == "__main__":
    main()