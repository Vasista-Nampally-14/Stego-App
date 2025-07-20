from flask import Flask, render_template, session, redirect, url_for, jsonify, request
from encode import encode_bp
from decode import decode_bp
from utils import bits_to_kbs
from datetime import datetime
import os, json

app = Flask(__name__)
app.secret_key = 'your-secret-key'

# Register Blueprints with prefixes for dedicated screens
app.register_blueprint(encode_bp, url_prefix='/encode')    # encode.py must have show_encode route
app.register_blueprint(decode_bp, url_prefix='/decode')    # decode.py must have show_decode route

# --- Home screen (Landing, project intro & navigation) ---
@app.route('/')
def home():
    """Landing page (templates/home.html)."""
    return render_template('home.html')

# --- History Route ---
@app.route('/history')
def show_history():
    """Session history screen (templates/history.html)."""
    history = session.get('history', [])
    return render_template('history.html', history=history)

# --- Progress management ---
@app.route('/encode_progress')
def encode_progress():
    percent = session.get('encode_progress', 0)
    after_msg = session.pop('encode_progress_after', '') if percent == 100 else ''
    return jsonify({'percent': percent, 'after_msg': after_msg})


@app.route('/decode_progress')
def decode_progress():
    percent = session.get('decode_progress', 0)
    after_msg = session.pop('decode_progress_after', '') if percent == 100 else ''
    return jsonify({'percent': percent, 'after_msg': after_msg})

# --- Session Export/Import ---
@app.route('/export_session')
def export_session():
    hist = session.get('history', [])
    return (json.dumps({'history': hist}), 200, {'Content-Type': 'application/json'})


@app.route('/import_session', methods=['POST'])
def import_session():
    try:
        data = request.get_json()
        session['history'] = data['history']
    except Exception:
        pass
    return '', 204

# --- Clear History & Preview ---
@app.route('/clear_history')
def clear_history():
    session['history'] = []
    session['flash_encode'] = ('success', 'Session history cleared.')
    session['flash_decode'] = (None, None)
    session.pop('enc_points', None)
    session.pop('dec_points', None)
    session.pop('step_state', None)
    session.pop('preview_id', None)
    session.pop('preview_fn', None)
    session.pop('preview_hash', None)
    ref = session.pop('decoded_file_ref', None)
    if ref:
        meta = session.pop(f'decoded_file_meta_{ref}', None)
        if meta and meta.get('temp_path') and os.path.isfile(meta['temp_path']):
            try:
                os.remove(meta['temp_path'])
            except Exception:
                pass
    session.pop('decoded_message', None)
    return redirect(url_for('home'))

# --- Special endpoint to clear encode preview via AJAX or link/button ---
@app.route('/encode/clear_preview', methods=['POST', 'GET'])
def clear_encode_preview():
    session.pop('preview_id', None)
    session.pop('preview_fn', None)
    session.pop('preview_hash', None)
    # Remove any step_state if you use it to conditionally show preview
    step_state = session.get('step_state', {})
    if step_state and step_state.get('encode'):
        step_state.pop('encode', None)
        session['step_state'] = step_state
    # If user did GET, do a redirect; if POST (AJAX), 204 is fine
    if request.method == 'GET':
        return redirect(url_for('encode.show_encode'))
    return '', 204

# --- Global context (i.e., year in layout/footer) ---
@app.context_processor
def inject_year():
    return dict(config={'YEAR': datetime.now().year})

if __name__ == '__main__':
    app.run(debug=True)
