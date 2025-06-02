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

    #add dummy building for additional loads (a 1x1x1 cube at -10 z)

    #Extract values from JSON
    width = inputJson["width"]
    length = inputJson["length"]
    height =inputJson["height"]
    gfa = inputJson['gfa']
    newLPD = inputJson["LPD"]
    eqiupment = assumptions["equipment_density"]
    peopleDensity = assumptions["design_people_density"]
    n_WWR = inputJson["n_WWR"]
    s_WWR = inputJson["s_WWR"]
    w_WWR = inputJson["w_WWR"]
    e_WWR = inputJson["e_WWR"]

    #Set Schedules


    # Set building size 
    set_building_dimensions(idf,length,width,height)

    # Add windows
    add_window('wall_n',n_WWR,idf)
    add_window('wall_s',s_WWR,idf)
    add_window('wall_w',w_WWR,idf)
    add_window('wall_e',e_WWR,idf)


    # Add shading
    
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

    #Set fresh air

    #Set constructions

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
    #vertices = selected.coords




    # Calculate area using eppy's geometry utility
    #wallArea = surface_area_calc(vertices)
    windowheight=selected.height*WWR




    #windowArea = WWR * wallArea
    #windowRatio = height/width
    #windowWidth = math.sqrt(windowArea/windowRatio)
    #windowHeight = windowWidth * windowRatio
    #numberWindows = math.ceil(windowHeight/selected.height)
    #actualHeight = windowHeight/numberWindows
    #actualWidth = actualHeight/windowRatio
    
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
def set_building_dimensions(idf,length,width,height):
    scaleX = width/10
    scaleY= length/10
    scaleZ=height/10
    idf.scale(scaleX,axes='x')
    idf.scale(scaleY,axes='y')
    idf.scale(scaleZ,axes='z')

    return 0
def add_shade(overhang_fraction,fins_fraction):
    return 0
def calculate_area(coords):
    x = [coord[0] for coord in coords]
    y = [coord[1] for coord in coords]
    area = 0.5 * abs(sum(x[i] * y[i - 1] - x[i - 1] * y[i] for i in range(len(x))))
    return area