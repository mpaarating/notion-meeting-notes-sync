# Insert Meeting Notes into Notion Database

## Prerequisites

Ensure you have the following installed:

- Python 3.10 or higher
- pip (Python package manager)

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/mpaarating/notion-meeting-notes-sync.git
   cd notion-meeting-notes-sync
   ```

2. **Create a virtual environment:**

   ```bash
   python -m venv notion_env
   ```

3. **Activate the virtual environment:**

   - On Windows:

     ```bash
     .\notion_env\Scripts\activate
     ```

   - On macOS and Linux:

     ```bash
     source notion_env/bin/activate
     ```

4. **Install the dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. **Create a `.env` file** in the root directory of your project using the provided `.env.example` as a template:

   ```plaintext
   NOTION_TOKEN=your_notion_token
   DATABASE_ID=your_database_id
   WATCH_DIRECTORY=/path/to/your/watch/directory
   LOG_FILE=/path/to/your/log/file.log
   ```

   - `NOTION_TOKEN`: Your Notion integration token (see [Notion API Documentation](https://developers.notion.com/docs/getting-started))
   - `DATABASE_ID`: The ID of your Notion database (found in the database URL)
   - `WATCH_DIRECTORY`: The directory where your meeting notes will be saved
   - `LOG_FILE`: The location where the script will write its logs

2. **Directory Structure**

   The script expects the following directory structure:

   ```
   notion-meeting-notes-sync/
   ├── .env
   ├── .env.example
   ├── watch_meeting_notes.py
   ├── get_notion_database_schema.py
   ├── notion_schema.json
   └── logs/
       └── notion-meeting-notes-sync.log

   # In your cloud storage:
   ~/Dropbox/meeting_notes/          # Your WATCH_DIRECTORY (example)
   └── your_meeting_notes.txt
   ```

3. **Watch Directory Setup**

   The watch directory (`WATCH_DIRECTORY`) is where you'll save your meeting notes text files. This should typically be a directory within your cloud storage service (like Dropbox, Google Drive, or OneDrive) to enable automatic syncing of meeting notes. The script will:
   - Automatically create this directory if it doesn't exist
   - Monitor this directory for new `.txt` files
   - Process any new files and upload them to Notion

   Example directory paths:
   - macOS: `/Users/username/Dropbox/meeting_notes` or `/Users/username/Google Drive/meeting_notes`
   - Windows: `C:\Users\username\Dropbox\meeting_notes` or `C:\Users\username\Google Drive\meeting_notes`
   - Linux: `/home/username/Dropbox/meeting_notes` or `/home/username/google-drive/meeting_notes`

4. **Log File Configuration**

   The log file (`LOG_FILE`) helps you monitor the script's operation:
   - Logs are written in a human-readable format with timestamps
   - The script will create the necessary directories for the log file
   - Log entries include file processing status and any errors

   Example log file paths:
   - macOS: `/Users/username/Library/Logs/notion-meeting-notes-sync.log`
   - Windows: `C:\Users\username\AppData\Local\notion-meeting-notes-sync.log`
   - Linux: `/var/log/notion-meeting-notes-sync.log`

5. **File Permissions**

   Ensure that:
   - The script has read/write access to the watch directory
   - The script has write access to the log file location
   - On Unix-like systems (macOS/Linux), you may need to set appropriate permissions:

     ```bash
     # Set permissions for watch directory
     chmod 755 /path/to/your/watch/directory
     
     # Set permissions for log directory
     sudo mkdir -p /path/to/your/logs
     sudo chown $USER:$USER /path/to/your/logs
     chmod 755 /path/to/your/logs
     ```

6. **Testing Your Configuration**

   To verify your setup:
   1. Create a test meeting note in your watch directory:

      ```bash
      echo "Test meeting note" > /path/to/your/watch/directory/test_meeting.txt
      ```

   2. Check the log file for processing status:

      ```bash
      tail -f /path/to/your/log/file.log
      ```

   3. Verify that the note appears in your Notion database

2. **Generate the Notion Schema**

   Run the schema generator to create your `notion_schema.json`:
   ```bash
   python get_notion_database_schema.py
   ```
   This will create a schema file based on your Notion database structure. An example schema is provided in `notion_schema.example.json`.

   The schema file contains the structure of your Notion database, including:
   - Required fields (Name, Date of Meeting, Platform)
   - Available meeting types and their colors
   - Available platforms and their colors

## Running the Project

### Using `screen` (macOS/Linux)

`screen` is a terminal multiplexer that allows you to run long-term processes in the background. It's particularly useful for:

- **Development and Testing**: If you're actively developing or testing your script and need to monitor its output or interact with it, `screen` provides an easy way to keep the process running even if you disconnect from your terminal.

- **Temporary Tasks**: For tasks that don't need to start automatically on boot or run continuously, `screen` is a quick and simple solution.

- **Session Management**: `screen` allows you to detach and reattach to sessions, making it easy to check on your process without interrupting it.

#### Instructions for Using `screen`

1. Start a new screen session:

   ```bash
   screen -S notion-meeting-notes-sync
   ```

2. Run the script:

   ```bash
   python watch_meeting_notes.py
   ```

3. Detach from the screen session by pressing `Ctrl+A` followed by `D`.

4. To reattach to the session, use:

   ```bash
   screen -r notion-meeting-notes-sync
   ```

### Running as a System Service (Linux)

1. Create a systemd service file:

   ```bash
   sudo nano /etc/systemd/system/meeting-notes-watcher.service
   ```

2. Add the following content to the file:

   ```ini
   [Unit]
   Description=Meeting Notes Watcher

   [Service]
   ExecStart=/path/to/your/venv/bin/python /path/to/your/watch_meeting_notes.py
   WorkingDirectory=/path/to/your/project
   Environment="PYTHONUNBUFFERED=1"
   User=your_username
   Group=your_groupname
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

   Replace `/path/to/your/venv/bin/python`, `/path/to/your/watch_meeting_notes.py`, `/path/to/your/project`, `your_username`, and `your_groupname` with your actual paths and user details.

3. Reload systemd and start the service:

   ```bash
   sudo systemctl daemon-reload
   sudo systemctl start meeting-notes-watcher.service
   sudo systemctl enable meeting-notes-watcher.service
   ```

4. Check the status of the service:

   ```bash
   sudo systemctl status meeting-notes-watcher.service
   ```

### Using a Launch Daemon (macOS)

A `launch daemon` is more suitable for:

- **Production Environments**: When you need your script to run continuously and start automatically on system boot, a launch daemon provides a robust solution.

- **System Integration**: `launchd` is the native service manager for macOS, offering better integration with the system, including automatic restarts and logging.

- **No User Interaction**: If the script doesn't require user interaction and should run independently, a launch daemon is a better fit.

#### Instructions for Setting Up a Launch Daemon

1. **Create a Launch Daemon plist file:**

   Create a new plist file in `/Library/LaunchDaemons/`. You will need administrative privileges to do this.

   ```bash
   sudo nano /Library/LaunchDaemons/com.yourusername.notion-meeting-notes-sync.plist
   ```

2. **Add the following content to the plist file:**

   ```xml
   <?xml version="1.0" encoding="UTF-8"?>
   <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
   <plist version="1.0">
   <dict>
       <key>Label</key>
       <string>com.yourusername.notion-meeting-notes-sync</string>
       <key>ProgramArguments</key>
       <array>
           <string>/path/to/your/venv/bin/python</string>
           <string>/path/to/your/watch_meeting_notes.py</string>
       </array>
       <key>WorkingDirectory</key>
       <string>/path/to/your/project</string>
       <key>RunAtLoad</key>
       <true/>
       <key>KeepAlive</key>
       <true/>
       <key>StandardOutPath</key>
       <string>/path/to/your/logs/notion-meeting-notes-sync.log</string>
       <key>StandardErrorPath</key>
       <string>/path/to/your/logs/notion-meeting-notes-sync.log</string>
   </dict>
   </plist>
   ```

   Replace `/path/to/your/venv/bin/python`, `/path/to/your/watch_meeting_notes.py`, `/path/to/your/project`, and `/path/to/your/logs/notion-meeting-notes-sync.log` with your actual paths.

3. **Load the Launch Daemon:**

   ```bash
   sudo launchctl load /Library/LaunchDaemons/com.yourusername.notion-meeting-notes-sync.plist
   ```

4. **Check the status of the Launch Daemon:**

   ```bash
   sudo launchctl list | grep com.yourusername.notion-meeting-notes-sync
   ```

5. **Unload the Launch Daemon (if needed):**

   ```bash
   sudo launchctl unload /Library/LaunchDaemons/com.yourusername.notion-meeting-notes-sync.plist
   ```

## Why Use `screen` on macOS?

When running long-term processes on macOS, you have several options, including using `screen`, `tmux`, or creating a system service. Here's why you might choose `screen`:

- **Session Persistence**: `screen` allows you to detach and reattach to sessions, which is useful if you need to disconnect from your terminal or if your SSH connection drops. This ensures that your process continues running in the background.

- **Simplicity**: Setting up `screen` is straightforward and doesn't require additional configuration files or permissions, unlike creating a system service with `launchd` or using third-party applets.

- **Portability**: `screen` is available on most Unix-like systems, making it a versatile tool if you work across different environments. This can be advantageous if you are familiar with `screen` and want to use the same tool on both macOS and Linux.

- **No Root Access Required**: Unlike setting up a system service, which may require administrative privileges, `screen` can be used by any user without special permissions.

- **Resource Efficiency**: `screen` is lightweight and doesn't consume significant system resources, making it suitable for running background tasks without impacting system performance.

While `screen` is a powerful tool, you might consider alternatives like `tmux` for more advanced session management features or `launchd` for more integrated system service management on macOS. Choose the tool that best fits your workflow and project requirements.

## Troubleshooting

- Ensure that the `.env` file is correctly configured and accessible.
- Check the log file specified in the `.env` file for any errors or warnings.
- Ensure that the Notion API token and database ID are correct and have the necessary permissions.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
