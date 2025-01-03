from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
from dotenv import load_dotenv
import logging
import requests
import json
from datetime import datetime
import time
import platform

# Load environment variables
load_dotenv()

# Get credentials from environment variables
NOTION_TOKEN = os.getenv('NOTION_TOKEN')
DATABASE_ID = os.getenv('DATABASE_ID')
WATCH_DIRECTORY = os.getenv('WATCH_DIRECTORY')
LOG_FILE = os.getenv('LOG_FILE')

# Validate required environment variables
required_env_vars = ['NOTION_TOKEN', 'DATABASE_ID', 'WATCH_DIRECTORY', 'LOG_FILE']
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

# Load Notion schema from file
def load_notion_schema(schema_file='notion_schema.json'):
    try:
        with open(schema_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error("Schema file not found. Run `get_notion_database_schema.py` first.")
        return {}
    except json.JSONDecodeError as e:
        logging.error(f"Failed to decode schema file: {e}")
        return {}

# Validate schema for required fields
def validate_schema(schema):
    required_fields = ["Name", "Date of Meeting", "Platform"]
    missing_fields = [field for field in required_fields if field not in schema]
    if missing_fields:
        raise ValueError(f"Missing required fields in schema: {', '.join(missing_fields)}")

def detect_meeting_type(transcript_content):
    keywords = {
        "standup": "Standup",
        "client": "Client Meeting",
        "review": "Code Review",
    }
    for keyword, meeting_type in keywords.items():
        if keyword in transcript_content.lower():
            return meeting_type
    return "General Meeting"  # Default fallback

class MeetingNotesHandler(FileSystemEventHandler):
    def __init__(self, schema):
        self.schema = schema
        self.notion_token = NOTION_TOKEN
        self.database_id = DATABASE_ID
        self.processed_files = set()  # Track processed files
        
    def create_notion_page(self, title, meeting_date, meeting_platform, meeting_type):
        url = "https://api.notion.com/v1/pages"
        headers = {
            "Authorization": f"Bearer {self.notion_token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        current_time = datetime.now().astimezone()
        formatted_date = f"{meeting_date}T12:00:00{current_time.strftime('%z')}"
        page_title = title.replace('.txt', '')
        
        data = {
            "parent": {"database_id": self.database_id},
            "properties": {
                "Name": {
                    "title": [{"text": {"content": page_title}}]
                },
                "Date of Meeting": {
                    "date": {"start": formatted_date}
                },
                "Platform": {
                    "select": {"name": meeting_platform}
                },
                "Meeting Type": {
                    "select": {"name": meeting_type}
                },
                "AI summary": {
                    "rich_text": [{"text": {"content": "Placeholder summary to trigger AI."}}]
                }
            }
        }
        
        response = requests.post(url, headers=headers, json=data)
        if not response.ok:
            logging.error(f"Notion API Error: {response.status_code}")
            logging.error(f"Response: {response.text}")
            response.raise_for_status()
        
        return response.json()

    def update_page_with_transcript(self, page_id, transcript_content):
        url = f"https://api.notion.com/v1/blocks/{page_id}/children"
        headers = {
            "Authorization": f"Bearer {self.notion_token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        # Split content into chunks of 2000 characters
        content_chunks = [transcript_content[i:i+2000] for i in range(0, len(transcript_content), 2000)]
        
        # Create blocks for each chunk
        content_blocks = [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "Meeting Transcript"}}]
                }
            }
        ]
        
        for chunk in content_chunks:
            content_blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": chunk}
                    }]
                }
            })
        
        data = {
            "children": content_blocks
        }
        
        response = requests.patch(url, headers=headers, json=data)
        if not response.ok:
            logging.error(f"Notion API Error: {response.status_code}")
            logging.error(f"Response: {response.text}")
            response.raise_for_status()
        
        return response.json()

    def upload_to_notion(self, title, meeting_date, meeting_platform, file_path):
        try:
            with open(file_path, 'r') as f:
                transcript_content = f.read()
        except Exception as e:
            logging.error(f"Failed to read file content: {e}")
            return {}
        
        meeting_type = detect_meeting_type(transcript_content)
        
        page_response = self.create_notion_page(title, meeting_date, meeting_platform, meeting_type)
        page_id = page_response.get('id')
        
        if not page_id:
            return page_response
        
        time.sleep(2)
        
        return self.update_page_with_transcript(page_id, transcript_content)

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.txt'):
            file_name = os.path.basename(event.src_path)
            
            # Skip if we've already processed this file
            if file_name in self.processed_files:
                return
                
            logging.info(f"New meeting note detected: {event.src_path}")
            
            # Wait for file to be fully synced
            time.sleep(5)
            
            try:
                # 1. Get file creation time with fallbacks
                try:
                    if platform.system() == 'Windows':
                        created_timestamp = os.path.getctime(event.src_path)
                    else:
                        stat = os.stat(event.src_path)
                        try:
                            created_timestamp = stat.st_birthtime  # macOS
                        except AttributeError:
                            created_timestamp = stat.st_mtime  # Linux and others
                    
                    created_date = datetime.fromtimestamp(created_timestamp)
                    formatted_date = created_date.strftime("%Y-%m-%d")
                except Exception as e:
                    logging.warning(f"Failed to get file date, using today: {e}")
                    formatted_date = datetime.now().strftime("%Y-%m-%d")
                
                # 2. Generate a clean title
                clean_title = file_name.replace('.txt', '')
                
                # 3. Set default platform first
                notion_platform = 'Zoom'  # Default platform
                
                # Try to detect platform from filename
                platform_keywords = {
                    'zoom': 'Zoom',
                    'meet': 'Google Meet',
                    'slack': 'Slack',
                    'teams': 'Zoom',  # map Teams to Zoom
                    'webex': 'Zoom',  # map Webex to Zoom
                }
                
                # Look for platform keywords in filename
                file_lower = clean_title.lower()
                for keyword, mapped_platform in platform_keywords.items():
                    if keyword in file_lower:
                        notion_platform = mapped_platform
                        break
                
                # Upload to Notion
                self.upload_to_notion(
                    title=clean_title,
                    meeting_date=formatted_date,
                    meeting_platform=notion_platform,
                    file_path=event.src_path
                )
                
                # Mark file as processed
                self.processed_files.add(file_name)
                logging.info(f"Successfully uploaded {file_name} to Notion")
                
            except Exception as e:
                logging.error(f"Error processing file {file_name}: {e}")

if __name__ == "__main__":
    schema = load_notion_schema()
    validate_schema(schema)
    
    event_handler = MeetingNotesHandler(schema)
    observer = Observer()
    
    # Add error handling for observer
    try:
        observer.schedule(event_handler, path=WATCH_DIRECTORY, recursive=False)
        observer.start()
        logging.info(f"Monitoring {WATCH_DIRECTORY} for new meeting notes...")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            logging.info("Stopped monitoring.")
            
    except OSError as e:
        logging.error(f"Failed to monitor directory: {e}")
        if "No such file or directory" in str(e):
            logging.error(f"Please make sure {WATCH_DIRECTORY} exists and is accessible")
    finally:
        observer.join()