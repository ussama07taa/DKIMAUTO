import CloudFlare
import json
import random
import string
from colorama import init as colorama_init
from colorama import Fore
from colorama import Style
import paramiko
import time

with open(r'MJ-API', 'r', encoding="UTF-8") as json_file:
    APIS = json.load(json_file)

cf = CloudFlare.CloudFlare(email=APIS['cf_email'], key=APIS['cf_key'])
ipszaz = "runningips.txt"
ip_subdomain = "ip_subdomain.bin"
username = "root"
opendkim_conf = "opendkim.conf"
opendkim_def = "opendkim"
postfix_config = """
# Milter configuration
# DKIM
milter_default_action = accept
milter_protocol = 2
smtpd_milters = local:/opendkim/opendkim.sock
non_smtpd_milters = local:/opendkim/opendkim.sock
"""


def subdomain():
    with open(ipszaz, 'r') as f:
        ips = f.readlines()

    subdomain_perip = []
    for i, ip in enumerate(ips):
        subdomain = '' + ''.join(random.choices(string.ascii_lowercase, k=3))
        subdomain_perip.append(subdomain)
    with open(ip_subdomain, 'w') as f:
        for subdomain, ip in zip(subdomain_perip, ips):
            f.write(f'{subdomain}:{ip}')


dns_records_created = False  # Guard to only create DNS records once

if __name__ == "__main__":
    colorama_init()
    subdomain()
    with open(ip_subdomain, 'r') as f:
        file = f.readlines()

    for info_dns in file:

        row = info_dns.split(':')
        HostName = row[0]
        Address = row[1].strip()

        Ip_redirect = '185.47.174.250'

        trusted_hosts = f"""
                127.0.0.1
                localhost
                {APIS["domain"]}
                *.{APIS["domain"]}
        """

        print(f"{Fore.RED}------------------------------------------------- {Style.RESET_ALL}")
        print(f"{Fore.GREEN}Server with ip: {Address} is connected! ---- {APIS['domain']} {Style.RESET_ALL}!")
        print(f"{Fore.RED}------------------------------------------------- {Style.RESET_ALL}")

        try:
            commands = [
                f'hostnamectl set-hostname {APIS["domain"]}',
                'apt-get -o "Dpkg::Options::=--force-confold" install opendkim -y --allow-downgrades --allow-remove-essential --allow-change-held-packages',
                'apt-get install opendkim-tools -y',
                f'debconf-set-selections <<< "postfix postfix/mailname string {APIS["domain"]}"',
                'debconf-set-selections <<< "postfix postfix/main_mailer_type string \'Internet Site\'"',
                'apt-get install --assume-yes postfix',
                'adduser postfix opendkim',
                'chmod u=rw,go=r /etc/opendkim.conf',
                f'mkdir -p /etc/opendkim/keys/{APIS["domain"]}',
                f'echo "*@{APIS["domain"]}      default._domainkey.{APIS["domain"]}" > /etc/opendkim/signing.table',
                f'echo "default._domainkey.{APIS["domain"]}     {APIS["domain"]}:default:/etc/opendkim/keys/{APIS["domain"]}/default.private" > /etc/opendkim/key.table',
                f'printf "{trusted_hosts}" > /etc/opendkim/trusted.hosts',
                f'opendkim-genkey -b 2048 -d {APIS["domain"]} -D /etc/opendkim/keys/{APIS["domain"]} -s default -v',
                'chown -R opendkim:opendkim /etc/opendkim && chmod go-rw /etc/opendkim/keys',
                'mkdir -p /var/spool/postfix/opendkim',
                'chown opendkim:postfix /var/spool/postfix/opendkim',
                f'cat <<EOF >> /etc/postfix/main.cf\n{postfix_config}\nEOF',
                f'sudo sed -i "s/myhostname = .*/myhostname = {APIS["domain"]}/" /etc/postfix/main.cf',
                f'sudo sed -i "s/myorigin = .*/myorigin = {APIS["domain"]}/" /etc/postfix/main.cf',
                'systemctl enable postfix && systemctl enable opendkim.service',
                'systemctl restart postfix && systemctl restart opendkim.service',
                'systemctl status opendkim.service',
                f'openssl rsa -in /etc/opendkim/keys/{APIS["domain"]}/default.private -pubout -out {APIS["domain"]}',
                'apt install mailutils -y',
                'systemctl restart postfix && systemctl restart opendkim.service',
            ]

            create_config_dns = [
                f'cat {APIS["domain"]} | tr -d "\\n"'
            ]

            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname=Address, username=username, password=APIS["password"])

            sftp = ssh.open_sftp()
            sftp.put(opendkim_conf, '/etc/opendkim.conf')
            print(f"{Fore.RED}------------------------------------------------- {Style.RESET_ALL}")
            print(f"{Fore.GREEN}the file: {opendkim_conf} is copied successfully! ---- {Address} {Style.RESET_ALL}!")
            print(f"{Fore.RED}------------------------------------------------- {Style.RESET_ALL}")

            sftp.put(opendkim_def, '/etc/default/opendkim')
            print(f"{Fore.RED}------------------------------------------------- {Style.RESET_ALL}")
            print(f"{Fore.GREEN}the file: {opendkim_def} is copied successfully! ---- {Address} {Style.RESET_ALL}!")
            print(f"{Fore.RED}------------------------------------------------- {Style.RESET_ALL}")
            sftp.close()

            for command in commands:
                print(command)
                with open(f'tmp/{Address}', 'w') as f:
                    f.write('\n'.join(commands))
                stdin, stdout, stderr = ssh.exec_command(command)
                for line in stdout:
                    print(line.strip())

            for dns_create in create_config_dns:
                print(dns_create)
                stdin, stdout, stderr = ssh.exec_command(dns_create)
                for read_privatkey in stdout:
                    out_public = read_privatkey.strip()
                    private_keyy = out_public.replace('-----BEGIN PUBLIC KEY-----', '')
                    private_key = private_keyy.replace('-----END PUBLIC KEY-----', '')
                    time.sleep(1)

                    # Only create DNS records once across all servers
                    if not dns_records_created:
                        dns_records = [
                            {'name': f'{APIS["domain"]}',                        'type': 'A',   'content': Ip_redirect},
                            {'name': f'mail.{APIS["domain"]}',                   'type': 'A',   'content': Address},
                            {'name': f'{APIS["domain"]}',                        'type': 'MX',  'content': f'mail.{APIS["domain"]}', 'priority': 10},
                            {'name': f'default._domainkey.{APIS["domain"]}',     'type': 'TXT', 'content': f'v=DKIM1; k=rsa; p={private_key}'},
                            {'name': f'_dmarc.{APIS["domain"]}',                 'type': 'TXT', 'content': f'v=DMARC1; p=reject; sp=reject; adkim=s; aspf=s; rf=afrf; pct=100; ri=86400'},
                            {'name': f'{APIS["domain"]}',                        'type': 'TXT', 'content': f'v=spf1 include:spf_{APIS["domain"]} -all'},
                            {'name': f'spf_{APIS["domain"]}',                    'type': 'TXT', 'content': f'v=spf1 mx a ip4:164.92.186.234 ip4:3.64.237.196 +all'},
                        ]

                        print(f"{Fore.RED}------------------------------------------------- {Style.RESET_ALL}")
                        print(f"{Fore.GREEN}Creating DNS records for: {APIS['domain']} ---- {Address} {Style.RESET_ALL}!")
                        print(f"{Fore.RED}------------------------------------------------- {Style.RESET_ALL}")

                        print('Create DNS records ...')
                        zones = cf.zones.get()
                        zone_id = "f0e16b4238ba908ab029d3a8232bec29"

                        for zone in zones:
                            if zone['name'] == APIS["domain"]:
                                zone_id = zone['id']
                                break

                        for dns_record in dns_records:
                            r = cf.zones.dns_records.post(zone_id, data=dns_record)
                            echo_record = r
                            print('\t%s %30s %6d %-5s %s ; proxied=%s proxiable=%s' % (
                                echo_record['id'],
                                echo_record['name'],
                                echo_record['ttl'],
                                echo_record['type'],
                                echo_record['content'],
                                echo_record['proxied'],
                                echo_record['proxiable']
                            ))

                            dns_record_id = echo_record['id']
                            if dns_record['type'] == 'A':
                                new_dns_record = {
                                    'type': echo_record['type'],
                                    'name': echo_record['name'],
                                    'content': echo_record['content'],
                                    'proxied': True
                                }
                            else:
                                new_dns_record = {
                                    'type': echo_record['type'],
                                    'name': echo_record['name'],
                                    'content': echo_record['content'],
                                    'priority': 10,
                                    'proxied': False
                                }

                            cf.zones.dns_records.put(zone_id, dns_record_id, data=new_dns_record)

                        dns_records_created = True  # Mark DNS as done, skip for remaining servers

            time.sleep(5)
            stdin, stdout, stderr = ssh.exec_command("sudo bash /root/jokaste.sh")
            ssh.close()
            print('')

        except Exception as e:
            if "Authentication failed." in str(e):
                print(e)
                break