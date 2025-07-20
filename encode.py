from flask import Blueprint, request, redirect, url_for, session, send_file, abort, render_template
from PIL import Image
from cryptography.fernet import Fernet
import hashlib, base64, tempfile, os, time
from utils import allowed_file, get_fernet_key, bits_to_kbs, END_MARKER

encode_bp = Blueprint('encode', __name__)
TEMP_PREVIEW_DIR = tempfile.gettempdir()

def encode_image(image, secret_str, update_progress):
    img = image.convert("RGB")
    encoded = img.copy()
    width, height = img.size
    index = bits_written = 0
    binary_message = ''.join([format(ord(char), '08b') for char in secret_str])
    total = len(binary_message)
    progress = 0
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

def safe_tempfile(suffix="", prefix="stego_", dir=None):
    fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=dir)
    return path, os.fdopen(fd, 'wb')

# --- Dedicated encode screen for GET /encode/ ---
@encode_bp.route('/', methods=['GET'])
def show_encode():
    history = session.get('history', [])
    enc_status, enc_msg = session.pop('flash_encode', (None, None))
    enc_points = session.pop('enc_points', None)
    step_state = session.pop('step_state', None)
    preview_id = session.get('preview_id')
    preview_hash = session.get('preview_hash')
    preview_fn = session.get('last_encoded_fn')
    return render_template(
        'encode.html',
        history=history,
        enc_status=enc_status, enc_msg=enc_msg, enc_points=enc_points,
        step_state=step_state,
        preview_id=preview_id, preview_hash=preview_hash, preview_fn=preview_fn,
        bits_to_kbs=bits_to_kbs
    )

# POST handler for hiding a message in an image
@encode_bp.route('/encode', methods=['POST'])
def encode():
    session['encode_progress'] = 0
    image_file = request.files.get('image')
    hide_file = request.files.get('hide_file')
    password = request.form.get('password', '')
    message = request.form.get('message', '')

    # Clear any previous preview on each new encode
    session.pop('preview_id', None)
    session.pop('last_encoded_fn', None)
    session.pop('preview_hash', None)

    if hide_file and hide_file.filename:
        raw = hide_file.read()
        if len(raw) > 70_000:
            session['flash_encode'] = ('error', 'File to hide is too large! Try a file <70kB.')
            session['step_state'] = {'encode': True}
            return redirect(url_for('.show_encode'))
        file_b64 = base64.b64encode(raw).decode()
        message = "[FILE]:" + hide_file.filename + ":" + file_b64

    if not image_file or image_file.filename == '':
        session['flash_encode'] = ('error', 'Please select an image to hide your message.')
        session['step_state'] = {'encode': True}
        return redirect(url_for('.show_encode'))
    if not allowed_file(image_file.filename):
        session['flash_encode'] = ('error', 'Only PNG or JPG images are supported.')
        session['step_state'] = {'encode': True}
        return redirect(url_for('.show_encode'))
    if not password:
        session['flash_encode'] = ('error', 'A password is required for message encryption.')
        session['step_state'] = {'encode': True}
        return redirect(url_for('.show_encode'))
    if not message:
        session['flash_encode'] = ('error', 'Please enter a secret message to hide in the image.')
        session['step_state'] = {'encode': True}
        return redirect(url_for('.show_encode'))

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
        'image_kb': bits_to_kbs(image_bits),
        'msg_len': len(message),
        'msg_bits': message_bits,
        'msg_kb': bits_to_kbs(message_bits),
        'marker': END_MARKER
    }

    if message_bits > image_bits:
        points['status'] = (
            f"❌ Message too long! Image can store {image_bits} bits "
            f"({bits_to_kbs(image_bits):.2f} KB), your secret (with marker) needs {message_bits} bits "
            f"({bits_to_kbs(message_bits):.2f} KB)."
        )
        session['enc_points'] = points
        session['flash_encode'] = ('error', points['status'])
        session['step_state'] = {'encode': True}
        return redirect(url_for('.show_encode'))
    try:
        def set_progress(pct): session['encode_progress'] = pct
        t0 = time.time()
        encoded_image, bits_written = encode_image(image, secret_str, set_progress)
        duration = time.time() - t0
        ext = image_file.filename.rsplit('.', 1)[1].lower()
        ext = 'PNG' if ext == 'png' else 'JPEG'
        # Save to temp file for preview/download
        preview_path, tf = safe_tempfile(suffix=f".{ext.lower()}", dir=TEMP_PREVIEW_DIR)
        encoded_image.save(tf, ext)
        tf.close()
        with open(preview_path, "rb") as f:
            stego_bytes = f.read()
        hash = hashlib.sha256(stego_bytes).hexdigest()
        preview_id = os.path.basename(preview_path)
        session['preview_id'] = preview_id
        session['last_encoded_fn'] = f"stego_image.{ext.lower()}"
        session['preview_hash'] = hash

        points.update({
            'bits_written': bits_written,
            'written_kb': bits_to_kbs(bits_written),
            'status': f"✅ Encoded. Message bits written: {bits_written} ({bits_to_kbs(bits_written):.2f} KB), time: {duration:.2f}s"
        })
        session['enc_points'] = points
        history = session.get('history', [])
        history.append({'action': 'Encoded', 'msg': '[hidden]', 'image': True})
        session['history'] = history
        session['encode_progress_after'] = '✅ Encoding Complete! Download/preview shown below.'
        session['flash_encode'] = ('success', points['status'])
        session['step_state'] = {'encode': True}
        return redirect(url_for('.show_encode'))
    except Exception as e:
        points['status'] = f"❌ ERROR: {e}"
        session['enc_points'] = points
        session['flash_encode'] = ('error', points['status'])
        session['encode_progress_after'] = points['status']
        session['step_state'] = {'encode': True}
        return redirect(url_for('.show_encode'))

@encode_bp.route('/preview/<filename>')
def preview_file(filename):
    abs_path = os.path.join(TEMP_PREVIEW_DIR, filename)
    if not os.path.exists(abs_path):
        abort(404)
    return send_file(abs_path)

# FEATURE: Special endpoint to clear preview from session (for hide/cancel/download buttons)
@encode_bp.route('/clear_preview', methods=['POST', 'GET'])
def clear_preview():
    session.pop('preview_id', None)
    session.pop('last_encoded_fn', None)
    session.pop('preview_hash', None)
    # Optional: Clear any step_state if it controls preview
    step_state = session.get('step_state', {})
    if step_state and step_state.get('encode'):
        step_state.pop('encode', None)
        session['step_state'] = step_state
    # GET: redirect to base encode; POST (AJAX): 204 for async hide
    if request.method == 'GET':
        return redirect(url_for('.show_encode'))
    return '', 204
