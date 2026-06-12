import sys
import io
import pycurl
from bs4 import BeautifulSoup
from pathlib import Path
import os
import notify2
from time import sleep
import subprocess
import json

global matrixPing, matrixUserToPing, matrixUserServer, matrixRoom

state_dir = Path(
    os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state")
) / "nixpkgs-notifier"
state_dir.mkdir(parents=True, exist_ok=True)

trackedPRPath = state_dir / "tracked.txt"
trackedPRFile = Path(trackedPRPath)

config_dir = Path(
    os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
) / "nixpkgs-notifier"

configPath = config_dir / "config.json"
configFile = Path(configPath)

# parse config file
DEFAULT_CONFIG = {
    "configTime": 3600,
    "configFetchTime": 1,
    "localNotify": True,
    "matrix": {
        "enable": False,
        "room": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "ping": False,
        "userPing": "@someone",
        "userPingServer": "matrix.org"
    }
}

def getPRTitle(PRnumber):
    buf = io.BytesIO()

    c = pycurl.Curl()
    c.setopt(
        c.URL,
        f"https://api.github.com/repos/NixOS/nixpkgs/pulls/{PRnumber}"
    )
    c.setopt(c.USERAGENT, "pycurl")
    c.setopt(c.WRITEDATA, buf)
    c.perform()
    c.close()

    return json.loads(buf.getvalue())["title"]

def load_config():
    config_dir.mkdir(parents=True, exist_ok=True)

    if not configFile.exists():
        with configFile.open("w") as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)
        return DEFAULT_CONFIG

    try:
        with configFile.open("r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print("Config file is broken. Using default config.")
        return DEFAULT_CONFIG

def addTracker(PRnumber):
    result = fetchStatus(PRnumber)
    if result == "accepted":
        print("PR " + str(PRnumber) + " was already merged into nixos-unstable.")
    elif result == "not_found":
        print("PR " + str(PRnumber) + " not found.")
    elif result == "unknown":
        print("PR " + str(PRnumber) + " returned unknown status.")
    elif result == "pending":
        with trackedPRFile.open("a") as f:
            f.write(f"{PRnumber}\n")
    print("Added tracked PR " + str(PRnumber) + " " + getPRTitle(PRnumber))

def removeTracker(PRnumber):
    if not trackedPRFile.exists():
        return

    with trackedPRFile.open("r") as f:
        lines = f.readlines()

    with trackedPRFile.open("w") as f:
        for line in lines:
            if line.strip() != str(PRnumber):
                f.write(line)

    print("Removed tracked PR " + str(PRnumber) + " " + getPRTitle(PRnumber))

def localNotify(PRnumber):
    notify2.init("nixpkgs-tracker-notify")

    notification = notify2.Notification(
        "nixpkgs PR merged",
        "PR #" + str(PRnumber) + " " +  getPRTitle(PRnumber) + "\n" 
        "is now available in nixos-unstable.\n"
        f"https://nixpk.gs/pr-tracker.html?pr={PRnumber}",
    )

    notification.show()

def matrix_check_whoami():
    try:
        result = subprocess.run(
            ["matrix-commander-rs", "--whoami"],
            capture_output=True,
            text=True,
            check=True
        )

        output = result.stdout.strip()

        if output.startswith("@"):
            return output  # OK, proceed
        else:
            print(f"Error: invalid identity returned: {output}")
            return None

    except FileNotFoundError:
        print("Error: matrix-commander-rs not found in PATH.")
        return None

    except subprocess.CalledProcessError as e:
        print(f"Error: command failed with exit code {e.returncode}")
        print(e.stderr.strip())
        return None

def matrixNotify(PRnumber):
    if matrix_check_whoami():
        command = "matrix-commander-rs -m \"PR #" + str(PRnumber) + "  " + getPRTitle(PRnumber) + " is now available in nixos-unstable.\nhttps://nixpk.gs/pr-tracker.html?pr=" + str(PRnumber)
        if matrixPing:
            command += '\n<a href=\\"https://matrix.to/#/' + matrixUserToPing + ':' + matrixUserServer + '\\">' + matrixUserToPing + '</a>\" --html'
        else:
            command += "\""
        command += " -r \"" + matrixRoom + "\""
        subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True
        )
def fetchStatus(PRnumber):
    buf = io.BytesIO()

    c = pycurl.Curl()
    c.setopt(c.URL, f"https://nixpk.gs/pr-tracker.html?pr={PRnumber}")
    c.setopt(c.WRITEDATA, buf)
    c.perform()
    c.close()

    soup = BeautifulSoup(buf.getvalue(), "html.parser")

    # Check if the PR does not exist
    no_pr_msg = soup.find(
        string=lambda s: s and f"No such nixpkgs PR #{PRnumber}" in s
    )
    if no_pr_msg:
        return "not_found"

    # Check nixos-unstable status
    for a in soup.find_all("a"):
        if a.get_text(strip=True) == "nixos-unstable":
            span = a.find_parent("li").find("span")
            classes = span.get("class", [])

            if "state-accepted" in classes:
                return "accepted"
            elif "state-pending" in classes:
                return "pending"
            elif "state-rejected" in classes:
                return "rejected"
            else:
                return "unknown"

    return "unknown"

def main():
    # fetch config
    cfg = load_config()
    configTime = cfg["configTime"]
    configFetchTime = cfg["configFetchTime"]
    shouldLocalNotify = cfg["localNotify"]
    shouldMatrixNotify = cfg["matrix"]["enable"]
    matrixRoom = cfg["matrix"]["room"]
    matrixPing = cfg["matrix"]["ping"]
    matrixUserToPing = cfg["matrix"]["userPing"]
    matrixUserServer = cfg["matrix"]["userPingServer"]
    
    
    if len(sys.argv) < 2:
        print("Missing command")
        sys.exit(1)
    if sys.argv[1] == "add":
        for PR in sys.argv:
            if PR != sys.argv[0] and PR != sys.argv[1]:
                try:
                    PR = int(PR)
                    addTracker(PR)
                except ValueError:
                    print(f"{PR} is not an int")
                    continue
            sleep(configFetchTime) # avoid spamming requests
    
    
    elif sys.argv[1] == "remove" or sys.argv[1] == "rm":
        for PR in sys.argv:
            if PR != sys.argv[0] and PR != sys.argv[1]:
                try:
                    PR = int(PR)
                    removeTracker(PR)
                except ValueError:
                    print(f"{PR} is not an int")
                    continue
            sleep(configFetchTime) # avoid spamming requests
    
    elif sys.argv[1] == "list" or sys.argv[1] == "ls":
        if not trackedPRFile.exists():
            print("No tracked PRs.")
        else:
            print("Tracked PRs:")
            with trackedPRFile.open("r") as f:
                for line in f:
                    pr = line.strip()
                    if pr:
                        print("  " + str(pr) + "  " + getPRTitle(pr))
    
elif sys.argv[1] == "listen":
    while True:
        try:
            if trackedPRFile.exists():
                # Read a snapshot of the file first so we don't modify
                # tracked.txt while iterating over it.
                with trackedPRFile.open("r") as f:
                    tracked_prs = []
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        tracked_prs.append(int(line))
                
                for PR in tracked_prs:
                    try:
                        status = fetchStatus(PR)

                        if status == "accepted":
                            print(f"PR #{PR} accepted")

                            if shouldLocalNotify:
                                localNotify(PR)
                            if shouldMatrixNotify:
                                matrixNotify(PR)
                            removeTracker(PR)
                            print(f"Removed PR #{PR} from tracking")

                    except Exception as e:
                        print(
                            f"Failed to process PR #{PR}: {e}"
                        )

                    # Avoid hammering the tracker website
                    sleep(configFetchTime)

        except Exception as e:
            print(f"Listener loop error: {e}")

        sleep(configTime)
    else:
        print("Unknown argument \"" + sys.argv[1] + "\"\nAccepted arguments are:\n    add\n    remove or rm\n    list or ls\n    listen")
    
    
