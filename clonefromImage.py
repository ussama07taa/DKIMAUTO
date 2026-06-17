import time
from linode_api4 import LinodeClient
import json
# -------------------------------------------------------------------- #

# Mumbai, IN => 0, Toronto, ON => 1, Sydney, AU => 2, Dallas, TX => 3, Fremont, CA => 4, Atlanta, GA => 5
# Newark, NJ => 6, London, UK => 7, Singapore, SG => 8, Frankfurt, DE => 9(8), Tokyo 2, JP => 10

# -------------------------------------------------------------------- #

with open(r'MJ-API', 'r', encoding="UTF-8") as json_file:
    APIS = json.load(json_file)

client = LinodeClient(APIS["API1"])
# Get a list of all available images
images = client.images()
# Filter images to only show private ones
private_images = [image for image in images if image.created_by == APIS['Linode_user']]

# Sort private images by created date (most recent first)
private_images.sort(key=lambda image: image.created, reverse=True)

# Print the label and ID of the most recent private image
if private_images:
    print("Private images:")
    for i, image in enumerate(private_images, start=1):
        print(f"{i}. {image.label}: {image.id}")
else:
    print('No private images found.')



image_id = input("Ara id dial image a zabi: ")
# region_index = int(input("Region? 9 pour DE  7 pour UK : "))
region_index = int(input("Region? 0-MUMB,1-TORON,2-SYDN,3-DAL,4-FREM,5-ATLAN,7-UK,8-SG,9-DE : "))
num_instances = int(input("ch7al mne ip baghy?: "))

print("Create Instance in progress ... ")

for k in range(0, num_instances):
    available_regions = client.regions()
    chosen_region = available_regions[region_index]
    #new_linode = client.linode.instance_create('g6-highmem-16',
    new_linode = client.linode.instance_create('g6-nanode-1',chosen_region,root_pass=APIS["password"],image='private/' + image_id)
    if (k+1)%10 == 0:
        time.sleep(30)

linodes = client.linode.instances()
first_linode = linodes[0]
first_linode = linodes.first()
last_linode = linodes[-1]
for i, current_linode in enumerate(linodes):
    print("[", i + 1, "/", len(linodes), "]", "ID: ", current_linode.label, "ipv4: ", current_linode.ipv4)

print('+Done')