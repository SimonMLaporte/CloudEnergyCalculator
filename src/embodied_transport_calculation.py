from generate_idf import load_assumptions

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
    

def embodied_calc(building_type,assumptions,build_area,input):
    # kgCo2e/ton
    rc = float(assumptions['Emission factor']['Concrete + rebar']) * 1000
    green_rc = float(assumptions['Emission factor']['Green concrete + rebar'])  * 1000
    steel = float(assumptions['Emission factor']['Steel'])  * 1000
    green_steel = float(assumptions['Emission factor']['Green steel'])  * 1000
    glu_lam = float(assumptions['Emission factor']['Glu-lam'])  * 1000
    
   
    
    # building life-span in years
    building_lifespan = 50
    
    build_area = input['gfa'] + input['carpark_area_above_ground'] + input['carpark_area_above_ground']
     #Quantities ton/m2
    ref_steel = float(assumptions[building_type]['Steel'])/1000
    ref_rc = float(assumptions[building_type]['Concrete + rebar'])/1000
    ref_glu_lam = float(assumptions[building_type]['Glu-lam'])/1000
    
    #reference emissions
    reference_steel = ref_steel * steel
    reference_rc = ref_rc * rc
    reference_glu_lam = ref_glu_lam * glu_lam
    
    
    # Submissions
    steel_emissions = steel * input['steel_usage'] * (1-input['green_steel_percent'])+ green_steel* input['green_steel_percent'] * input['steel_usage']
    concrete_emissions = rc * input['concrete_usage'] * (1-input['green_concrete_percent']) + green_rc * input['green_concrete_percent'] * input['concrete_usage']
    timber_emissions = glu_lam * input['timber_usage']

    reference_emissions = (reference_steel + reference_rc + reference_glu_lam) / building_lifespan
    total_annual_emissions =  ((steel_emissions + concrete_emissions + timber_emissions)/build_area) / building_lifespan
    return  reference_emissions, total_annual_emissions#reference_embodied,

    
    
def embodied_transport_emissions(input):
    build_area = input['gfa'] + input['carpark_area_above_ground'] + input['carpark_area_above_ground']
    assumptions = load_assumptions(input['building_type'])
    transport_assumptions = load_assumptions(input['building_type'],'transport')
    embodied_assumptions = load_assumptions(input['building_type'],'embodied')
    total_pax =   input['gfa'] /assumptions['People density (m2/pax AC area)']
    embodied_carbon_reference, embodied_carbon = embodied_calc(input['building_type'],embodied_assumptions, build_area,input)
    transport_carbon_reference, transport_carbon = transport_calc(transport_assumptions,build_area,total_pax,input)
    
    
    other_carbon = {
        "embodied_carbon_reference": embodied_carbon_reference,
        "embodied_carbon_submission": embodied_carbon,
        "transport_carbon_reference": transport_carbon_reference,
        "transport_carbon_submission": transport_carbon,
    }
    
    return other_carbon

