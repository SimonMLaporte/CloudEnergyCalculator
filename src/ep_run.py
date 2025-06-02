import os
from pyenergyplus.plugin import EnergyPlusPlugin
from geomeppy import IDF

def run_energyplus():
    #Load correct file paths
    script_dir = os.path.dirname(__file__)
    project_root = os.path.dirname(script_dir)
    weather_file_dir = os.path.join(project_root, 'weather_files')
    weather_file = os.path.join(weather_file_dir, 'KUALA_LUMPUR_MY-hour.epw')
    idf_file_dir= os.path.join(project_root, 'idf_files')
    idf_file = os.path.join(idf_file_dir, 'generated.idf')
    output_dir = os.path.join(project_root, 'output')
    resc_path = os.path.join(project_root, 'resource')
    idd_file_path = os.path.join(resc_path, 'Energy+.idd')
    IDF.setiddname(idd_file_path)
    idf = IDF(idf_file,weather_file)

    # Run simulation
    idf.run(annual=True, output_directory=output_dir)
