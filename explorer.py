"""Read-only supplier inventory explorer. Prices here are supplier quotes."""
import json
import os
from pathlib import Path
from flask import Blueprint, jsonify, render_template

explorer = Blueprint('explorer', __name__)
CATALOG = Path(__file__).parent / 'data/catalog.json'

@explorer.get('/explore')
def explore():
    return render_template('explorer.html')

@explorer.get('/api/catalog')
def catalog():
    return jsonify(json.loads(CATALOG.read_text()))

@explorer.get('/uploads/')
def upload_portal():
    from flask import Response
    from urllib.parse import urlparse
    value=os.environ.get('UU_SCOUT_ADMIN_URL','').strip()
    if value and (urlparse(value).scheme!='https' or not urlparse(value).netloc):value=''
    html=(Path(__file__).parent/'templates/upload-admin.html').read_text()
    return Response(html.replace('__ADMIN_URL__',json.dumps(value).replace('<','\\u003c')),mimetype='text/html')

@explorer.get("/api/updates")
def updates():
    from updates_feed import build_feed
    return jsonify(build_feed(json.loads(CATALOG.read_text())))
