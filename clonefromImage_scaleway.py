import time
import json
import requests
from colorama import init, Fore, Style

init()

with open(r'MJ-API', 'r', encoding="UTF-8") as json_file:
    APIS = json.load(json_file)

SCALEWAY_API = "https://api.scaleway.com/instance/v1/zones"
HEADERS = {
    "X-Auth-Token": APIS["scaleway_token"],
    "Content-Type": "application/json"
}

ZONES = {
    "1": "fr-par-1",
    "2": "fr-par-2",
    "3": "fr-par-3",
    "4": "nl-ams-1",
    "5": "nl-ams-2",
    "6": "nl-ams-3",
    "7": "pl-waw-1",
    "8": "pl-waw-2",
    "9": "pl-waw-3"
}

def list_images(zone):
    url = f"{SCALEWAY_API}/{zone}/images"
    r = requests.get(url, headers=HEADERS)
    if r.status_code != 200:
        print(f"{Fore.RED}Error listing images: {r.text}{Style.RESET_ALL}")
        return []
    images = r.json().get("images", [])
    private = [img for img in images if img.get("root_volume")]
    return private

def create_instance(zone, image_id, count):
    url = f"{SCALEWAY_API}/{zone}/servers"
    ips = []

    for k in range(count):
        payload = {
            "name": f"{APIS['domain']}-{k+1}",
            "dynamic_ip_required": True,
            "commercial_type": "DEV1-S",
            "image": image_id,
            "enable_ipv6": False,
            "project": APIS.get("scaleway_project", ""),
            "tags": ["mailer", "postfix"]
        }

        r = requests.post(url, headers=HEADERS, json=payload)
        if r.status_code != 201:
            print(f"{Fore.RED}Failed to create instance {k+1}: {r.text}{Style.RESET_ALL}")
            continue

        server = r.json()["server"]
        server_id = server["id"]

        # Power on
        power_url = f"{SCALEWAY_API}/{zone}/servers/{server_id}/action"
        requests.post(power_url, headers=HEADERS, json={"action": "poweron"})

        print(f"{Fore.GREEN}[{k+1}/{count}] Created: {server_id}{Style.RESET_ALL}")

        if (k+1) % 10 == 0:
            print(f"{Fore.YELLOW}Sleeping 30s...{Style.RESET_ALL}")
            time.sleep(30)

    # Wait for IPs
    print(f"\n{Fore.CYAN}Waiting for IPs...{Style.RESET_ALL}")
    time.sleep(60)

    servers_url = f"{SCALEWAY_API}/{zone}/servers"
    r = requests.get(servers_url, headers=HEADERS)
    servers = r.json().get("servers", [])

    print(f"\n{Fore.CYAN}=== IPs ==={Style.RESET_ALL}")
    for i, srv in enumerate(servers, 1):
        ip = srv.get("public_ip", {}).get("address", "N/A")
        if ip != "N/A":
            ips.append(ip)
            print(f"[{i}] {srv['name']} → {ip}")

    # Save to runningips.txt
    with open("runningips.txt", "w") as f:
        for ip in ips:
            f.write(ip + "\n")

    print(f"\n{Fore.GREEN}✅ Saved {len(ips)} IPs to runningips.txt{Style.RESET_ALL}")
    return ips

# MENU
print("-----------------------------------------------")
print("         Scaleway Instance Creator")
print("-----------------------------------------------")

print("Zones:")
for k, v in ZONES.items():
    print(f"  {k}. {v}")

zone_choice = input("\nZone? ")
zone = ZONES.get(zone_choice, "fr-par-1")

print(f"\nFetching images from {zone}...")
images = list_images(zone)

if not images:
    print("No images found.")
    exit(1)

for i, img in enumerate(images, 1):
    print(f"{i}. {img['name']} ({img['id']})")

img_choice = int(input("\nImage? ")) - 1
image_id = images[img_choice]["id"]

count = int(input("ch7al mne instance? "))

print(f"\nCreating {count} instances...")
create_instance(zone, image_id, count)
print(f"{Fore.GREEN}+Done{Style.RESET_ALL}")