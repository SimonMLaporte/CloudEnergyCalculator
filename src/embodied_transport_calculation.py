from generate_idf import load_assumptions, calculate_glazing_area

def transport_calc(assumption,build_area,total_pax,input):
 
    if input['building_type'] == 'office':
        #segment assumptions
        car = assumption['Car']
        motor = assumption['Motorcycle']
        taxi = assumption['Taxi/e-hailing']
        bus = assumption['Bus']
        rail = assumption['Rail']
        walk = assumption['Walk/Cycle']
        EV = assumption['EV']
        E_motorcycle = assumption['E_Motorcycle']
        annual_commute_days = 220    
        #one way emissions
        annual_transport_emissions_ref = total_pax *annual_commute_days*(car['Fraction'] * car['GHG Emissions']*car['Distance']+
                                                                     motor['Fraction'] * motor['GHG Emissions']*motor['Distance']+
                                                                     bus['Fraction'] * bus['GHG Emissions']*bus['Distance']+
                                                                     rail['Fraction'] * rail['GHG Emissions']*rail['Distance']+
                                                                     walk['Fraction'] * walk['GHG Emissions']*walk['Distance']+
                                                                     taxi['Fraction'] * taxi['GHG Emissions']*taxi['Distance']
                                                                     )/build_area/2
        car = {
            "Fraction": input['commute_by_car'],
            "Distance": input['commute_distance_by_car'],
            "GHG Emissions": car['GHG Emissions']
            }
        e_car = {
            "Fraction": input['commute_by_ev'],
            "Distance": input['commute_distance_by_ev'],
            "GHG Emissions": EV['GHG Emissions']
            }
        motor = {
            "Fraction": input['commute_by_motor_bike'],
            "Distance": input['commute_distance_by_motor_bike'],
            "GHG Emissions": motor['GHG Emissions']
            }
        e_motor = {
            "Fraction": input['commute_by_e_motor_bike'],
            "Distance": input['commute_distance_by_e_motor_bike'],
            "GHG Emissions": E_motorcycle['GHG Emissions']
            }
        
        rail = {
            "Fraction": input['commute_by_rail'],
            "Distance": input['commute_distance_by_rail'],
            "GHG Emissions": rail['GHG Emissions']
        }
        bus = {
            "Fraction": input['commute_by_bus'],
            "Distance": input['commute_distance_by_bus'],
            "GHG Emissions": bus['GHG Emissions']
            }
        taxi = {
            "Fraction": input['commute_by_taxi'],
            "Distance": input['commute_distance_by_taxi'],
            "GHG Emissions": bus['GHG Emissions']
            
        }
        #One way emissions
        annual_transport_emissions = total_pax *annual_commute_days*(car['Fraction'] * car['GHG Emissions']*car['Distance']+
                                                                motor['Fraction'] * motor['GHG Emissions']*motor['Distance']+
                                                                rail['Fraction'] * rail['GHG Emissions']*rail['Distance']+
                                                                taxi['Fraction'] * taxi['GHG Emissions']*taxi['Distance']+
                                                                bus['Fraction'] * bus['GHG Emissions']*bus['Distance']+
                                                                e_car['Fraction'] * e_car['GHG Emissions'] * e_car['Distance']+
                                                                e_motor['Fraction'] * e_motor['GHG Emissions'] * e_motor['Distance']
                                                                )/build_area/2
        
        
        
        return annual_transport_emissions_ref, annual_transport_emissions 
    else:
        return 0,0 # transportation carbon not valid for building types
    

def embodied_calc(building_type,assumptions,input):
    # kgCo2e/m2
    structural_system = float(assumptions[building_type][input['structural_system']]) # multiplied by GFA
    wall_system = float(assumptions[building_type][input['wall_system']]) # multipplied by GFA
    roof_system = float(assumptions[building_type][input['roof_system']]) # multiplied by roof area
    glazing_system = float(assumptions[building_type][input['glazing_system']]) # multiplied by glazing area
    carpark_above_ground = float(assumptions['carpark_above_ground'][input['structural_system']]) # multiplied by carpark area
    carpark_below_ground = float(assumptions['carpark_below_ground'][input['structural_system']]) # multiplied by carpark area
    height_adjusetment_factor = float(assumptions['height_adjustment']['height_adjustment'])
    height_adjustment = (input['height']-50)*height_adjusetment_factor/100 # percent change based on ratio counting from 50m
    benchmark = float(assumptions[building_type]['threshold'])
    
    if input['structural_system'] == 'reinforced_concrete':
        green_percent = input['green_concrete_percent']
        green_value = float(assumptions[building_type]['reinforced_concrete_green'])
        structural_system = green_percent * green_value + (1-green_percent)*structural_system
        
    elif input['structural_system'] == 'structural_steel':
        green_percent = input['green_concrete_percent']
        green_value = float(assumptions[building_type]['structural_steel_green'])
        structural_system = green_percent * green_value + (1-green_percent)*structural_system
        

    
    # building life-span in years based on structural system
    building_lifespan = float(assumptions['building_lifespan'][input['structural_system']])
    
    #Areas
    gfa = input['gfa'] 
    carpark_above_ground_area = input['carpark_area_above_ground']
    carpark_below_ground_area = input['carpark_area_below_ground']
    glazing = calculate_glazing_area(input['walls'],input['height'])
    roof = input['footprint']
    built_area = gfa + carpark_above_ground_area + carpark_below_ground_area
    
    emissions = (
    (structural_system * gfa 
    + wall_system * gfa 
    + roof_system * roof 
    + glazing_system * glazing 
    + carpark_below_ground_area * carpark_below_ground 
    + carpark_above_ground_area * carpark_above_ground) 
    * (1+height_adjustment) / building_lifespan) /built_area
    threshold_emissions = benchmark * (1+height_adjustment) / building_lifespan
    average_emissions = threshold_emissions/1.25 # assumed 25% lower
    
    return  threshold_emissions, average_emissions, emissions #reference_embodied,

    
    
def embodied_transport_emissions(input):
    build_area = input['gfa'] + input['carpark_area_above_ground'] + input['carpark_area_above_ground']
    assumptions = load_assumptions(input['building_type'])
    transport_assumptions = load_assumptions(input['building_type'],'transport')
    embodied_assumptions = load_assumptions(input['building_type'],'embodied')
    total_pax = input['gfa'] /assumptions['People density (m2/pax AC area)']
    embodied_carbon_reference, average_carbon,embodied_carbon = embodied_calc(input['building_type'],embodied_assumptions,input)
    transport_carbon_reference, transport_carbon = transport_calc(transport_assumptions,build_area,total_pax,input)
    
    
    other_carbon = {
        "embodied_carbon_reference": embodied_carbon_reference,
        "embodied_carbon_average": average_carbon,
        "embodied_carbon_submission": embodied_carbon,
        "transport_carbon_reference": transport_carbon_reference,
        "transport_carbon_submission": transport_carbon,
    }
    
    return other_carbon
