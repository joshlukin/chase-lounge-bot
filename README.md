# chase-lounge-bot

Python script that uses Selenium to monitor the Chase Lounge reservation portal and auto-reserve qualifying events (e.g., New York Rangers games).

## Prerequisites
- Python 3.10+ installed
- Google Chrome

## Setup
1. (Recommended) Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # .venv\Scripts\activate on Windows
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create empty `credentials.txt` file
   Then edit `credentials.txt` so it contains:
   ```
   EMAIL: email@example.com
   PASSWORD: your-password
   ```
   > `credentials.txt` is ignored by Git.
4. Edit constant variables in 

## Usage
Run the watcher:
```bash
python main.py
```
The script logs in, repeatedly scans the Madison Square Garden events table, and clicks the first Rangers (or configured test) event with a blue "Reserve" button. It will attempt to reserve two tickets, acknowledge the confirmation dialog, and loop back to keep watching.
