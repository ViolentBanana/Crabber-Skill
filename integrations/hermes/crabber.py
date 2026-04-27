import os
import subprocess
import shlex

def handle(message):
    """
    Hermes Skill for Crabber.
    Expected message format or parameters should contain 'file_path'.
    """
    # Try to extract file_path from the message
    file_path = message.get("file_path")
    
    if not file_path:
        return "Error: file_path parameter is missing."
        
    crabber_bin = os.path.expanduser("~/.crabber/bin/crabber")
    
    if not os.path.exists(crabber_bin):
        return "Error: Crabber CLI is not installed or not found at ~/.crabber/bin/crabber"
        
    try:
        # Run crabber CLI
        cmd = [crabber_bin, file_path]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        # Returns the CLI output which includes the Markdown link
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Crabber CLI failed: {e.stderr.strip()}"
    except Exception as e:
        return f"Unexpected error running Crabber: {e}"

# For standalone testing
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        print(handle({"file_path": sys.argv[1]}))
    else:
        print("Usage: python crabber.py <file_path>")
