from shapely.geometry import Polygon, Point
import matplotlib.pyplot as plt
import os
import math
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
   save_plot(coordinates,new_coordinates,daylight_name,daylight_adjustment,multiblock,inset_distance)
   return daylight_adjustment

def generate_inset_shape(coordinates, inset_distance):
    shape = Polygon(coordinates)
    new_shape = shape.buffer(-inset_distance, join_style='bevel')
    
    if new_shape.geom_type == 'Polygon':
        new_coordinates = list(new_shape.exterior.coords)
        return new_coordinates,False
    else:
        # Handle cases where the shape breaks into multiple pieces
        new_coordinates = []
        for shape in new_shape.geoms:
            new_coordinates.append(list(shape.exterior.coords))
        return new_coordinates,True

def save_plot(coords, new_coords, filename,daylight_adjustment,multiblock, inset_distance):
    daylight_text = str(round((1-daylight_adjustment)*100))+ "% Daylit"
    fig, ax = plt.subplots(figsize=(10, 8))

    # Plot the original shape
    orig_x, orig_y = zip(*coords)
    ax.fill(orig_x, orig_y, color='dodgerblue', alpha=0.5, label='Daylit area')

    inset_distance_text = "("+str(round((inset_distance)))+ "m daylit perimeter)" 

    # Plot the new, inset shape(s)
    if multiblock == False:
        inset_x, inset_y = zip(*list(new_coords))
        ax.fill(inset_x, inset_y, color='grey', alpha=1, label='Dark area')
        plt.text(0.5,0.5,daylight_text,color = 'black'
                ,horizontalalignment='center', 
        verticalalignment='center',
        fontsize = 24,
        transform=ax.transAxes)
        
        inset_x, inset_y = zip(*list(new_coords))
        ax.fill(inset_x, inset_y, color='grey', alpha=1, label='Dark area')
        plt.text(0.5,0.45,inset_distance_text,color = 'black'
                ,horizontalalignment='center', 
        verticalalignment='center',
        fontsize = 12,
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
    #Shoelace formula
    n = len(coordinates)
    signed_area =0
    for i in range(n):
        x1, y1 = coordinates[i]
        x2, y2 = coordinates[(i + 1) % n]   #wrap around
        signed_area += (x1 * y2) - (x2 * y1)
    return abs(signed_area)/2

def isInside(px,py,polygon_points):
    point = Point(px, py)
    polygon = Polygon(polygon_points)
   
    if polygon.contains(point):
        return True
    elif polygon.boundary.contains(point) or polygon.touches(point):
        return 0
    else:
        return 0
    

def generate_coordinate_list(walls,ordered):
    coordinates = []
    
    #first wall add both points
    coordinates.append((walls[0]['x1'],walls[0]['y1']))
    
    for wall in walls:
       coordinates.append((wall['x2'],wall['y2']))

    coordinates.reverse()
    
    if ordered:
        #Find the index of the point with the lowest distance to (0,0)
        coordinates = coordinates[:-1]
        min_distance = float('inf')
        closest_point_index = -1
        for i, point in enumerate(coordinates):
            x, y = point
            distance = math.sqrt(x**2 + y**2)
            if distance < min_distance:
                min_distance = distance
                closest_point_index = i
        
        adjusted_coordinates = []
        n = len(coordinates)
        for i in range(len(coordinates)):
            adjusted_coordinates.append(coordinates[(closest_point_index +i) %n])
        return adjusted_coordinates
    else:
        return coordinates




