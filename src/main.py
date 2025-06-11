#This file contains the main project loop to be called by front end
from generate_idf import generate_idf
from ep_run import run_energyplus
from ep_utilities import extract_ep_results,debug_show_ep_results
from embodied_transport_calculation import embodied_transport_emissions
import json
import os

#testvalues
script_dir = os.path.dirname(__file__)
project_root = os.path.dirname(script_dir)
json_file_dir= os.path.join(project_root, 'resource')
debugJSON = os.path.join(json_file_dir, 'benchmark_building.json')
f = open(debugJSON)
inputJSON = json.load(f)

#run script
assumptions = generate_idf(inputJSON)
run_energyplus()
other_carbon = embodied_transport_emissions(inputJSON)
extract_ep_results(inputJSON, assumptions, other_carbon)
debug_show_ep_results()
