from colorama import Fore, Style, init
from dotenv import load_dotenv
import os

# Get the current script directory
current_dir = os.path.dirname(os.path.abspath(__file__))
# Build the full path to the .env file
env_path = os.path.join(current_dir, '.env')

# Load environment variables, specifying the .env file path
load_dotenv(env_path)
# Get the version number, using the default value if not found
version = os.getenv('VERSION', '1.0.0')

# Initialize colorama
init()