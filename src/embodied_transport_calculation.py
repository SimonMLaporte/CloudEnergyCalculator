from generate_idf import load_assumptions

def transport_calc(assumption,build_area,total_pax,input):
 
    if input['building_type'] == 'office':
        #segment assumptions
        car = assumption['Car']
        motor = assumption['Motorcycle']
        bus = assumption['Bus']
        rail = assumption['Rail']
        walk = assumption['Walk/Cycle']
        
        annual_commute_days = 200    
        #one way emissions
        annual_transport_emissions = total_pax *annual_commute_days*(car['Fraction'] * car['GHG Emissions']*car['Distance']+
                                                                     motor['Fraction'] * motor['GHG Emissions']*motor['Distance']+
                                                                     bus['Fraction'] * bus['GHG Emissions']*bus['Distance']+
                                                                     rail['Fraction'] * rail['GHG Emissions']*rail['Distance']+
                                                                     walk['Fraction'] * walk['GHG Emissions']*walk['Distance']
                                                                     )/build_area/2
        
        return annual_transport_emissions
    else:
        return 'not valid for building type'
    

def embodied_calc(assumptions,build_area,input):
    # kgCo2e/ton
    rc = assumptions['Concrete + rebar'] * 1000
    green_rc = assumptions['Green concrete + rebar']  * 1000
    steel = assumptions['Steel']  * 1000
    green_steel = assumptions['Green steel']  * 1000
    glu_lam = assumptions['Glu-lam']  * 1000
    
    
    
    # building life-span in years
    building_lifespan = 50
    
    build_area = input['gfa'] + input['carpark_area_above_ground'] + input['carpark_area_above_ground']
    
    steel_emissions = steel * input['steel_usage'] * (1-input['green_steel_percent'])+ green_steel* input['green_steel_percent'] * input['steel_usage']
    concrete_emissions = rc * input['concrete_usage'] * (1-input['green_concrete_percent']) + green_rc * input['green_concrete_percent'] * input['concrete_usage']
    timber_emissions = glu_lam * input['timber_usage']

    total_annual_emissions =  ((steel_emissions + concrete_emissions + timber_emissions)/build_area) / building_lifespan
    return total_annual_emissions

    
    
def embodied_transport_emissions(input):
    build_area = input['gfa'] + input['carpark_area_above_ground'] + input['carpark_area_above_ground']
    assumptions = load_assumptions(input['building_type'])
    transport_assumptions = load_assumptions(input['building_type'],'transport')
    embodied_assumptions = load_assumptions(input['building_type'],'embodied')
    total_pax =   input['gfa'] /assumptions['People density (m2/pax AC area)']
    
    
    embodied_carbon = embodied_calc(embodied_assumptions, build_area,input)
    transport_carbon = transport_calc(transport_assumptions,build_area,total_pax,input)
    
    
    other_carbon = {
        "embodied_carbon": embodied_carbon,
        "transport_carbon": transport_carbon,
    }
    
    return other_carbon

