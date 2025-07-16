import os

SCRIPT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
RESOURCE_PATH= os.path.join(PROJECT_ROOT, 'resource')
DEBUG_JSON = os.path.join(RESOURCE_PATH, '250710_interface.json')
OUTPUT_PATH =os.path.join(PROJECT_ROOT, 'output')