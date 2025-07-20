from flask import (
    Flask, render_template, request, send_file, 
    redirect, url_for, session, jsonify
)
from PIL import Image
from cryptography.fernet import Fernet
import base64, hashlib, io, time, json, os

app = Flask(__name__)
app.secret_key = "replace_with_a_secure_random_value"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
END_MARKER = "||END||"

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_fernet_key(password: str):
    key = hashlib.sha256(password.encode()).digest()
    return base64.urlsafe_b64encode(key)

def encode_image(image, secret_str, update_progress):
    img = image.convert("RGB")
    encoded = img.copy()
    width, height = img.size
    index = 0
    binary_message = ''.join([format(ord(char), '08b') for char in secret_str])
    total = len(binary_message)
    progress = 0
    bits_written = 0
    for row in range(height):
        for col in range(width):
            if index < total:
                r, g, b = img.getpixel((col, row))
                r = r & ~1 | int(binary_message[index])
                index += 1; bits_written += 1
                if index < total:
                    g = g & ~1 | int(binary_message[index])
                    index += 1; bits_written += 1
                if index < total:
                    b = b & ~1 | int(binary_message[index])
                    index += 1; bits_written += 1
                encoded.putpixel((col, row), (r, g, b))
                if index // 1000 != progress // 1000 or index == total:
                    progress = index
                    percent = int((progress / total) * 100)
                    update_progress(percent)
            else:
                update_progress(100)
                return encoded, bits_written
    update_progress(100)
    return encoded, bits_written

def decode_image(image, update_progress):
    binary_data = ''
    img = image.convert("RGB")
    width, height = img.size
    total = width * height * 3
    read_bits = 0
    for row in range(height):
        for col in range(width):
            r, g, b = img.getpixel((col, row))
            for bit in (r, g, b):
                binary_data += str(bit & 1)
                read_bits += 1
                if read_bits % 2000 == 0 or read_bits == total:
                    percent = int((read_bits / total) * 100)
                    update_progress(percent)
    chars = []
    for i in range(0, len(binary_data), 8):
        byte = binary_data[i:i+8]
        if len(byte) < 8:
            break
        chars.append(chr(int(byte, 2)))
    data = ''.join(chars)
    marker_idx = data.find(END_MARKER)
    if marker_idx == -1:
        update_progress(100)
        return '', False, None, read_bits
    else:
        update_progress(100)
        return data[:marker_idx], True, marker_idx, read_bits

def pop_section_flash(section):
    val = session.pop(f'flash_{section}', None)
    if not val:
        return None, None
    status, message = val
    return status, message

def set_section_flash(section, status, message):
    session[f'flash_{section}'] = (status, message)

@app.route('/', methods=['GET'])
def index():
    session['encode_progress'], session['decode_progress'] = 0, 0
    history = session.get('history', [])
    step_state = session.pop('step_state', None)
    enc_status, enc_msg = pop_section_flash('encode')
    dec_status, dec_msg = pop_section_flash('decode')
    enc_points = session.pop('enc_points', None)
    dec_points = session.pop('dec_points', None)
    preview_img = session.pop('preview_img', None)
    preview_hash = session.pop('preview_hash', None)
    preview_fn = session.pop('last_encoded_fn', None)
    return render_template(
        'index.html',
        decoded_message=None,
        history=history,
        enc_status=enc_status, enc_msg=enc_msg, enc_points=enc_points,
        dec_status=dec_status, dec_msg=dec_msg, dec_points=dec_points,
        step_state=step_state,
        preview_img=preview_img, preview_hash=preview_hash, preview_fn=preview_fn
    )

@app.route('/encode', methods=['POST'])
def encode():
    session['encode_progress'] = 0
    image_file = request.files.get('image')
    hide_file = request.files.get('hide_file')
    password = request.form.get('password', '')
    message = request.form.get('message', '')

    # If a file to hide is provided, use that as the "message"
    if hide_file and hide_file.filename:
        raw = hide_file.read()
        if len(raw) > 70_000:  # Limit ~70Kb
            set_section_flash('encode', 'error', 'File to hide is too large! Try a file <70kB.')
            session['step_state'] = {'encode': True}
            return redirect(url_for('index'))
        file_b64 = base64.b64encode(raw).decode()
        message = "[FILE]:" + hide_file.filename + ":" + file_b64

    if not image_file or image_file.filename == '':
        set_section_flash('encode', 'error', 'Please select an image to hide your message.')
        session['step_state'] = {'encode': True}
        return redirect(url_for('index'))
    if not allowed_file(image_file.filename):
        set_section_flash('encode', 'error', 'Only PNG or JPG images are supported.')
        session['step_state'] = {'encode': True}
        return redirect(url_for('index'))
    if not password:
        set_section_flash('encode', 'error', 'A password is required for message encryption.')
        session['step_state'] = {'encode': True}
        return redirect(url_for('index'))
    if not message:
        set_section_flash('encode', 'error', 'Please enter a secret message to hide in the image.')
        session['step_state'] = {'encode': True}
        return redirect(url_for('index'))

    image = Image.open(image_file.stream)
    width, height = image.size
    image_bits = width * height * 3

    fernet = Fernet(get_fernet_key(password))
    encrypted_bytes = fernet.encrypt(message.encode())
    secret_str = base64.urlsafe_b64encode(encrypted_bytes).decode() + END_MARKER
    message_bits = len(secret_str) * 8

    points = {
        'dimension': f"{width}x{height}",
        'image_bits': image_bits,
        'msg_len': len(message),
        'msg_bits': message_bits,
        'marker': END_MARKER
    }

    if message_bits > image_bits:
        points['status'] = f"❌ Message too long! Image can store {image_bits} bits, your secret (with marker) needs {message_bits} bits."
        session['enc_points'] = points
        set_section_flash('encode', 'error', points['status'])
        session['step_state'] = {'encode': True}
        return redirect(url_for('index'))
    try:
        def set_progress(pct): session['encode_progress'] = pct
        t0 = time.time()
        encoded_image, bits_written = encode_image(image, secret_str, set_progress)
        duration = time.time() - t0
        buf = io.BytesIO()
        ext = image_file.filename.rsplit('.', 1)[1].lower()
        ext = 'PNG' if ext == 'png' else 'JPEG'
        encoded_image.save(buf, ext)
        buf.seek(0)
        stego_bytes = buf.getvalue()
        hash = hashlib.sha256(stego_bytes).hexdigest()
        img_data = base64.b64encode(stego_bytes).decode('utf-8')
        img_mime = 'image/png' if ext == "PNG" else 'image/jpeg'
        session['preview_img'] = f"data:{img_mime};base64,{img_data}"
        session['last_encoded_fn'] = f"stego_image.{ext.lower()}"
        session['preview_hash'] = hash

        points.update({
            'bits_written': bits_written,
            'status': f"✅ Encoded. Message bits written: {bits_written}, time: {duration:.2f}s"
        })
        session['enc_points'] = points
        history = session.get('history', [])
        history.append({'action': 'Encoded', 'msg': '[hidden]', 'image': True})
        session['history'] = history
        session['encode_progress_after'] = '✅ Encoding Complete! Download/preview shown below.'
        set_section_flash('encode', 'success', points['status'])
        session['step_state'] = {'encode': True}

        # After preview, do not serve send_file directly; just redirect to "/" to show preview.
        return redirect(url_for('index'))
    except Exception as e:
        points['status'] = f"❌ ERROR: {e}"
        session['enc_points'] = points
        set_section_flash('encode', 'error', points['status'])
        session['encode_progress_after'] = points['status']
        session['step_state'] = {'encode': True}
        return redirect(url_for('index'))

@app.route('/decode', methods=['POST'])
def decode():
    session['decode_progress'] = 0
    stego_file = request.files.get('stego_image')
    password = request.form.get('password', '')
    if not stego_file or stego_file.filename == '':
        set_section_flash('decode', 'error', 'Please select the image you want to decode.')
        session['step_state'] = {'decode': True}
        return redirect(url_for('index'))
    if not allowed_file(stego_file.filename):
        set_section_flash('decode', 'error', 'Only PNG or JPG images are supported.')
        session['step_state'] = {'decode': True}
        return redirect(url_for('index'))
    if not password:
        set_section_flash('decode', 'error', 'Please enter the password to decrypt your hidden message.')
        session['step_state'] = {'decode': True}
        return redirect(url_for('index'))
    stego_bytes = stego_file.read()
    # Optionally verify integrity hash if available (for demo, show below when present)
    image = Image.open(io.BytesIO(stego_bytes))
    width, height = image.size
    image_bits = width * height * 3
    points = {
        'dimension': f"{width}x{height}",
        'image_bits': image_bits,
        'marker': END_MARKER
    }
    try:
        def set_progress(pct): session['decode_progress'] = pct
        t0 = time.time()
        data, marker_found, marker_at, bits_scanned = decode_image(image, set_progress)
        points.update({
            'marker_found': marker_found,
            'marker_at': marker_at,
            'bits_scanned': bits_scanned
        })
        if not marker_found or not data:
            points['status'] = f"❌ No marker found — there is no hidden message in this image."
            session['dec_points'] = points
            set_section_flash('decode', 'error', points['status'])
            session['decode_progress_after'] = points['status']
            session['step_state'] = {'decode': True}
            return redirect(url_for('index'))

        try:
            encrypted_bytes = base64.urlsafe_b64decode(data.encode())
            fernet = Fernet(get_fernet_key(password))
            decoded_message = fernet.decrypt(encrypted_bytes).decode()
            duration = time.time() - t0
            points['dec_success'] = True
            points['status'] = f"✅ Decoded. Marker at char {marker_at}, {bits_scanned} bits scanned, time: {duration:.2f}s"
            session['dec_points'] = points
            history = session.get('history', [])
            # Handle file reveal
            if decoded_message.startswith("[FILE]:"):
                _, fname, f64 = decoded_message.split(":",2)
                file_bytes = base64.b64decode(f64)
                # For demo: serve the file for download
                return send_file(
                    io.BytesIO(file_bytes),
                    mimetype="application/octet-stream",
                    as_attachment=True,
                    download_name=fname
                )
            history.append({'action': 'Decoded', 'msg': decoded_message, 'image': False})
            session['history'] = history
            session['decode_progress_after'] = '✅ Message revealed!'
            set_section_flash('decode', 'success', points['status'])
            session['step_state'] = {'decode': True}
            enc_status, enc_msg = pop_section_flash('encode')
            enc_points = session.pop('enc_points', None)
            preview_img = session.pop('preview_img', None)
            preview_hash = session.pop('preview_hash', None)
            preview_fn = session.pop('last_encoded_fn', None)
            return render_template(
                'index.html',
                decoded_message=decoded_message,
                history=history,
                enc_status=enc_status, enc_msg=enc_msg, enc_points=enc_points,
                dec_status='success', dec_msg=points['status'], dec_points=points,
                step_state={'decode': True},
                preview_img=preview_img, preview_hash=preview_hash, preview_fn=preview_fn
            )
        except Exception:
            points['dec_success'] = False
            points['status'] = f"❌ Marker found, but password is incorrect or data is corrupted."
            session['dec_points'] = points
            set_section_flash('decode', 'error', points['status'])
            session['decode_progress_after'] = points['status']
            session['step_state'] = {'decode': True}
            return redirect(url_for('index'))
    except Exception as e:
        points['dec_success'] = False
        points['status'] = f"❌ ERROR: {e}"
        session['dec_points'] = points
        set_section_flash('decode', 'error', points['status'])
        session['decode_progress_after'] = points['status']
        session['step_state'] = {'decode': True}
        return redirect(url_for('index'))

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
    return '',204

@app.route('/clear_history')
def clear_history():
    session['history'] = []
    set_section_flash('encode', 'success', 'Session history cleared.')
    set_section_flash('decode', None, None)
    session.pop('enc_points', None)
    session.pop('dec_points', None)
    session.pop('step_state', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
