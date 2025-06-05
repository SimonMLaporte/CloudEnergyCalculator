import os
from pyenergyplus.plugin import EnergyPlusPlugin
from geomeppy import IDF

def run_energyplus():
    #Load correct file paths
    script_dir = os.path.dirname(__file__)
    project_root = os.path.dirname(script_dir)
    resc_path = os.path.join(project_root, 'resource')
    weather_file = os.path.join(resc_path, 'KUALA_LUMPUR_MY-hour.epw')
    idf_file = os.path.join(resc_path, 'generated.idf')
    output_dir = os.path.join(project_root, 'output')
    idd_file_path = os.path.join(resc_path, 'Energy+.idd')
    IDF.setiddname(idd_file_path)
    idf = IDF(idf_file,weather_file)

    # Run simulation
    idf.run(annual=True, output_directory=output_dir)
