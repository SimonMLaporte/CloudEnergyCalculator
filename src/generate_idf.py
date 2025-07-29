from geomeppy import IDF
from geometry import generate_coordinate_list, get_daylight_area_adjustment, calculate_area, isInside
from shapely.geometry import Polygon
import math
import pandas as pd
import os
import math



def generate_idf(inputJson):
    schedules = { "office": "office",
                 "retail_hyper": "retail",
                 "retail_center": "retail",
                 "hotel_4star": "hotel",
                 "healthcare_limited": "alwaysON",
                 "healthcare_major": "alwaysON",
                 "residential": "residential",
    }
    idf, outpath = load_baseline()
    assumptions = load_assumptions(inputJson['building_type'])
    
    #Extract values from JSON
    schedule = schedules[inputJson['building_type']]
    height =inputJson["height"]
    gfa = inputJson['gfa']
    NV = inputJson['NV_percent']
    
    #generate main geometry
    coordinates = generate_coordinate_list(inputJson['walls'])
    facade_area = calculate_facade_area(inputJson['walls'],height)
    idf.add_block('MAIN',coordinates,height)
    idf.intersect_match()
    idf.rotate(inputJson['rotation']) #rotates in degrees CCW from north/Y-axis

    idf.set_default_constructions()
    surfaces = idf.getsurfaces()
    surface_names = []
    for s in surfaces:
        surface_names.append(s.Name)
    
    #
    daylight_adjustment = get_daylight_area_adjustment(coordinates, inputJson['daylight_distance'])
    # remove dummy names form list, the floor and the roof
    wall_names = surface_names[6:-2]
    #Get roof as the last item on the list
    roof_name = surface_names[-1]
    
    
    
    #add dummy objects
    idf.newidfobject("LIGHTS",
                     Name = 'dummyLights',
                     Zone_or_ZoneList_or_Space_or_SpaceList_Name = 'dummyBlock',
                     Schedule_Name = schedule,
                     Lighting_Level = NV * gfa * inputJson["LPD"] * daylight_adjustment,
                     EndUse_Subcategory = "main_lighting"
                     )
    idf.newidfobject("LIGHTS",
                     Name = 'facadeLights_landscapeLights',
                     Zone_or_ZoneList_or_Space_or_SpaceList_Name = 'dummyBlock',
                     Schedule_Name = 'night',
                     Lighting_Level = facade_area * assumptions['Facade lighting (W/m2)'] + inputJson['landscape_area']* assumptions['Landscape lighting (W/m2)'],
                     EndUse_Subcategory = "facade_landscape_lighting"
                     )
    idf.newidfobject("LIGHTS",
                     Name = 'carParkLights',
                     Zone_or_ZoneList_or_Space_or_SpaceList_Name = 'dummyBlock',
                     Schedule_Name = 'night',
                     Lighting_Level = inputJson['carpark_area_above_ground'] * assumptions['Carpark lighting, above ground (W/m2)']+ inputJson['carpark_area_below_ground'] * assumptions['Carpark lighting, below ground (W/m2)'],
                     EndUse_Subcategory = "carpark_lighting"
                     )
    idf.newidfobject("ELECTRICEQUIPMENT",
                     Name = 'dummyEquipment',
                     Zone_or_ZoneList_or_Space_or_SpaceList_Name = 'dummyBlock',
                     Schedule_Name = schedule,
                     Design_Level = NV * gfa * (assumptions['Equipment (W/m2)']),
                     EndUse_Subcategory = "main_equipment"
                     )
    idf.newidfobject("ELECTRICEQUIPMENT",
                     Name = 'lifts',
                     Zone_or_ZoneList_or_Space_or_SpaceList_Name = 'dummyBlock',
                     Schedule_Name = schedule,
                     Design_Level = gfa * assumptions['Lift (W/m2)'],
                     EndUse_Subcategory = "lifts"
                     )
    
    idf.newidfobject("ELECTRICEQUIPMENT",
                     Name = 'carparkVentilation',
                     Zone_or_ZoneList_or_Space_or_SpaceList_Name = 'dummyBlock',
                     Schedule_Name = schedule,
                     Design_Level = inputJson['carpark_area_above_ground']*assumptions['Carpark ventilation, above ground (W/m2)'] + inputJson['carpark_area_below_ground']*assumptions['Carpark ventilation, below ground (W/m2)'],
                     EndUse_Subcategory = "carpark_ventilation"
                     )
                                   


    #Set Schedules
    set_schedules(idf,schedule)

    # Add windows and shading
    window_id = []
    counter = 0
    for wall in inputJson['walls']:
        window = add_window(wall_names[counter], wall['WWR'],idf)
        window_id.append(window)
        add_shade(idf, window,wall['window_width'],wall['window_height'],wall['overhang_depth'],wall['sidefin_depth'],wall['fin_to_fin_distance'],wall['z_offset'])
        counter += 1
    roof_windows = add_roof_window(roof_name, inputJson['roof']['roof_WWR'],idf, coordinates,height)
    
    
    # Set lighting
    newWatt = gfa*(1-NV) * daylight_adjustment
    lights = idf.idfobjects["LIGHTS"]
    lights[0].Lighting_Level = newWatt
    
    # Set equipment
    newEquip = gfa*(1-NV) * assumptions['Equipment (W/m2)']
    equip = idf.idfobjects["ELECTRICEQUIPMENT"]
    equip[0].Design_Level = newEquip

    # Set people
    newPeople = gfa * (1-NV) * assumptions['People diversity, 0-1'] /assumptions['People density (m2/pax AC area)']
    people = idf.idfobjects["PEOPLE"]
    people[0].Number_of_People = newPeople

    #Set fresh air rate
    freshAir = idf.idfobjects["DESIGNSPECIFICATION:OUTDOORAIR"][0]
    freshAir.Outdoor_Air_Flow_per_Zone = (assumptions['Fresh Air Rate per Floor Area (l/s/m2)'] * (1-NV) * gfa + assumptions['Fresh Air Rate per person (l/s)'] * (1-NV) * (gfa / assumptions['People density (m2/pax AC area)']))/1000
    
    #Set building thermal mass
    idf.newidfobject("INTERNALMASS",
                Name = 'internalmass',
                Construction_Name = 'AllSurfaces',
                Zone_or_ZoneList_Name = 'Block MAIN Storey 0',
                Surface_Area = gfa*(1-NV)
                )
    
    #Set constructions
    counter = 0
    for wall in inputJson['walls']:
        set_construction(idf, wall_names[counter], window_id[counter],wall['wall_u'],wall['absorptivity'],wall['glass_sc'],wall['glass_u'],True)
        counter += 1
    counter = 0
    for skylight_name in roof_windows:
        if counter == 0: #ensure wall construction is only being added once
            set_construction(idf, roof_name, skylight_name,inputJson['roof']['roof_u'],inputJson['roof']['roof_absorptivity'],inputJson['roof']['roof_glass_sc'],inputJson['roof']['roof_glass_u'],True)
        else:
            set_construction(idf, roof_name, skylight_name,inputJson['roof']['roof_u'],inputJson['roof']['roof_absorptivity'],inputJson['roof']['roof_glass_sc'],inputJson['roof']['roof_glass_u'],False)
        counter += 1
    #Save idf
    idf.saveas(outpath)
    return assumptions

def add_roof_window(wallID,WWR,idf, coordinates,z):

    #Special case as there is a risk of window going outside the roof 
    window_ratio = 0
    if WWR == 1:
        window_ratio = 0.99
    else:
        window_ratio = WWR
    
    #extract roof
    surfaces = idf.idfobjects["BUILDINGSURFACE:DETAILED"]
    selected = ''
    for s in surfaces:
        if s.Name == wallID:
            selected = s
    
    
    #script breaks down the total window size into a range of smaller windows
    roof_area = calculate_area(coordinates)
    target_area = roof_area * window_ratio
    window_area = max(1,roof_area/50) #ensure that there is no more than 50 windows
    side_length = math.sqrt(window_area)
    number_skylights = int(round(target_area/window_area))
    
    
    placed_skylight_count = 0
    skylight_spacing = 0.2
    current_x_local =skylight_spacing
    current_y_local = skylight_spacing
    
    origin_x = coordinates[0][0]
    origin_y = coordinates[0][1]
    skylight_names = []
    #try to fit each skylight
    for i in range(number_skylights):

        global_upper_right = [origin_x + current_x_local + side_length,origin_y + current_y_local+side_length]
        global_lower_right = [origin_x + current_x_local + side_length,origin_y + current_y_local]
        
        #check if window is outside of roof if outside go to next line
        if isInside(global_upper_right[0],global_upper_right[1],coordinates)==0 or isInside(global_lower_right[0],global_lower_right[1],coordinates)==0:
            current_x_local = skylight_spacing
            current_y_local += side_length + current_y_local
        
        global_upper_right = [origin_x + current_x_local + side_length,origin_y + current_y_local+side_length,z]
        global_lower_right = [origin_x + current_x_local + side_length,origin_y + current_y_local,z]
        global_upper_left = [origin_x + current_x_local,origin_y + current_y_local + side_length,z]
        global_lower_left = [origin_x + current_x_local,origin_y + current_y_local,z]
        
        
        skylight_fields = {
           'Name': f'Skylight_{i+1}',
            'Surface_Type': 'Window',
            'Construction_Name': "window",
            'Building_Surface_Name': wallID,
            'Number_of_Vertices': 4 # Always 4 for a rectangle
        }
         # Assign the 4 global vertex coordinates directly
        skylight_fields['Vertex_1_Xcoordinate'] = global_upper_right[0]
        skylight_fields['Vertex_1_Ycoordinate'] = global_upper_right[1]
        skylight_fields['Vertex_1_Zcoordinate'] = global_upper_right[2]

        skylight_fields['Vertex_2_Xcoordinate'] = global_upper_left[0]
        skylight_fields['Vertex_2_Ycoordinate'] = global_upper_left[1]
        skylight_fields['Vertex_2_Zcoordinate'] = global_upper_left[2]

        skylight_fields['Vertex_3_Xcoordinate'] = global_lower_left[0]
        skylight_fields['Vertex_3_Ycoordinate'] = global_lower_left[1]
        skylight_fields['Vertex_3_Zcoordinate'] = global_lower_left[2]

        skylight_fields['Vertex_4_Xcoordinate'] = global_lower_right[0]
        skylight_fields['Vertex_4_Ycoordinate'] = global_lower_right[1]
        skylight_fields['Vertex_4_Zcoordinate'] = global_lower_right[2]
            # Create the FenestrationSurface:Detailed object
        idf.newidfobject(
            'FENESTRATIONSURFACE:DETAILED',
            **skylight_fields
        )
        
        skylight_names.append(f'Skylight_{i+1}')
        current_x_local += (side_length + skylight_spacing)
        
    return skylight_names
        

        
            
    #check is exceeding roof width, go to next line if exceeding
        
        
    # Calculate the centroid

    
    #Draw skylight as a square in the middle of the roof
    if WWR>0:
        idf.newidfobject(
            'WINDOW',
            Name=wallID + "_window",
            Construction_Name='window',
            Building_Surface_Name=wallID,
            Starting_X_Coordinate=centroid_x-side_length/2,
            Starting_Z_Coordinate=centroid_y-side_length/2,
            Length=side_length,
            Height=side_length
            )
    return wallID + "_window"

def add_window(wallID,WWR,idf):
    #extract wall
    surfaces = idf.idfobjects["BUILDINGSURFACE:DETAILED"]
    selected = ''
    for s in surfaces:
        if s.Name == wallID:
            selected = s
    windowheight=selected.height*WWR

    #ensure window is fully surrounded
    if WWR>0:
        idf.newidfobject(
            'WINDOW',
            Name=wallID + "_window",
            Construction_Name='window',
            Building_Surface_Name=wallID,
            Starting_X_Coordinate=0.01,
            Starting_Z_Coordinate=0.01,
            Length=selected.width - 0.02,
            Height=windowheight - 0.02
            )
    return wallID + "_window"

def set_construction(idf, wallID,windowID, Uvalue, absorb, glassSC, glassU, add_wall_construction):
    
    #Add window constrction
   
    idf.newidfobject(
        'WINDOWMATERIAL:SIMPLEGLAZINGSYSTEM',
        Name = windowID + '_window_construction',
        UFactor = glassU,
        Solar_Heat_Gain_Coefficient = glassSC,
    )
    
    idf.newidfobject(
        'CONSTRUCTION',
        Name=windowID + '_window_construction',
        Outside_Layer=windowID + '_window_construction'
        )
    
    
    
    #Set window construction
    surfaces = idf.idfobjects["WINDOW"]
    selected = ''
    for s in surfaces:
        if s.Name == windowID:
            s.Construction_Name = windowID + '_window_construction'
    if add_wall_construction:
        #Add wall construction
        #Add dummy material with solar absorbtance
        r_value = 1 / Uvalue 

        # 2. Calculate Solar Absorptance from Albedo
        solar_absorptance = absorb
        # 3. Create a unique Material:NoMass name
        construction_name = wallID + '_wall_material'

    
        # 4. Create the Material:NoMass object
        idf.newidfobject(
            'MATERIAL:NOMASS',
            Name=construction_name,
            Roughness='Smooth', # You can adjust roughness as needed
            Thermal_Resistance=r_value, # This sets the U-value
            Solar_Absorptance=solar_absorptance, # This sets the albedo
            Visible_Absorptance=solar_absorptance, # Often set to same as solar absorptance for simplicity
            Thermal_Absorptance=0.9 # Typical value for exterior surfaces
            )
        
        # 5. Create a simple Construction using this Material:NoMass
        idf.newidfobject(
            'CONSTRUCTION',
            Name=construction_name,
            Outside_Layer=construction_name
            )
        
        #Set wall construction
        surfaces = idf.idfobjects["BUILDINGSURFACE:DETAILED"]
        selected = ''
        for s in surfaces:
            if s.Name == wallID:
                s.Construction_Name = construction_name
        
    return 0
    
def set_building_dimensions(idf,length,width,height,orientation):
    
    rotationMapping = {
    "North": 0,
    "North-East": 315,
    "East": 270,
    "South-East": 225,
    "South": 180,
    "South-West": 135,
    "West": 90,
    "North-West": 45,
    }
    
    angle = rotationMapping[orientation]
    idf.rotate(angle)
    
    scaleX = width/10 #starting dimensions are 10m x 10m x 10m
    scaleY= length/10
    scaleZ=height/10
    idf.scale(scaleX,axes='x')
    idf.scale(scaleY,axes='y')
    idf.scale(scaleZ,axes='z')

    return 0

def add_shade(idf, window_name,window_width, window_height,overhang_depth, sidefin_depth,fin_to_fin, z_offset):
        idf.newidfobject(
        'SHADING:OVERHANG:PROJECTION',
        Name=window_name +'overhang',
        Window_or_Door_Name=window_name,
        Tilt_Angle_from_WindowDoor=90,
        Depth_as_Fraction_of_WindowDoor_Height = overhang_depth/window_height,
        Height_above_Window_or_Door = z_offset,
        )
        
        
        if fin_to_fin > window_width:
            left_offset = fin_to_fin - window_width/2
            right_offset = fin_to_fin - window_width/2
            
            idf.newidfobject(
            'SHADING:FIN:PROJECTION',
            Name=window_name +'fin',
            Window_or_Door_Name=window_name,
            Left_Extension_from_WindowDoor = left_offset,
            Right_Extension_from_WindowDoor = right_offset,
            Left_Tilt_Angle_from_WindowDoor = 90,
            Right_Tilt_Angle_from_WindowDoor = 90,
            Left_Depth_as_Fraction_of_WindowDoor_Width = sidefin_depth/window_width,
            Right_Depth_as_Fraction_of_WindowDoor_Width = sidefin_depth/window_width,
                
        )
        else: 
            idf.newidfobject(
            'SHADING:FIN:PROJECTION',
            Name=window_name +'fin',
            Window_or_Door_Name=window_name,
            Left_Tilt_Angle_from_WindowDoor = 90,
            Right_Tilt_Angle_from_WindowDoor = 90,
            Left_Depth_as_Fraction_of_WindowDoor_Width = sidefin_depth/fin_to_fin,
            Right_Depth_as_Fraction_of_WindowDoor_Width = sidefin_depth/fin_to_fin,
                
        )   

def calculate_area(coords):
    x = [coord[0] for coord in coords]
    y = [coord[1] for coord in coords]
    area = 0.5 * abs(sum(x[i] * y[i - 1] - x[i - 1] * y[i] for i in range(len(x))))
    return area

def load_assumptions(building_type,assumption='base'):
    script_dir = os.path.dirname(__file__)
    project_root = os.path.dirname(script_dir)
    resc_path = os.path.join(project_root, 'resource')
    
    parameters = []
    if assumption == 'base':
        assumption_path = os.path.join(resc_path, 'assumptions.csv')
        df = pd.read_csv(assumption_path)
        building_data = df[df['Building type'] == building_type]

        # Convert to python objects
        parameters = {
            key: float(pd.to_numeric(pd.Series([value]), errors='coerce').iloc[0])
            for key, value in building_data.drop(columns=['Building type']).iloc[0].to_dict().items()
        }

                
    elif assumption == 'transport':
        assumption_path = os.path.join(resc_path, 'transport_assumptions.csv')
        df = pd.read_csv(assumption_path)
        numeric_cols = ['Fraction', 'GHG Emissions', 'Distance']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df = df.set_index('Transport mode')
        parameters = df.to_dict(orient='index')
        
            
    elif assumption == 'embodied':
        assumption_path = os.path.join(resc_path, 'embodied_assumptions.csv')
        df = pd.read_csv(assumption_path)
        df = df.set_index('data')
        parameters = df.to_dict()  
    return parameters
    
def load_baseline():
    script_dir = os.path.dirname(__file__)
    project_root = os.path.dirname(script_dir)
    resc_path = os.path.join(project_root, 'resource')
    idf_file = os.path.join(resc_path, 'baseline.idf')
    outpath = os.path.join(resc_path, 'generated.idf')
    idd_file_path = os.path.join(resc_path, 'Energy+.idd')
    IDF.setiddname(idd_file_path)
    idf = IDF(idf_file)
    return idf, outpath

def set_schedules(idf, schedule):
    lights = idf.idfobjects["LIGHTS"][0]
    lights.Schedule_Name = schedule
    
    equip = idf.idfobjects["ELECTRICEQUIPMENT"][0]
    equip.Schedule_Name = schedule
    
    freshAir = idf.idfobjects["DESIGNSPECIFICATION:OUTDOORAIR"][0]
    freshAir.Outdoor_Air_Schedule_Name = schedule
    
    HVAC = idf.idfobjects["ZONEHVAC:IDEALLOADSAIRSYSTEM"][0]
    HVAC.Availability_Schedule_Name = schedule
    
    people = idf.idfobjects["PEOPLE"][0]
    people.Number_of_People_Schedule_Name = schedule
    
    
    return 0

def calculate_facade_area(walls,height):
    area = 0
    for wall in walls:
        x1 = wall['x1']
        x2 = wall['x2']
        y1 = wall['y1']
        y2 = wall['y2']
        distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        area += distance * height
    
    return area