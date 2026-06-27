
import json
import time
import requests

from ataka.common.flag_status import FlagStatus

### EXPORTED CONFIG

# Ataka Host Domain / IP    
ATAKA_HOST = "127.0.0.1:8000"

# Default targets for atk runlocal
RUNLOCAL_TARGETS = [
    # NOP Team
    "10.60.0.1",
]

# Default targets for atk runremote
STATIC_EXCLUSIONS = {
    "10.60.5.1", #TODO: Set our ip here
}

ROUND_TIME = 120

# format: regex, group where group 0 means the whole regex
FLAG_REGEX = r"[A-Z0-9]{31}=", 0

FLAG_BATCHSIZE = 200 # Maximum list length for submit_flags()

FLAG_RATELIMIT = 2 # Minimum wait in seconds between each call of submit_flags()

START_TIME = 1781942100 # First time -> When the CTF starts, set to 1 minute in the future for testing

#START_TIME = 1778241600 # Second time 
### END EXPORTED CONFIG

TEAM_TOKEN = "728fcfe9e2eb1c493899adac2be82328"

SUBMIT_URL = "http://10.10.0.1:8080/flags"
FLAGID_URL = "http://10.10.0.1:8081/flagIds"
SERVICE_URL = "http://10.10.0.1:8081/"


def _decode_flag(flag):
    # Implement your flag decoding logic here
    round_number = int(flag[0:2], 36)
    team_number = int(flag[2:4], 36)
    service_number = int(flag[4:6], 36)
    return round_number, team_number, service_number


def _fetch_service():
    
    # Implement your logic to fetch service information here
    try:
        response = requests.get(SERVICE_URL, timeout=5)
        data = response.json()
        services = {}
        for service in data.get("services", []):
            services[service['shortname']] = service['shortname']
        print(f"Fetched {len(services)} services: {services}")
        return services
    except Exception as e:
        print(f"Got error while flagsubmission: {e}")
        return {}

def _fetch_flag_ids():
    # Implement your logic to fetch flag IDs here
    try:
        response = requests.get(FLAGID_URL, timeout=5)
        data = response.json()
        flag_ids = {}
        print(f"Fetched {len(flag_ids)} flag IDs")
        return data
    except Exception as e:
        print(f"Got error while fetching flag IDs: {e}")
        return {}

def _send_to_discord(game_responses):
    """
    Riceve un ARRAY di oggetti JSON dal server di gioco:
    [
      { "msg": "flag claimed", "flag": "...", "status": "ACCEPTED" },
      { "msg": "too old", "flag": "...", "status": "DENIED" }
    ]
    """
    # Se questo è il Webhook di Discord, lo script scriverà direttamente nel canale.
    webhook_url = "https://discord.com/api/webhooks/1488657124325068922/Ym31WOUTFmhtRJdBu3cSmXEy-eCuWs_BkjQzwPfyDyslXV47AaQQEwOEgZnEQZGXDWX3"
    
    if not game_responses:
        return

    lines = []
    for res in game_responses:
        flag = res.get('flag', 'INVALID')
        status = res.get('status', 'ERROR')
        full_msg = res.get('msg', 'No message')

        # 1. Decodifica metadati (Base 36)
        try:
            r_num, t_num, s_id = _decode_flag(flag)
            identity = f"S:{s_id}|T:{t_num}|R:{r_num}"
        except:
            identity = "??? Metadata"

        # 2. Icona dinamica
        s = status.upper()
        emoji = "✅" if "ACCEPTED" in s else "❌" if "DENIED" in s else "⏳" if "RESUBMIT" in s else "⚠️"

        # 3. Costruzione della riga (compatta)
        line = f"{emoji} **{identity}** ▸ `{status}` ▸ {full_msg}"
        lines.append(line)

    # 4. Raggruppamento (Discord ha un limite di 2000 caratteri per messaggio)
    # Uniamo le righe in blocchi di 10 per non fare troppe richieste
    chunk_size = 10 
    for i in range(0, len(lines), chunk_size):
        chunk = lines[i:i + chunk_size]
        payload = {
            "content": "\n".join(chunk) # Unisce le righe con un a capo
        }

        try:
            r = requests.post(webhook_url, json=payload, timeout=5)
            if r.status_code == 429: # Rate limit di Discord
                print("[-] Discord sta frenando... aspetto 5 secondi.")
                time.sleep(5)
                requests.post(webhook_url, json=payload)
            print(f"[+] Inviato blocco di {len(chunk)} notifiche.")
        except Exception as e:
            print(f"[-] Errore invio: {e}")

def get_targets():
    # Implement your logic to fetch targets here
    try:
        flag_ids = _fetch_flag_ids()
        targets = {}
        for service_name, services_data in flag_ids.items():
                try:
                    targets[service_name] = []

                    for team_id, team_data in services_data.items():
                        team_id = int(team_id)
                        target_ip = f"10.60.{team_id}.1"

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
        headers={'X-Team-Token': TEAM_TOKEN}
        response = requests.put(SUBMIT_URL, headers=headers, json=flags, timeout=5).json()
        #_send_to_discord(response)
        results = []
        for flag_resp in response:
            msg = flag_resp["msg"]
            if flag_resp["status"] == 'ACCEPTED':
                status = FlagStatus.OK
            elif "invalid flag" in msg or "the check which dispatched this flag didn't terminate successfully" in msg:
                status = FlagStatus.INVALID
            elif "flag from nop team" in msg:
                status = FlagStatus.INACTIVE
            elif "flag is your own" in msg:
                status = FlagStatus.OWNFLAG
            elif "flag too old" in msg or "flag is too old" in msg:
                status = FlagStatus.INACTIVE
            elif "flag already claimed" in msg:
                status = FlagStatus.DUPLICATE
            elif "the flag is not active yet, wait for next round" in msg:
                status = FlagStatus.INACTIVE
            else:
                status = FlagStatus.ERROR
                print(f"Got error while flagsubmission: {msg}")
            results.append(status)
        return results
    except Exception as e:
        print(f"Got error while submitting flags: {e}")
        return [FlagStatus.ERROR] * len(flags)




