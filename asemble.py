import subprocess

while True:
    print("-----------------------------------------------")
    print("     Postfix from A to Z.")
    print("     Multi-Cloud: Linode + Scaleway")
    print("-----------------------------------------------")

    print("1. Clone Linode instances (from image)")
    print("2. Clone Scaleway instances (from image)")
    print("3. Configure DNS + Postfix (create_records)")
    print("4. Delete Cloudflare records")
    print("5. Generate SMTP config for mailer")
    print("99. Exit")

    choice = input("Khtar: ")

    if choice == "1":
        subprocess.run(["python3", "clonefromImage.py"])
    elif choice == "2":
        subprocess.run(["python3", "clonefromImage_scaleway.py"])
    elif choice == "3":
        subprocess.run(["python3", "create_records_cf.py"])
    elif choice == "4":
        subprocess.run(["python3", "delete_all_records_cf.py"])
    elif choice == "5":
        subprocess.run(["python3", "generate_smtp_config.py"])
    elif choice == "99":
        break