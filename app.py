from flask import Flask, request, jsonify, render_template, send_file
from model import predict_gep
from utils.report_generator import generate_pdf_report, generate_excel_report
import io
import os
import requests   # for Ollama API calls

app = Flask(__name__)
# Always re-read index.html from disk, even outside debug mode. Without this,
# once debug=False, Flask/Jinja caches the compiled template after the first
# request and keeps serving the OLD file's content until the process is
# fully restarted — even if you save a new index.html to templates/.
app.config['TEMPLATES_AUTO_RELOAD'] = True

# ================== Helper: GEP calculation ==================
def calculate_gep_from_inputs(data):
    method = data.get('method', 'provisioning')

    # Provisioning
    crop_val = float(data.get('p-crop-val', 0)) * float(data.get('p-crop-gamma', 0.5))
    livestock_val = float(data.get('p-livestock-val', 0)) * float(data.get('p-livestock-gamma', 0.4))
    water_val = float(data.get('p-water-qty', 0)) * float(data.get('p-water-price', 0))
    timber_val = float(data.get('p-timber-val', 0))
    fishery_val = float(data.get('p-fishery-val', 0))
    medicinal_val = float(data.get('p-medicinal-val', 0))
    epv = crop_val + livestock_val + water_val + timber_val + fishery_val + medicinal_val

    # Regulating
    carbon_val = float(data.get('r-carbon-qty', 0)) * float(data.get('r-carbon-price', 0))
    climate_val = float(data.get('r-climate-val', 0))
    air_val = float(data.get('r-airpurify-qty', 0)) * float(data.get('r-airpurify-price', 0))
    water_purify_val = float(data.get('r-waterpurify-qty', 0)) * float(data.get('r-waterpurify-price', 0))
    flood_val = float(data.get('r-flood-val', 0))
    soil_val = float(data.get('r-soil-qty', 0)) * float(data.get('r-soil-price', 0))
    pollination_val = float(data.get('r-pollination-val', 0))
    sandstorm_val = float(data.get('r-sandstorm-val', 0))
    erv = carbon_val + climate_val + air_val + water_purify_val + flood_val + soil_val + pollination_val + sandstorm_val

    # Cultural
    tourists = float(data.get('c-tourists', 0)) * float(data.get('c-tourist-spend', 0))
    recreation_val = float(data.get('c-recreation-val', 0))
    aesthetic_val = float(data.get('c-aesthetic-val', 0))
    spiritual_val = float(data.get('c-spiritual-val', 0))
    education_val = float(data.get('c-education-val', 0))
    mental_val = float(data.get('c-mentalhealth-val', 0))
    ecv = tourists + recreation_val + aesthetic_val + spiritual_val + education_val + mental_val

    # Fauna
    if method == 'fauna':
        wildlife_tourism = float(data.get('fa-wildlife-tourism', 0))
        animal_products = float(data.get('fa-animal-products', 0))
        genetic_resources = float(data.get('fa-genetic-resources', 0))
        pest_control = float(data.get('fa-pest-control', 0))
        seed_dispersal = float(data.get('fa-seed-dispersal', 0))
        fv = wildlife_tourism + animal_products + genetic_resources + pest_control + seed_dispersal
    else:
        fv = 0

    # Combined
    if method == 'combined':
        epv = (float(data.get('f-food-val', 0)) + float(data.get('f-water-val', 0)) +
               float(data.get('f-timber-val', 0)) + float(data.get('f-fishery-val', 0)))
        erv = (float(data.get('f-carbon-val', 0)) + float(data.get('f-airwater-val', 0)) +
               float(data.get('f-disaster-val', 0)) + float(data.get('f-pollination-val', 0)))
        ecv = float(data.get('f-tourism-val', 0)) + float(data.get('f-nonmaterial-val', 0))
        fv = (float(data.get('f-fauna-tourism', 0)) +
              float(data.get('f-fauna-products', 0)) +
              float(data.get('f-fauna-genetic', 0)) +
              float(data.get('f-fauna-pest', 0)) +
              float(data.get('f-fauna-seed', 0)))

    gep = epv + erv + ecv + fv

    components = []
    if method in ['provisioning', 'combined']:
        components.append({'label': 'Provisioning', 'value': epv, 'color': '#4caf7f', 'icon': '🌾'})
    if method in ['regulating', 'combined']:
        components.append({'label': 'Regulating', 'value': erv, 'color': '#4fc3f7', 'icon': '🌬️'})
    if method in ['cultural', 'combined']:
        components.append({'label': 'Cultural', 'value': ecv, 'color': '#fbbf24', 'icon': '🏞️'})
    if method in ['fauna', 'combined']:
        components.append({'label': 'Fauna', 'value': fv, 'color': '#f06292', 'icon': '🐾'})

    inputs = {k: v for k, v in data.items() if k.startswith(('p-', 'r-', 'c-', 'fa-', 'f-', 'ai-'))}

    return {
        'gep': gep,
        'epv': epv,
        'erv': erv,
        'ecv': ecv,
        'fv': fv,
        'components': components,
        'method': method,
        'carbonVal': carbon_val if method != 'combined' else float(data.get('f-carbon-val', 0)),
        'inputs': inputs,
        'area': float(data.get('f-ecosystem-area', 0)),
        'population': float(data.get('f-population', 0))
    }

# ================== Routes ==================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/calculate', methods=['POST'])
def calculate():
    data = request.json
    result = calculate_gep_from_inputs(data)
    result['currency'] = data.get('currency', 'INR')
    result['region'] = data.get('regionName', 'Unknown')
    return jsonify(result)

@app.route('/api/predict', methods=['POST'])
def predict():
    data = request.json
    area = float(data.get('area_km2', 0))
    population = float(data.get('population', 0))
    forest_pct = float(data.get('forest_pct', 0))
    wetland_pct = float(data.get('wetland_pct', 0))
    agri_pct = float(data.get('agri_pct', 0))

    if area <= 0 or population <= 0:
        return jsonify({'error': 'Area and population must be positive.'}), 400

    pred = predict_gep(area, population, forest_pct, wetland_pct, agri_pct)
    return jsonify(pred)

@app.route('/api/report', methods=['POST'])
def generate_report():
    data = request.json
    try:
        pdf_bytes = generate_pdf_report(data)
        return send_file(
            io.BytesIO(pdf_bytes),
            download_name='GEP_Report.pdf',
            as_attachment=True,
            mimetype='application/pdf'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export-excel', methods=['POST'])
def export_excel():
    data = request.json
    try:
        excel_bytes = generate_excel_report(data)
        return send_file(
            io.BytesIO(excel_bytes),
            download_name='GEP_Data.xlsx',
            as_attachment=True,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ================== Wildlife Census: real species directory (GBIF) ==================
# GBIF's backbone taxonomy holds the real, currently-accepted species for the
# whole animal kingdom (~1.05-1.2 million species) — this replaces a small
# hand-written list with the real thing, paged from the server so the browser
# never has to hold more than one page of results in memory at a time.
GBIF_SPECIES_SEARCH_URL = 'https://api.gbif.org/v1/species/search'
GBIF_SPECIES_MATCH_URL = 'https://api.gbif.org/v1/species/match'
ANIMALIA_KINGDOM_KEY = 1

# Maps the census UI's filter buttons to a real taxonomic class name we can
# resolve to a GBIF key at runtime (never hardcode a guessed numeric key).
CENSUS_CLASS_TAXON_NAME = {
    'Mammals': 'Mammalia',
    'Birds': 'Aves',
    'Reptiles': 'Reptilia',
    'Amphibians': 'Amphibia',
    'Fish': 'Actinopterygii',   # ray-finned fish — the large majority of "fish"
    'Insects': 'Insecta',
}
_class_key_cache = {}

def _resolve_class_key(class_label):
    taxon_name = CENSUS_CLASS_TAXON_NAME.get(class_label)
    if not taxon_name:
        return None
    if taxon_name in _class_key_cache:
        return _class_key_cache[taxon_name]
    try:
        r = requests.get(GBIF_SPECIES_MATCH_URL, params={'name': taxon_name, 'rank': 'CLASS'}, timeout=10)
        r.raise_for_status()
        key = r.json().get('usageKey')
        _class_key_cache[taxon_name] = key
        return key
    except Exception:
        return None

@app.route('/api/species')
def get_species():
    q = (request.args.get('q') or '').strip()
    class_filter = request.args.get('class', 'all')

    try:
        offset = max(0, int(request.args.get('offset', 0)))
    except (TypeError, ValueError):
        offset = 0
    try:
        limit = min(100, max(1, int(request.args.get('limit', 50))))
    except (TypeError, ValueError):
        limit = 50

    params = {
        'rank': 'SPECIES',
        'status': 'ACCEPTED',
        'kingdomKey': ANIMALIA_KINGDOM_KEY,
        'offset': offset,
        'limit': limit,
    }
    if q:
        params['q'] = q
    if class_filter and class_filter != 'all':
        class_key = _resolve_class_key(class_filter)
        if class_key:
            # Send both param spellings — GBIF's REST API has used
            # highertaxon_key in older examples and highertaxonKey in
            # current docs; unknown params are simply ignored.
            params['highertaxonKey'] = class_key
            params['highertaxon_key'] = class_key

    try:
        resp = requests.get(GBIF_SPECIES_SEARCH_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return jsonify({'error': f'Could not reach GBIF: {e}'}), 502

    results = []
    for item in data.get('results', []):
        results.append({
            'key': item.get('key'),
            'name': item.get('canonicalName') or item.get('scientificName'),
            'kingdom': item.get('kingdom'),
            'phylum': item.get('phylum'),
            'class': item.get('class'),
            'order': item.get('order'),
            'family': item.get('family'),
        })

    return jsonify({
        'count': data.get('count', 0),
        'offset': data.get('offset', offset),
        'limit': data.get('limit', limit),
        'endOfRecords': data.get('endOfRecords', True),
        'results': results,
    })

# ================== AI Chatbot with Ollama ==================
@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '').strip()
    if not user_message:
        return jsonify({'error': 'Message is empty'}), 400

    try:
        ollama_url = os.environ.get('OLLAMA_URL', 'http://localhost:11434/api/chat')
        response = requests.post(
            ollama_url,
            json={
                "model": "llama3.2:3b",   # Change to your preferred model
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a helpful assistant specialized in Gross Ecosystem Product (GEP), "
                            "ecosystem services (provisioning, regulating, cultural, fauna), environmental economics, "
                            "and the GEP Calculator tool. Keep answers concise, accurate, and friendly."
                        )
                    },
                    {"role": "user", "content": user_message}
                ],
                "stream": False,
                "temperature": 0.7,
                "max_tokens": 500
            },
            timeout=30
        )

        if response.status_code != 200:
            return jsonify({'error': f'Ollama error: {response.text}'}), 500

        reply = response.json()["message"]["content"]
        return jsonify({'reply': reply})

    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Ollama is not running. Please start it from the system tray or run "ollama serve".'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ================== Run ==================
if __name__ == '__main__':
    # Configurable via environment variables so the same code runs unchanged
    # locally, on a LAN, in a container, or behind a cloud deploy.
    # HOST defaults to 0.0.0.0 so the server is reachable from outside the
    # machine it runs on (127.0.0.1 only accepts connections from itself).
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(debug=debug, host=host, port=port)