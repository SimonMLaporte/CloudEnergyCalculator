import csv
import matplotlib.pyplot as plt
import os
import math
from statistics import quantiles
import pandas as pd
import json
from ottv_calculations import calculate_OTTV


def extract_ep_results(inputJSON, assumptions, other_carbon):
    script_dir = os.path.dirname(__file__)
    project_root = os.path.dirname(script_dir)
    result_dir = os.path.join(project_root, 'output')
    result_file = os.path.join(result_dir, 'eplusout.csv')
    output_file_path = os.path.join(result_dir, 'output.json')
    assumptions_out_path = os.path.join(result_dir, 'used_assumptions.json')
    gfa = inputJSON["gfa"]
    COP = inputJSON["COP"]


    #Calculate OTTV & RTTV
    OTTV, RTTV = calculate_OTTV(inputJSON)

    # Extract energy use
    annual_cooling_demand = round(sum(get_csv_data(result_file,"DistrictCooling:Facility [J](Hourly)"))*2.78*math.pow(10,-7)/gfa,2)
    
    cooling_electricity = get_csv_data(result_file,"DistrictCooling:Facility [J](Hourly)")
    max_cooling_electricity = max([item *2.78*math.pow(10,-7)/COP for item in cooling_electricity])
    annual_cooling_electricity = round(sum(cooling_electricity)*2.78*math.pow(10,-7)/gfa/COP,2)
    
    lighting_electricity = get_csv_data(result_file,"main_lighting:InteriorLights:Electricity [J](Hourly)")
    max_lighting_electricity = max([item *2.78*math.pow(10,-7) for item in lighting_electricity])
    annual_lighting_electricity = round(sum(lighting_electricity)*2.78*math.pow(10,-7)/gfa,2)
    
    lift_electricity = get_csv_data(result_file,"lifts:InteriorEquipment:Electricity [J](Hourly)")
    
    equipment_electricity = get_csv_data(result_file,"main_equipment:InteriorEquipment:Electricity [J](Hourly)") + lift_electricity
    max_equipment_electricity = max([item *2.78*math.pow(10,-7) for item in equipment_electricity])
    annual_equipment_electricity = round(sum(equipment_electricity)*2.78*math.pow(10,-7)/gfa,2)
    
    carpark_electricity = get_csv_data(result_file,"carpark_lighting:InteriorLights:Electricity [J](Hourly)")+get_csv_data(result_file,"carpark_ventilation:InteriorEquipment:Electricity [J](Hourly)")
    max_carpark_electricity = max([item *2.78*math.pow(10,-7) for item in carpark_electricity])
    annual_carpark_electricity = round(sum(carpark_electricity)*2.78*math.pow(10,-7)/gfa,2)
    
    misc_electricity = assumptions['Miscellaneous (kWh/m2/year)']
    
    outdoor_lighting_electricity = get_csv_data(result_file,"facade_landscape_lighting:InteriorLights:Electricity [J](Hourly)")
    max_outdoor_lighting_electricity = max([item *2.78*math.pow(10,-7) for item in outdoor_lighting_electricity])
    annual_outdoor_lighting_electricity = round(sum(outdoor_lighting_electricity)*2.78*math.pow(10,-7)/gfa,2)
    annual_total_electricity = round(annual_cooling_electricity + annual_equipment_electricity +annual_lighting_electricity + annual_carpark_electricity + annual_outdoor_lighting_electricity,2)
    
    
    hour_by_hour_electricity = max_cooling_electricity + max_lighting_electricity + max_equipment_electricity + max_carpark_electricity + max_outdoor_lighting_electricity
    max_electricity_demand = round(hour_by_hour_electricity,2)
    
    #get the 98th percentile chiller load
    all_cooling_demands = get_csv_data(result_file,"DistrictCooling:Facility [J](Hourly)") #in J
    
    #remove zero cooling hours
    only_cooling_demands = [i for i in all_cooling_demands if i != 0]
    max_cooling_demands = round(quantiles(only_cooling_demands, n=100)[98]*2.78*math.pow(10,-7),2) # get the 98th percentile active cooling load in kW 
    
    #Extract EUI
    gridFactor = assumptions['Grid pollution (kgCO2e/kWh)']
    EUI_submission = round(annual_total_electricity ,2)
    EUI_average = float(assumptions['Average Malaysian EUI (kWh/m2/year)'])
    EUI_threshold = float(assumptions['1-star threshold EUI (kWh/m2/year)'])
    
    #Extract carbon emissions
    submission_operation = round(annual_total_electricity * gridFactor,2)
    submission_embodied = round(other_carbon['embodied_carbon_submission'],2)
    submission_transport = round(other_carbon['transport_carbon_submission'],2)
    average_operation =round(EUI_average * gridFactor,2)
    average_embodied = round(other_carbon['embodied_carbon_average'],2)
    average_transport = round(other_carbon['transport_carbon_reference'],2)
    threshold_operation = round(EUI_threshold * gridFactor)
    threshold_embodied = round(other_carbon['embodied_carbon_reference'],2)
    threshold_transport = round(other_carbon['transport_carbon_reference'],2)
    
    output= {
        "cooling_electricity":annual_cooling_electricity,
        "cooling_consumption":annual_cooling_demand,
        "lighting_indoor_electricity":annual_lighting_electricity,
        "equipment_electricity":annual_equipment_electricity,
        "carpark_electricity": annual_carpark_electricity, 
        "lighting_outdoor_electricity":annual_outdoor_lighting_electricity,
        "misc_electricity": misc_electricity,
        "total_electricity":annual_total_electricity,
        "max_electricity_demand": max_electricity_demand,
        "max_cooling_demand_kW": max_cooling_demands,
        "max_cooling_demand_RT": round(max_cooling_demands*0.284,2),
        "EUI_submission": EUI_submission,
        "EUI_average": round(EUI_average,2),
        "EUI_threshold": round(EUI_threshold,2),
        "submission_operation": submission_operation,
        "submission_embodied": submission_embodied,
        "submission_transport": round(float(submission_transport),2),
        "submission_carbon_footprint": round(submission_operation + submission_embodied + submission_transport,2),
        "average_operation": round(float(average_operation),2),
        "average_embodied": average_embodied,
        "average_transport": average_transport,
        "average_carbon_footprint": round(average_operation + average_embodied + average_transport,2),
        "threshold_operation": threshold_operation,
        "threshold_embodied": threshold_embodied,
        "threshold_transport": threshold_transport,
        "threshold_carbon_footprint": round(threshold_operation + threshold_embodied + threshold_transport,2),
        "renewable_production": round(inputJSON['renewable_energy'],2),
        "ottv": round(OTTV,2),
        "rttv": round(RTTV,2)  
    }
    with open(output_file_path, 'w') as output_file:
        json.dump(output, output_file,indent=2)
        
    with open(assumptions_out_path, 'w') as output_file:
        json.dump(assumptions, output_file,indent=2)
    return 1

def get_csv_data(csv_path,header):
    df = pd.read_csv(csv_path)
    return df[header].tolist()

def debug_show_ep_results():
    script_dir = os.path.dirname(__file__)
    project_root = os.path.dirname(script_dir)
    result_dir = os.path.join(project_root, 'output')
    result_file = os.path.join(result_dir, 'eplusout.csv')

    
    temp = []

    with open(result_file, 'r') as csvfile:
        temp = get_csv_data(result_file,"BLOCK MAIN STOREY 0:Zone Mean Air Temperature [C](Hourly)")[:24]

    # Create the line plot
    plt.figure(figsize=(12, 7))
    
    # Plot Column 2
    if temp:
        plt.plot(temp, marker='o', linestyle='-', label="room_temperature")
    

    plt.title(f'First 24 Values from {result_file.split(os.sep)[-1]}')
    plt.ylabel('Values')
    plt.grid(True)
    plt.legend() # Show the legend for multiple series
    plt.tight_layout() # Adjust layout to prevent labels from overlapping
    plt.show()
    
    return 0
        