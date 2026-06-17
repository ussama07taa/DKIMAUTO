import os
import json
from flask import Flask, render_template, request, flash

try:
    from linode_api4 import LinodeClient
except Exception:
    LinodeClient = None

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET', 'devkey')


def load_apis():
    # try to load MJ-API from repo root
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    path = os.path.join(base, 'MJ-API')
    if not os.path.exists(path):
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


# Region mapping (index, display name)
REGIONS = [
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


@app.route('/')
def index():
    apis = load_apis()
    images = []
    if LinodeClient and apis.get('API1'):
        try:
            client = LinodeClient(apis['API1'])
            imgs = client.images()
            images = [img for img in imgs if img.created_by == apis.get('Linode_user')]
            images.sort(key=lambda i: i.created, reverse=True)
        except Exception as e:
            flash(f'Linode API error: {e}', 'warning')
    else:
        if not LinodeClient:
            flash('linode_api4 package not installed.', 'warning')
        else:
            flash('MJ-API not configured or missing API1 token.', 'info')

    return render_template('index.html', images=images, regions=REGIONS)


@app.route('/preview', methods=['POST'])
def preview():
    image_id = request.form.get('image_id')
    region_index = request.form.get('region_index')
    count = request.form.get('count') or '1'
    use_ssh_key = bool(request.form.get('use_ssh_key'))
    try:
        count_int = int(count)
    except Exception:
        count_int = 1

    region_name = dict(REGIONS).get(region_index, 'unknown')

    preview = {
        'image_id': image_id,
        'region_index': region_index,
        'region_name': region_name,
        'count': count_int,
        'use_ssh_key': use_ssh_key,
    }

    # Non-destructive: we do not call Linode instance_create here.
    return render_template('index.html', preview=preview, images=[], regions=REGIONS)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
