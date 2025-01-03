import requests
import json
import logging
from dotenv import load_dotenv
import os

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s"
)

# Load environment variables
load_dotenv()

# Get credentials from environment variables
NOTION_TOKEN = os.getenv('NOTION_TOKEN')
DATABASE_ID = os.getenv('DATABASE_ID')
LOG_FILE = os.getenv('LOG_FILE')

if not NOTION_TOKEN or not DATABASE_ID:
    raise ValueError("Missing required environment variables: NOTION_TOKEN and DATABASE_ID")

# Add after loading environment variables
log_directory = os.path.dirname(LOG_FILE)
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

def fetch_notion_schema():
    """
    Fetches the schema of the specified Notion database.
    """
    url = f'https://api.notion.com/v1/databases/{DATABASE_ID}'
    headers = {
        'Authorization': f'Bearer {NOTION_TOKEN}',
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        database_info = response.json()

        # Extract the 'properties' field, which contains the schema
        schema = database_info.get('properties', {})
        if not schema:
            logging.error("No properties found in the database schema.")
            return None

        return schema

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch database schema: {e}")
        return None

def write_schema_to_file(schema, output_file='notion_schema.json'):
    """
    Writes the schema to a JSON file.
    """
    try:
        with open(output_file, 'w') as f:
            json.dump(schema, f, indent=4)
        logging.info(f"Schema successfully written to {output_file}.")
    except IOError as e:
        logging.error(f"Failed to write schema to file: {e}")

def validate_required_fields(schema):
    """
    Validates that the required fields exist in the schema.
    """
    required_fields = ["Name", "Date of Meeting", "Platform"]
    missing_fields = [field for field in required_fields if field not in schema]
    if missing_fields:
        logging.error(f"Missing required fields in schema: {', '.join(missing_fields)}")
        return False
    return True

if __name__ == "__main__":
    logging.info("Fetching Notion database schema...")
    schema = fetch_notion_schema()

    if schema:
        # Validate schema before writing
        if validate_required_fields(schema):
            write_schema_to_file(schema)
        else:
            logging.error("Schema validation failed. Please check the database.")