from shapely.geometry import Polygon
import matplotlib.pyplot as plt
import os
from paths import OUTPUT_PATH

def get_daylight_area_adjustment(coordinates, inset_distance):
   full_area = calculate_area(coordinates)
   new_coordinates = generate_inset_shape(coordinates, inset_distance)
   dark_area = calculate_area(new_coordinates)
   daylight_adjustment = dark_area/full_area
   daylight_name=os.path.join(OUTPUT_PATH, 'daylight.png')
   save_plot(coordinates,new_coordinates,daylight_name,daylight_adjustment)
   return daylight_adjustment

def generate_inset_shape(coordinates, inset_distance):
    shape = Polygon(coordinates)
    new_shape = shape.buffer(-inset_distance, join_style='bevel')
    
    if new_shape.geom_type == 'Polygon':
        new_coordinates = list(new_shape.exterior.coords)
        return new_coordinates
    else:
        # Handle cases where the shape breaks into multiple pieces
        print("Warning: The inset operation resulted in a MultiPolygon. "
              "Returning coordinates of the first part.")
        # This is a simplified approach. You might need to iterate through
        # new_shape.geoms to handle all parts.
        new_coordinates = list(new_shape.geoms[0].exterior.coords)
        return new_coordinates

def save_plot(coords, new_coords, filename,daylight_adjustment):
    daylight_text = str(round((1-daylight_adjustment)*100))+ "% Daylit"
    fig, ax = plt.subplots(figsize=(10, 8))

    # Plot the original shape
    orig_x, orig_y = zip(*coords)
    ax.fill(orig_x, orig_y, color='springgreen', alpha=0.5, label='Daylit area')

    # Plot the new, inset shape(s)
    if len(new_coords)>2:
        inset_x, inset_y = zip(*list(new_coords))
        ax.fill(inset_x, inset_y, color='black', alpha=1, label='Dark area')
    plt.text(5,4,daylight_text,color = 'grey')
    
    # Set the plot to have no axes, gridlines, and a tight layout
    ax.set_axis_off()
    ax.set_aspect('equal', adjustable='box')
    plt.tight_layout(pad=0) # Removes padding around the plot area
    plt.legend()

    # Save the figure with no padding or extra space
    plt.savefig(filename, bbox_inches='tight', pad_inches=0)
    plt.close() # Close the plot to free memory
    
def calculate_area(coordinates):
    direction_vectors = []
    for i in range(len(coordinates)):
        p1 = coordinates[i]
        p2 = coordinates[(i+1)%len(coordinates)]
        x1 = p1[0]
        x2 = p2[0]
        y1 = p1[1]
        y2 = p2[1]
        v = [x2 - x1, y2 - y1]
        direction_vectors.append(v)
    
    n = len(direction_vectors)
    signed_area =0
    for i in range(n):
        p1 = direction_vectors[i]
        p2 = direction_vectors[(i+1)%n] #wrap around
        signed_area += p1[0]*p2[1] - p1[1]*p2[0]
    return abs(signed_area)

def generate_coordinate_list(walls):
    coordinates = []
    #first wall add both points
    coordinates.append((walls[0]['x1'],walls[0]['y1']))
    
    for wall in walls:
       coordinates.append((wall['x2'],wall['y2']))
   
    coordinates = coordinates[:-1]
    return coordinates


#debug shape 
coords = [
    (-10, 0), (10, 0), (10, 2), (2, 2), (2, 8), (10, 8), (10, 10), (0, 10), (-10, 0)
]


