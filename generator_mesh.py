class GeometryGenerator:
    def __init__(self, inlet_length, obstacle_width, obstacle_spacing, 
                 channel_height, channel_depth):
       
        self.inlet_length = inlet_length
        self.obstacle_width = obstacle_width
        self.obstacle_spacing = obstacle_spacing
        self.channel_height = channel_height  # Full height (will be divided by 2)
        self.channel_depth = channel_depth
        
        # Constants from original geometry
        self.GRADING_RATIO = 0.0002  # per unit length
        self.VERTICAL_GRADING = 3.333
        
        # Define the symmetry plane y-coordinate
        self.symmetry_y = self.channel_height / 2
        
    def calculate_grading(self, length):
        return self.GRADING_RATIO * length
        
    def generate_mesh_points(self):
        vertices = []
        
        # Calculate x positions
        x_inlet = 0
        x_inlet_end = self.inlet_length
        
        x_obs1 = x_inlet_end + self.obstacle_spacing
        x_obs1_end = x_obs1 + self.obstacle_width
        
        x_obs2 = x_obs1_end + self.obstacle_spacing
        x_obs2_end = x_obs2 + self.obstacle_width
        
        x_obs3 = x_obs2_end + self.obstacle_spacing
        x_obs3_end = x_obs3 + self.obstacle_width  # Removed /5 factor
        
        x_outlet = x_obs3_end + self.obstacle_spacing
        x_outlet_end = x_outlet + self.inlet_length

        # Define y coordinates for upper half only
        y_coords = [self.symmetry_y, 2, self.channel_height]  # Only y ≥ 1.5
        
        vertices = []
        # Generate points for z = 0 and z = 0.1
        for z in [0, self.channel_depth]:
            # Section 1 - Inlet
            for y in y_coords:
                vertices.extend([
                    (x_inlet, y, z),
                    (x_inlet_end, y, z)
                ])
            
            # Section 2 - First obstacle
            for y in y_coords:
                vertices.extend([
                    (x_obs1, y, z),
                    (x_obs1_end, y, z)
                ])
            
            # Section 3 - Second obstacle
            for y in y_coords:
                vertices.extend([
                    (x_obs2, y, z),
                    (x_obs2_end, y, z)
                ])
            
            # Section 4 - Third obstacle
            for y in y_coords:
                vertices.extend([
                    (x_obs3, y, z),
                    (x_obs3_end, y, z)
                ])
            
            # Section 5 - Outlet
            for y in y_coords:
                vertices.extend([
                    (x_outlet, y, z),
                    (x_outlet_end, y, z)
                ])
        
        return vertices

    def format_vertices_section(self):
        """Generate the vertices section with exact OpenFOAM formatting"""
        vertices = self.generate_mesh_points()
        
        # Header
        lines = ["vertices", "("]
        
        # Format each vertex with OpenFOAM style
        for i, (x, y, z) in enumerate(vertices):
            line = f"    ({x:.1f} {y:.1f} {z:.1f})        // {i}"
            lines.append(line)
            
        # Closing parenthesis
        lines.append(");")
        
        return "\n".join(lines)

    def update_blockmesh_file(self, filepath):
        """Update vertices in blockMeshDict file"""
        try:
            # Read the entire file
            with open(filepath, 'r') as file:
                content = file.read()
            
            # Find the vertices section
            start = content.find("vertices")
            if start == -1:
                raise Exception("Could not find vertices section")
            
            # Find the matching closing parenthesis
            end = content.find(");", start)
            if end == -1:
                raise Exception("Could not find end of vertices section")
            end += 2  # Include the ");
            
            # Generate new vertices section
            new_vertices = self.format_vertices_section()
            
            # Replace the old section with the new one
            new_content = content[:start] + new_vertices + content[end:]
            
            # Write back to file
            with open(filepath, 'w') as file:
                file.write(new_content)
            
            print(f"Successfully updated vertices in {filepath}")
            
        except Exception as e:
            print(f"Error updating file: {e}")

def main():
    # Example usage
    geometry = GeometryGenerator(
        inlet_length=12,
        obstacle_width=1,
        obstacle_spacing=3,
        channel_height=3,  # Full height
        channel_depth=0.1
    )
    
    # Update the blockMeshDict file
    filepath = "openfoam_data/simulation/fene_p/four_obstacle/system/blockMeshDict"
    geometry.update_blockmesh_file(filepath)

if __name__ == "__main__":
    main()