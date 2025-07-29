from shapely.geometry import Polygon, Point
import matplotlib.pyplot as plt
import os
from paths import OUTPUT_PATH

def get_daylight_area_adjustment(coordinates, inset_distance):
   full_area = calculate_area(coordinates)
   new_coordinates,multiblock = generate_inset_shape(coordinates, inset_distance)
   if multiblock == False:
    dark_area = calculate_area(new_coordinates)
   else:
       dark_area = 0
       for shape in new_coordinates:
           dark_area  += calculate_area(shape)
   
   daylight_adjustment = dark_area/full_area
   daylight_name=os.path.join(OUTPUT_PATH, 'daylight.png')
   save_plot(coordinates,new_coordinates,daylight_name,daylight_adjustment,multiblock)
   return daylight_adjustment

def generate_inset_shape(coordinates, inset_distance):
    shape = Polygon(coordinates)
    new_shape = shape.buffer(-inset_distance, join_style='bevel')
    
    if new_shape.geom_type == 'Polygon':
        new_coordinates = list(new_shape.exterior.coords)
        return new_coordinates,False
    else:
        # Handle cases where the shape breaks into multiple pieces
        # This is a simplified approach. You might need to iterate through
        # new_shape.geoms to handle all parts.
        new_coordinates = []
        for shape in new_shape.geoms:
            new_coordinates.append(list(shape.exterior.coords))
        return new_coordinates,True

def save_plot(coords, new_coords, filename,daylight_adjustment,multiblock):
    daylight_text = str(round((1-daylight_adjustment)*100))+ "% Daylit"
    fig, ax = plt.subplots(figsize=(10, 8))

    # Plot the original shape
    orig_x, orig_y = zip(*coords)
    ax.fill(orig_x, orig_y, color='dodgerblue', alpha=0.5, label='Daylit area')

    # Plot the new, inset shape(s)
    if multiblock == False:
        inset_x, inset_y = zip(*list(new_coords))
        ax.fill(inset_x, inset_y, color='grey', alpha=1, label='Dark area')
        plt.text(0.5,0.5,daylight_text,color = 'black'
                ,horizontalalignment='center', 
        verticalalignment='center',
        fontsize = 24,
        transform=ax.transAxes)
    else:
        for shape in new_coords:
            inset_x, inset_y = zip(*list(shape))
            ax.fill(inset_x, inset_y, color='grey', alpha=1, label='Dark area')
        plt.text(0.5,0.5,daylight_text,color = 'black',
        horizontalalignment='center', 
        verticalalignment='center',
        fontsize = 24,
        transform=ax.transAxes)
    
    #Remove duplicate labels
    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    
    # Set the plot to have no axes, gridlines, and a tight layout
    ax.set_axis_off()
    ax.set_aspect('equal', adjustable='box')
    plt.tight_layout(pad=0) # Removes padding around the plot area
    plt.legend(by_label.values(), by_label.keys())

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

def isInside(px,py,polygon_points):
    point = Point(px, py)
    polygon = Polygon(polygon_points)
   
    if polygon.contains(point):
        return True
    elif polygon.boundary.contains(point) or polygon.touches(point):
        # .boundary.contains(point) checks if the point is on the exterior or interior rings.
        # .touches(point) specifically checks if the point is on the boundary
        # without being inside. It's often redundant if .boundary.contains is used for
        # simple cases, but can be helpful for more complex boundary definitions or if
        # you want to be explicit about touching. For points, .boundary.contains is
        # usually sufficient for boundary checks.
        return 0
    else:
        return 0
    

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
    (0,0),(5,9),(10,0),(10,10),(0,10)
]
get_daylight_area_adjustment(coords, 1.5)


