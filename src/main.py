#This file contains the main project loop to be called by front end
from generate_idf import generate_idf
from ep_run import run_energyplus
from ep_utilities import extract_ep_results,debug_show_ep_results
import json
import os

#testvalues
script_dir = os.path.dirname(__file__)
project_root = os.path.dirname(script_dir)
json_file_dir= os.path.join(project_root, 'resource')
debugJSON = os.path.join(json_file_dir, 'sample_input.json')
f = open(debugJSON)
inputJSON = json.load(f)

#Load assumptions
buildingtype = inputJSON['building_type']
assumption_file = buildingtype + "_assumptions.json"
assumption_path = os.path.join(json_file_dir, assumption_file)
f = open(assumption_path)
assumptions = json.load(f)


#run script
generate_idf(inputJSON,assumptions)
run_energyplus()
extract_ep_results(inputJSON)
debug_show_ep_results()
