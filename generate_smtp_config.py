import json

with open(r'MJ-API', 'r', encoding="UTF-8") as json_file:
    APIS = json.load(json_file)

with open("runningips.txt", "r") as f:
    ips = [line.strip() for line in f if line.strip()]

password = APIS.get("password", "root")
domain = APIS.get("domain", "example.com")

with open("smtp_config.txt", "w") as f:
    for ip in ips:
        # Format: IP:PORT:USER:PASS:SSL/TLS:BCC/NOBCC
        line = f"{ip}:587:root@{domain}:{password}:TLS:NOBCC"
        f.write(line + "\n")

print(f"✅ Generated {len(ips)} SMTP lines in smtp_config.txt")
print("\nCopy paste content of smtp_config.txt into PHP mailer 'SMTP CONFIG' textarea")