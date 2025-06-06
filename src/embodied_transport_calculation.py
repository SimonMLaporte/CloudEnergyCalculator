from generate_idf import load_assumptions

def transport_calc(input,build_area,total_pax):

    if input['building_type'] == 'office':
        #kgco2/km - this should be assumptions 
        car_emission_factor = 1
        motor_emission_factor = 1
        lowCo2_emission_factor =1
        diversity_factor = 1
        annual_commute_days = 200    
        annual_transport_emissions = total_pax * diversity_factor * annual_commute_days*(input['commute_by_car'] * input['commute_distance_by_car']* motor_emission_factor
                                    +input['commute_by_car'] * input['commute_distance_by_car'] * car_emission_factor
                                    +input['commutelow3Co2']* input['commute_distance_by_lowCo2'] *lowCo2_emission_factor)/build_area
        
        return annual_transport_emissions
    else:
        return 'not valid for building type'
    

def embodied_calc(input,build_area):
    # kgCo2e/ton - get malaysian values - this should be in assumptions
    carbon_emission_factor_steel = 1
    carbon_emission_factor_concrete = 1
    carbon_emission_factor_timber = 1
    
    # building life-span in years
    building_lifespan = {
        'reinforced_concrete': 1, 
        'steel': 1,
        'low_strucutral_wood': 1,
        'high_structural_wood': 1
    }
    
    green_concrete_emission_factor = 1
    green_steel_emission_factor = 1
    
    build_area = input['gfa'] + input['carpark_area_above_ground'] + input['carpark_area_above_ground']
    
    steel_emissions = carbon_emission_factor_steel * input['steel_usage'] * (1-input['green_steel_percent'])+ green_steel_emission_factor * input['green_steel_percent'] * input['steel_usage']
    concrete_emissions = carbon_emission_factor_concrete * input['concrete_usage'] * (1-input['green_concrete_percent']) + green_concrete_emission_factor * input['green_concrete_percent'] * input['concrete_usage']
    timber_emissions = carbon_emission_factor_timber * input['timber_usage']

    total_annual_emissions =  ((steel_emissions + concrete_emissions + timber_emissions)/build_area) / building_lifespan[input['structural_system']]
    return total_annual_emissions

    
    
def embodied_transport_emissions(input):
    build_area = input['gfa'] + input['carpark_area_above_ground'] + input['carpark_area_above_ground']
    people_density = load_assumptions(input['building_type'])
    total_pax =  people_density * input['gfa']
    
    
    embodied_carbon = embodied_calc(input, build_area)
    transport_carbon = transport_calc(input,build_area,total_pax)
    
    
    other_carbon = {
        "embodied_carbon": embodied_carbon,
        "transport_carbon": transport_carbon,
        "transport_carbon": transport_carbon,
    }
    
    return other_carbon
    