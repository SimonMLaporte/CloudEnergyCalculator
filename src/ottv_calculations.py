import math
from geometry import generate_coordinate_list

def calculate_OTTV(input):
    #formula from MS 1525:2014 clause 5.2.1
    walls = input['walls']

    #find the wall normal directions and map to nearest 45 degrees
    actual_directions = calculate_wall_orientation(walls,input['rotation'])
    wall_nearest_direction = []
    for direction in actual_directions:
        wall_nearest_direction.append(quantize_direction(direction))
    
    #Calculate area of each wall
    total_area = 0
    wall_area = []
    height = input["height"]
    for wall in input['walls']:
        x1 = wall['x1']
        x2 = wall['x2']
        y1 = wall['y1']
        y2 = wall['y2']
        distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        wall_area.append(distance * height)
        total_area += distance * height
    
    #Calculate shading coefficients
    sc = []
    for i in range(len(input['walls'])):
        wall = input['walls'][i]
        direction = wall_nearest_direction[i]
        sc.append(OTTV_shading_coefficient(wall['glass_sc'],wall['overhang_depth'],wall['window_height'],wall['window_width'],wall['z_offset'],wall['sidefin_depth'],wall['fin_to_fin_distance'],direction))
    

    
    #OTTV orientation factors
    orientation_factor_dict = {
                0: 0.9,
                45: 1.09,
                90: 1.23,
                135: 1.13,
                180: 0.92,
                225: 0.9,
                270: 0.94,
                315: 0.9,
                }
    
    #Calculate OTTV
    OTTV_n = 0
    for i in range(len(input['walls'])):
        wall = input['walls'][i]
        OTTV_i = 15*wall['absorptivity']*(1-wall['WWR'])*wall['wall_u']+ 6*wall['WWR']*wall['glass_u']+(194*orientation_factor_dict[wall_nearest_direction[i]]*wall['WWR']*sc[i])
        OTTV_n += OTTV_i * wall_area[i]
    OTTV = OTTV_n/total_area
    
    #Calculate RTTV
    roof = input['roof']
    area_roof = input['footprint']
    u_roof = roof['roof_u']
    #Assuming heavy roof
    equivilent_temp_difference = 24 #from standard
    skylight_area = area_roof * roof['roof_WWR']
    opaque_area = area_roof - skylight_area
    skylight_u = roof['roof_glass_u']
    skylight_sc = roof['roof_glass_sc'] #does not allow for shading of skylight
    design_temperature_difference = 5 #standard from code
    solar_factor = 323 # from standard for flat roof
    
    RTTV = ((opaque_area * u_roof*equivilent_temp_difference)+(skylight_u*skylight_area*design_temperature_difference)+(skylight_area*solar_factor*skylight_sc))/area_roof
    
    return OTTV,RTTV


def quantize_direction(direction):
    bins = [0,45,90,135,180,225,270,315,360]
    nearest = 0
    min_diff = abs(direction - nearest)
    
    for b in bins:
        diff = abs(direction - b)
        if diff < min_diff:
            min_diff = diff
            nearest = b
    if nearest == 360:
        nearest = 0
    return nearest


def OTTV_shading_coefficient(glass_sc,overhang_depth,window_height,window_width,z_offset,side_fin_depth,fin_to_fin_distance,direction):
    sc1 = glass_sc
    R1 = overhang_depth/(window_height+z_offset)
    R2 = side_fin_depth/(window_width+(fin_to_fin_distance-window_width)/2)
    #maps index for orienttation in degrees clockwise to array of shading factors
    orientation_factor_dict = {
            0: 1, #N
            45: 4, #NE
            90: 3, #E
            135: 5, #SE
            180: 1, #S
            225: 4, #SW
            270: 3, #W
            315: 5, #NW
            }
    #R1 value table from reference
    SC2_r1_values = [
    [0.77, 0.71, 0.67, 0.65],   # N/S
    [0.77, 0.68, 0.6, 0.55],   # East
    [0.79, 0.71, 0.65, 0.61],   # West
    [0.77, 0.69, 0.63, 0.6], #NE/SW
    [0.79, 0.72, 0.66, 0.63] #NW/SE
    ]
    SC2_r2_values = [
    [0.82, 0.77, 0.73, 0.7],   # N/S
    [0.82, 0.82, 0.78, 0.75],   # East
    [0.86, 0.81, 0.77, 0.74],   # West
    [0.83, 0.77, 0.72, 0.69], #NE/SW
    [0.84, 0.79, 0.74, 0.71] #NW/SE
    ]
    column_ranges = [
    (0.3, 0.45),
    (0.45, 0.75),
    (0.75, 1.25),
    (1.25, 2.0)
    ]
    orientation = orientation_factor_dict[direction]
    
    sc2_r1 = get_row_by_value_and_ranges(SC2_r1_values, R1, orientation, column_ranges)
    sc2_r2 = get_row_by_value_and_ranges(SC2_r2_values, R2, orientation, column_ranges)
    sc2 = min(sc2_r1,sc2_r2)
    return sc1 * sc2


def get_row_by_value_and_ranges(arr_2d, value, row_index, ranges):
    col_to_return = -1  # Initialize with an invalid column index

    for i, (min_val, max_val) in enumerate(ranges):
        if min_val <= value < max_val:
            col_to_return = i
            break

    if col_to_return == -1:
        return 1

    if not (0 <= row_index < len(arr_2d)):
        return 1

    # Extract the value at the found column for the specified row
    if col_to_return < len(arr_2d[row_index]):
        return arr_2d[row_index][col_to_return]
    else:
        return 1
    
def calculate_wall_orientation(walls,rotation):
    points = generate_coordinate_list(walls,False)
    points.pop()
    #Map orientation to rodation
    #rotation_dict = {
    #    "North": 0,
    #    "North-East": 45,
    #    "East": 90,
    #    "South-East": 135,
    #    "South": 180,
    #    "South-West": 225,
    #    "West": 270,
    #    "North-West": 315,
    #}
    
    #orientation1 = rotation_dict[rotation]
    
    # calculate direction vector
    direction_vectors = []
    
    for i in range(len(points)):
        p1 = points[i]
        p2 = points[(i+1)%len(points)]
        x1 = p1[0]
        x2 = p2[0]
        y1 = p1[1]
        y2 = p2[1]
        v = [x2 - x1, y2 - y1]
        direction_vectors.append(v)
    
    # determine polygons winding order
    winding_order = calculate_winding_order(direction_vectors)
    # calculate the normal angle for each wall
    normal_angles = calculate_normal_and_angle(points, winding_order)
    
    rotated_angles = [] 
    for angle in normal_angles:
        rotated_angles.append((angle - rotation) % 360)
    
    return rotated_angles


def calculate_normal_and_angle(points, winding_order):
    n = len(points)
    normal_angles = []
    wall_directions = []
    
    for i in range(n):
        p1 = points[i]
        p2 = points[(i+1)%n]
        
        #calculate direction vector components
        vx = p2[0] - p1[0]
        vy = p2[1] - p1[1]
        
        #rotate vector 90 degrees depending on winding order
        if winding_order == 'CCW':
            normal_x = vy
            normal_y = -vx
        if winding_order == 'CW':
            normal_x = -vy
            normal_sy = vx
        
        #normalize vectors
        norm_magnitude = math.sqrt(normal_x**2 + normal_y**2)
        if norm_magnitude == 0:
            unit_normal_x = 0
            unit_normal_y = 0
        else:
            unit_normal_x = normal_x / norm_magnitude
            unit_normal_y = normal_y / norm_magnitude
        
        
        #convert to degrees CW from x axis
        angle_rad_from_x = math.atan2(normal_y, normal_x)
        angle_deg_from_x = math.degrees(angle_rad_from_x)
        angle_deg_clockwise_from_y_axis = (90 - angle_deg_from_x) % 360
        wall_directions.append((angle_deg_clockwise_from_y_axis) % 360)
        
        
    return wall_directions


def calculate_winding_order(direction_vectors):
    #Determine if a polygon is clockwise or counter clockwise based on the signed area (if the area is positive or negative)
    n = len(direction_vectors)
    signed_area =0
    for i in range(n):
        p1 = direction_vectors[i]
        p2 = direction_vectors[(i+1)%n] #wrap around
        signed_area += p1[0]*p2[1] - p1[1]*p2[0]
    
    if signed_area > 0:
        return 'CCW'
    elif signed_area < 0:
        return 'CW'
    else:
        return 'DEGENERATE'



