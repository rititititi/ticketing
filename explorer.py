"""Read-only supplier inventory explorer. Prices here are supplier quotes."""
import json
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
