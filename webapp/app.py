import os
import json
import requests
from flask import Flask, render_template, request, flash

try:
    from linode_api4 import LinodeClient
except Exception:
    LinodeClient = None

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET', 'devkey')


def load_apis():
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    path = os.path.join(base, 'MJ-API')
    if not os.path.exists(path):
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


# LINODE Regions
LINODE_REGIONS = [
    ("0", "Mumbai, IN"),
    ("1", "Toronto, ON"),
    ("2", "Sydney, AU"),
    ("3", "Dallas, TX"),
    ("4", "Fremont, CA"),
    ("5", "Atlanta, GA"),
    ("6", "Newark, NJ"),
    ("7", "London, UK"),
    ("8", "Singapore, SG"),
    ("9", "Frankfurt, DE"),
    ("10", "Tokyo, JP"),
]

# SCALEWAY Zones
SCALEWAY_ZONES = [
    ("fr-par-1", "Paris 1, FR"),
    ("fr-par-2", "Paris 2, FR"),
    ("fr-par-3", "Paris 3, FR"),
    ("nl-ams-1", "Amsterdam 1, NL"),
    ("nl-ams-2", "Amsterdam 2, NL"),
    ("nl-ams-3", "Amsterdam 3, NL"),
    ("pl-waw-1", "Warsaw 1, PL"),
    ("pl-waw-2", "Warsaw 2, PL"),
    ("pl-waw-3", "Warsaw 3, PL"),
]

SCALEWAY_API = "https://api.scaleway.com/instance/v1/zones"


def get_linode_images(apis):
    """Fetch private images from Linode."""
    images = []
    if not LinodeClient:
        flash('linode_api4 package not installed.', 'warning')
        return images
    if not apis.get('API1'):
        flash('MJ-API missing API1 token.', 'info')
        return images
    try:
        client = LinodeClient(apis['API1'])
        imgs = client.images()
        images = [img for img in imgs if img.created_by == apis.get('Linode_user')]
        images.sort(key=lambda i: i.created, reverse=True)
    except Exception as e:
        flash(f'Linode API error: {e}', 'warning')
    return images


def get_scaleway_images(apis, zone):
    """Fetch private images from Scaleway."""
    images = []
    if not apis.get('scaleway_token'):
        flash('MJ-API missing scaleway_token.', 'info')
        return images
    headers = {
        "X-Auth-Token": apis['scaleway_token'],
        "Content-Type": "application/json"
    }
    url = f"{SCALEWAY_API}/{zone}/images"
    try:
        r = requests.get(url, headers=headers, timeout=30)
        r.raise_for_status()
        data = r.json()
        for img in data.get("images", []):
            if img.get("root_volume"):
                images.append({
                    'id': img['id'],
                    'name': img['name'],
                    'created': img.get('creation_date', 'unknown')
                })
    except Exception as e:
        flash(f'Scaleway API error: {e}', 'warning')
    return images


@app.route('/')
def index():
    apis = load_apis()
    provider = request.args.get('provider', 'linode')
    images = []
    regions = []

    if provider == 'linode':
        images = get_linode_images(apis)
        regions = LINODE_REGIONS
    elif provider == 'scaleway':
        zone = request.args.get('zone', 'fr-par-1')
        images = get_scaleway_images(apis, zone)
        regions = SCALEWAY_ZONES

    return render_template(
        'index.html',
        images=images,
        regions=regions,
        provider=provider,
        apis=apis
    )


@app.route('/preview', methods=['POST'])
def preview():
    provider = request.form.get('provider', 'linode')
    image_id = request.form.get('image_id')
    region_index = request.form.get('region_index')
    zone = request.form.get('zone')
    count = request.form.get('count') or '1'
    use_ssh_key = bool(request.form.get('use_ssh_key'))

    try:
        count_int = int(count)
        if count_int <= 0 or count_int > 500:
            count_int = 1
    except Exception:
        count_int = 1

    if provider == 'linode':
        region_name = dict(LINODE_REGIONS).get(region_index, 'unknown')
    else:
        region_name = dict(SCALEWAY_ZONES).get(zone, 'unknown')

    preview_data = {
        'provider': provider,
        'image_id': image_id,
        'region_index': region_index,
        'zone': zone,
        'region_name': region_name,
        'count': count_int,
        'use_ssh_key': use_ssh_key,
    }

    flash('Preview mode — no instances created.', 'info')
    return render_template(
        'index.html',
        preview=preview_data,
        images=[],
        regions=LINODE_REGIONS if provider == 'linode' else SCALEWAY_ZONES,
        provider=provider
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
