from geomeppy import IDF
import pandas as pd
import os



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
    width = inputJson["facade1_width"]
    length = inputJson["facade2_width"]
    height =inputJson["height"]
    facade_area = width *height *2 + length * height *2
    gfa = inputJson['gfa']
    n_WWR = inputJson["1_WWR"]
    e_WWR = inputJson["2_WWR"]
    s_WWR = inputJson["3_WWR"]
    w_WWR = inputJson["4_WWR"]
    NV = inputJson['NV_percent']
    
    
    
    #add dummy objects
    idf.newidfobject("LIGHTS",
                     Name = 'dummyLights',
                     Zone_or_ZoneList_or_Space_or_SpaceList_Name = 'dummyBlock',
                     Schedule_Name = schedule,
                     Lighting_Level = NV * gfa * inputJson["LPD"] * (1-inputJson['sDA']),
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

    # Set building size
    heightScale = height * (1-NV) 
    set_building_dimensions(idf,length,width,heightScale,inputJson["facade1_orientation"])

    # Add windows and shading
    n_name = add_window('wall_n',n_WWR,idf)
    add_shade(idf, n_name, inputJson["1_window_width"],inputJson["1_window_height"],inputJson["1_overhang_depth"],inputJson["1_sidefin_depth"], inputJson["1_fin-to-fin_distance"],inputJson["1_z_offset"])
    s_name = add_window('wall_s',s_WWR,idf)
    add_shade(idf, s_name, inputJson["3_window_width"],inputJson["3_window_height"],inputJson["3_overhang_depth"],inputJson["3_sidefin_depth"], inputJson["3_fin-to-fin_distance"],inputJson["3_z_offset"])
    w_name = add_window('wall_w',w_WWR,idf)
    add_shade(idf, w_name, inputJson["4_window_width"],inputJson["4_window_height"],inputJson["4_overhang_depth"],inputJson["4_sidefin_depth"], inputJson["4_fin-to-fin_distance"],inputJson["4_z_offset"])
    e_name = add_window('wall_e',e_WWR,idf)
    add_shade(idf, e_name, inputJson["2_window_width"],inputJson["2_window_height"],inputJson["2_overhang_depth"],inputJson["2_sidefin_depth"], inputJson["2_fin-to-fin_distance"],inputJson["2_z_offset"])
    roof_name = add_window('roof',inputJson['roof_WWR'],idf)
    
    
    # Set lighting
    newWatt = gfa*(1-NV) * (1-inputJson['sDA']) * inputJson["LPD"]
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
                Zone_or_ZoneList_Name = 'main',
                Surface_Area = gfa*(1-NV)
                )
    
    #Set constructions
    set_construction(idf, 'wall_n',n_name,inputJson['1_wall_u'],inputJson['1_albedo'],inputJson['1_glass_sc'],inputJson["1_glass_u"])
    set_construction(idf, 'wall_e',e_name,inputJson['2_wall_u'],inputJson['2_albedo'],inputJson['2_glass_sc'],inputJson["2_glass_u"])
    set_construction(idf, 'wall_s',s_name,inputJson['3_wall_u'],inputJson['3_albedo'],inputJson['3_glass_sc'],inputJson["3_glass_u"])
    set_construction(idf, 'wall_w',w_name,inputJson['4_wall_u'],inputJson['4_albedo'],inputJson['4_glass_sc'],inputJson["4_glass_u"])
    set_construction(idf, 'roof',roof_name,inputJson['roof_u'],inputJson['roof_albedo'],inputJson['roof_glass_sc'],inputJson["roof_glass_u"])
    
    #Save idf
    idf.saveas(outpath)
    return assumptions

def add_window(wallID,WWR,idf):
    #extract wall
    surfaces = idf.idfobjects["BUILDINGSURFACE:DETAILED"]
    selected = ''
    for s in surfaces:
        if s.Name == wallID:
            selected = s
    windowheight=selected.height*WWR

    if WWR>0:
        idf.newidfobject(
            'WINDOW',
            Name=wallID + "_window",
            Construction_Name='window',
            Building_Surface_Name=wallID,
            Starting_X_Coordinate=0,
            Starting_Z_Coordinate=0,
            Length=selected.width,
            Height=windowheight
            )
    return wallID + "_window"

def set_construction(idf, wallID,windowID, Uvalue, albedo, glassSC, glassU):
    
    #Add window constrction
    idf.newidfobject(
        'WINDOWMATERIAL:SIMPLEGLAZINGSYSTEM',
        Name = wallID + '_window_construction',
        UFactor = glassU,
        Solar_Heat_Gain_Coefficient = glassSC,
    )
    
    idf.newidfobject(
        'CONSTRUCTION',
        Name=wallID + '_window_construction',
        Outside_Layer=wallID + '_window_construction'
        )
    
    
    
    #Set window construction
    surfaces = idf.idfobjects["WINDOW"]
    selected = ''
    for s in surfaces:
        if s.Name == windowID:
            s.Construction_Name = wallID + '_window_construction'

    #Add wall construction
    
    #Add dummy material with correct solar absorbtance
    r_value = 1 / Uvalue 

    # 2. Calculate Solar Absorptance from Albedo
    solar_absorptance = 1.0 - albedo

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
    
    scaleX = width/10
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
        
        idf.newidfobject(
            'SHADING:FIN:PROJECTION',
            Name=window_name +'fin',
            Window_or_Door_Name=window_name,
            Left_Tilt_Angle_from_WindowDoor = 90,
            Right_Tilt_Angle_from_WindowDoor = 90,
            Left_Depth_as_Fraction_of_WindowDoor_Width = sidefin_depth/window_width,
            Right_Depth_as_Fraction_of_WindowDoor_Width = sidefin_depth/window_width,
                
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
        values = df.iloc[0]
        parameters = values.to_dict()  
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
    