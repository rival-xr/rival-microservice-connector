import os
import subprocess
import sys
# Some ffmpeg libraries mess with the terminal state, so we need to capture and restore it.
# They e.g. unset echo mode, so that when we type a command afterwards we don't see it.
#  FYI "stty echo" also restores it
def get_terminal_state():
    """Capture the current terminal state using stty -g."""
    if sys.platform == "win32":
        return None
    try:
        result = subprocess.run(["stty", "-g"], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error capturing terminal state: {e}", file=sys.stderr)
        return None

def set_terminal_state(state):
    """Restore the terminal state using stty."""
    if state:
        try:
            subprocess.run(["stty", state], check=True)
            print("Terminal state restored.")
        except subprocess.CalledProcessError as e:
            print(f"Error restoring terminal state: {e}", file=sys.stderr)
    else:
        print("No terminal state to restore.")