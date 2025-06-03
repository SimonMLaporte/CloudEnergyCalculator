from geomeppy import IDF
from eppy.geometry.surface import area as surface_area_calc
import os
import math


def generate_idf(inputJson,assumptions):
    script_dir = os.path.dirname(__file__)
    project_root = os.path.dirname(script_dir)
    idf_file_dir= os.path.join(project_root, 'idf_files')
    resc_path = os.path.join(project_root, 'resource')
    idf_file = os.path.join(idf_file_dir, 'baseline.idf')
    outpath = os.path.join(idf_file_dir, 'generated.idf')
    idd_file_path = os.path.join(resc_path, 'Energy+.idd')
    IDF.setiddname(idd_file_path)
    idf = IDF(idf_file)

    #add dummy building for additional loads
    idf.add_block(name="dummyBlock",coordinates=[(-500,-500), (-500,-499), (-499,-499), (-499,-500)],height=1)
    idf.set_default_constructions()
    idf.intersect_match()

    #Extract values from JSON
    width = inputJson["facade1_width"]
    length = inputJson["facade2_width"]
    height =inputJson["height"]
    gfa = inputJson['gfa']
    newLPD = inputJson["LPD"]
    eqiupment = assumptions["equipment_density"]
    peopleDensity = assumptions["design_people_density"]
    n_WWR = inputJson["1_WWR"]
    e_WWR = inputJson["2_WWR"]
    s_WWR = inputJson["3_WWR"]
    w_WWR = inputJson["4_WWR"]

    #Set Schedules


    # Set building size 
    set_building_dimensions(idf,length,width,height,inputJson["facade1_orientation"])

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
    newWatt = gfa * newLPD
    lights = idf.idfobjects["LIGHTS"]
    lights[0].Lighting_Level = newWatt
    
    # Set other lighting
    ## Carpark, outdoor, facade
    
    
    
    # Set equipment
    newEquip = gfa * eqiupment
    equip = idf.idfobjects["ELECTRICEQUIPMENT"]
    equip[0].Design_Level = newEquip

    #Set lift

    # Set people
    newPeople = gfa / peopleDensity
    people = idf.idfobjects["PEOPLE"]
    people[0].Number_of_People = newPeople

    #Set fresh air rate

    #Set constructions
    set_construction(idf, 'wall_n',n_name,inputJson['1_wall_u'],inputJson['1_albedo'],inputJson['1_glass_sc'],inputJson["1_glass_u"])
    set_construction(idf, 'wall_e',e_name,inputJson['2_wall_u'],inputJson['2_albedo'],inputJson['2_glass_sc'],inputJson["2_glass_u"])
    set_construction(idf, 'wall_s',s_name,inputJson['3_wall_u'],inputJson['3_albedo'],inputJson['3_glass_sc'],inputJson["3_glass_u"])
    set_construction(idf, 'wall_w',w_name,inputJson['4_wall_u'],inputJson['4_albedo'],inputJson['4_glass_sc'],inputJson["4_glass_u"])
    set_construction(idf, 'roof',roof_name,inputJson['roof_u'],inputJson['roof_albedo'],inputJson['roof_glass_sc'],inputJson["roof_glass_u"])
    
    #Save idf
    idf.saveas(outpath)
    return 

def add_window(wallID,WWR,idf):
    #extract wall
    surfaces = idf.idfobjects["BUILDINGSURFACE:DETAILED"]
    selected = ''
    for s in surfaces:
        if s.Name == wallID:
            selected = s
    windowheight=selected.height*WWR

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