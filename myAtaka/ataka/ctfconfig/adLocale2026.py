
import json
import time
import requests
from pwn import *

from ataka.common.flag_status import FlagStatus

### EXPORTED CONFIG

# Ataka Host Domain / IP    
ATAKA_HOST = "127.0.0.1:8000"

# Default targets for atk runlocal
RUNLOCAL_TARGETS = [
    # NOP Team
    "10.66.15.1",
]

# Default targets for atk runremote
STATIC_EXCLUSIONS = {
    "10.66.6.1", #TODO: Set our ip here
}

ROUND_TIME = 120

# format: regex, group where group 0 means the whole regex
FLAG_REGEX = r"ptm[A-Z0-9]{28}=", 0

FLAG_BATCHSIZE = 200 # Maximum list length for submit_flags()

FLAG_RATELIMIT = 60 # Minimum wait in seconds between each call of submit_flags()

START_TIME = 1777033800 # First time -> When the CTF starts, set to 1 minute in the future for testing

### END EXPORTED CONFIG

TEAM_TOKEN = "1017955b2de5061a"

SUBMIT_URL = {"URL": "10.10.0.1", "PORT": 31337}
FLAGID_URL = "http://10.10.0.1/api/client/attack_data"


def _fetch_flag_ids():
    # Implement your logic to fetch flag IDs here
    try:
        response = requests.get(FLAGID_URL, timeout=1)
        data = response.json()
        print(f"Fetched {len(data)} flag IDs")
        return data
    except Exception as e:
        print(f"Got error while fetching flag IDs: {e}")
        return {}


def get_targets():
    # Implement your logic to fetch targets here
    try:
        flag_ids = _fetch_flag_ids()
        targets = {}
        for service_name, services_data in flag_ids.items():
                try:
                    targets[service_name] = []
                    for target_ip, team_data in services_data.items():

                        if target_ip in STATIC_EXCLUSIONS:
                            continue
                        # Add target with flag IDs in extra
                        targets[service_name].append({
                            "ip": target_ip,
                            #TODO: Gestire i dati extra -> team_data
                            "extra": json.dumps(team_data),
                        })
                except Exception as e:
                    print(f"Got error while processing service {service_name}: {e}") 
                    continue
        return targets
    except Exception as e:
        print(f"Got error while fetching targets: {e}")
        return ""

def submit_flags(flags):
    
    if not TEAM_TOKEN:
        print("TEAM_TOKEN not set! Cannot submit flags.")
        return [FlagStatus.ERROR] * len(flags)
    try:
        conn = remote(SUBMIT_URL["URL"], SUBMIT_URL["PORT"], timeout=5)
        conn.recvline()
        conn.sendline(TEAM_TOKEN.encode())
        #TODO: Aggingere eccezione
        response = conn.recvline().decode().strip()
        if not response.startswith("Now enter your flags"):
            print(f"Unexpected response from flag submission server: {response}")
            return [FlagStatus.ERROR] * len(flags)
        results = []
        for flag in flags:
            conn.sendline(flag.encode())
            flag_resp = conn.recvline().decode()  # Consume the response for each flag
            if "Flag accepted!" in flag_resp:
                status = FlagStatus.OK
            elif "Flag is invalid or too old" in flag_resp:
                status = FlagStatus.INVALID
            elif "Flag is your own" in flag_resp:
                status = FlagStatus.OWNFLAG
            else:
                status = FlagStatus.ERROR
                print(f"Got error while flagsubmission: {flag_resp}")
            results.append(status)
        conn.close()
        return results       
        
    except Exception as e:
        print(f"Got error while submitting flags: {e}")
        return [FlagStatus.ERROR] * len(flags)




