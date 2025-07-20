from flask import Blueprint, render_template, request, redirect, url_for, session, send_file, abort
from PIL import Image
import io
from cryptography.fernet import Fernet
import base64, tempfile, os, time, mimetypes, secrets
from utils import allowed_file, get_fernet_key, bits_to_kbs, END_MARKER

decode_bp = Blueprint('decode', __name__)
TEMP_PREVIEW_DIR = tempfile.gettempdir()

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

@decode_bp.route('/', methods=['GET'])
def show_decode():
    # Always clear decoded preview/message/session artifacts on page load (no persistence after refresh)
    decoded_message = session.pop('decoded_message', None)
    decoded_file_ref = session.pop('decoded_file_ref', None)
    decoded_file_data = None
    if decoded_file_ref:
        decoded_file_data = session.get(f'decoded_file_meta_{decoded_file_ref}', None)
        if decoded_file_data:
            decoded_file_data['download_url'] = url_for('.download_decoded_file', ref=decoded_file_ref)
            if decoded_file_data.get('is_image'):
                decoded_file_data['preview_url'] = url_for('.decoded_file_preview', ref=decoded_file_ref)
    history = session.get('history', [])
    dec_status, dec_msg = session.pop('flash_decode', (None, None))
    dec_points = session.pop('dec_points', None)
    step_state = session.pop('step_state', None)
    # Clean up decoded_file_ref session on GET to avoid persistent previews/messages after refresh
    session.pop('decoded_file_ref', None)
    return render_template(
        'decode.html',
        decoded_message=decoded_message,
        decoded_file=decoded_file_data,
        history=history,
        dec_status=dec_status, dec_msg=dec_msg, dec_points=dec_points,
        step_state=step_state,
        bits_to_kbs=bits_to_kbs
    )

@decode_bp.route('/decode', methods=['POST'])
def decode():
    session['decode_progress'] = 0
    stego_file = request.files.get('stego_image')
    password = request.form.get('password', '')
    # Clear prior output vars
    session.pop('decoded_message', None)
    session.pop('decoded_file_ref', None)
    # Defensive clean: remove any old decoded_file_meta_*
    for k in list(session.keys()):
        if k.startswith('decoded_file_meta_'):
            session.pop(k)

    if not stego_file or stego_file.filename == '':
        session['flash_decode'] = ('error', 'Please select the image you want to decode.')
        session['step_state'] = {'decode': True}
        return redirect(url_for('.show_decode'))
    if not allowed_file(stego_file.filename):
        session['flash_decode'] = ('error', 'Only PNG or JPG images are supported.')
        session['step_state'] = {'decode': True}
        return redirect(url_for('.show_decode'))
    if not password:
        session['flash_decode'] = ('error', 'Please enter the password to decrypt your hidden message.')
        session['step_state'] = {'decode': True}
        return redirect(url_for('.show_decode'))

    stego_bytes = stego_file.read()
    image = Image.open(io.BytesIO(stego_bytes))
    width, height = image.size
    image_bits = width * height * 3
    points = {
        'dimension': f"{width}x{height}",
        'image_bits': image_bits,
        'image_kb': bits_to_kbs(image_bits),
        'marker': END_MARKER
    }
    try:
        def set_progress(pct): session['decode_progress'] = pct
        t0 = time.time()
        data, marker_found, marker_at, bits_scanned = decode_image(image, set_progress)
        points.update({
            'marker_found': marker_found,
            'marker_at': marker_at,
            'bits_scanned': bits_scanned,
            'scanned_kb': bits_to_kbs(bits_scanned)
        })
        if not marker_found or not data:
            points['status'] = (
                f"❌ No marker found — there is no hidden message in this image. "
                f"Scanned {bits_scanned} bits ({bits_to_kbs(bits_scanned):.2f} KB)."
            )
            session['dec_points'] = points
            session['flash_decode'] = ('error', points['status'])
            session['decode_progress_after'] = points['status']
            session['step_state'] = {'decode': True}
            return redirect(url_for('.show_decode'))
        try:
            encrypted_bytes = base64.urlsafe_b64decode(data.encode())
            fernet = Fernet(get_fernet_key(password))
            decoded_message = fernet.decrypt(encrypted_bytes).decode()
            duration = time.time() - t0
            points['dec_success'] = True
            points['status'] = (
                f"✅ Decoded. Marker at char {marker_at}, "
                f"{bits_scanned} bits ({bits_to_kbs(bits_scanned):.2f} KB) scanned, time: {duration:.2f}s"
            )
            session['dec_points'] = points
            history = session.get('history', [])
            # If file hidden, handle preview (store a ref/meta in session)
            if decoded_message.startswith("[FILE]:"):
                _, fname, f64 = decoded_message.split(":", 2)
                file_bytes = base64.b64decode(f64)
                mime, _ = mimetypes.guess_type(fname)
                is_image = (mime or "").startswith('image')
                is_text = False
                text_snippet = None
                if not mime:
                    # Magic bytes for common image formats
                    if file_bytes[:8].startswith(b'\x89PNG'):
                        mime = 'image/png'
                        is_image = True
                    elif file_bytes[:2] == b'\xff\xd8':
                        mime = 'image/jpeg'
                        is_image = True
                if not is_image:
                    try:
                        decoded = file_bytes.decode('utf-8')
                        is_text = all(31 < ord(c) < 127 or c in '\r\n\t' for c in decoded[:512])
                        text_snippet = decoded[:512] if is_text else None
                    except Exception:
                        pass
                file_id = secrets.token_hex(16)
                suffix = os.path.splitext(fname)[1] or ""
                temp_path = os.path.join(TEMP_PREVIEW_DIR, f"decoded_{file_id}{suffix}")
                with open(temp_path, "wb") as f:
                    f.write(file_bytes)
                meta = {
                    'filename': fname,
                    'size': len(file_bytes),
                    'is_image': is_image,
                    'is_text': is_text,
                    'temp_path': temp_path,
                    'text_snippet': text_snippet,
                    'mime': mime,
                }
                session[f'decoded_file_meta_{file_id}'] = meta
                session['decoded_file_ref'] = file_id
                session['decoded_message'] = None
            else:
                session['decoded_message'] = decoded_message
                session['decoded_file_ref'] = None
            # Update history
            if decoded_message.startswith("[FILE]:"):
                history.append({'action': 'Decoded file', 'msg': '[file]', 'image': False})
            else:
                history.append({'action': 'Decoded message', 'msg': decoded_message, 'image': False})
            session['history'] = history
            session['decode_progress_after'] = '✅ Message revealed!'
            session['flash_decode'] = ('success', points['status'])
            session['step_state'] = {'decode': True}
            return redirect(url_for('.show_decode'))
        except Exception:
            points['dec_success'] = False
            points['status'] = (
                f"❌ Marker found, but password is incorrect or data is corrupted. "
                f"Scanned {bits_scanned} bits ({bits_to_kbs(bits_scanned):.2f} KB)."
            )
            session['dec_points'] = points
            session['flash_decode'] = ('error', points['status'])
            session['decode_progress_after'] = points['status']
            session['step_state'] = {'decode': True}
            return redirect(url_for('.show_decode'))
    except Exception as e:
        points['dec_success'] = False
        points['status'] = f"❌ ERROR: {e}"
        session['dec_points'] = points
        session['flash_decode'] = ('error', points['status'])
        session['decode_progress_after'] = points['status']
        session['step_state'] = {'decode': True}
        return redirect(url_for('.show_decode'))

@decode_bp.route('/decoded_file_preview')
def decoded_file_preview():
    ref = request.args.get('ref')
    meta = session.get(f'decoded_file_meta_{ref}')
    if not meta or not meta.get('is_image'):
        return abort(404)
    path = meta.get('temp_path')
    if not os.path.isfile(path):
        return abort(404)
    mimetype = meta.get('mime') or 'image/png'
    return send_file(path, mimetype=mimetype, as_attachment=False, download_name=meta['filename'])

@decode_bp.route('/download_decoded_file')
def download_decoded_file():
    ref = request.args.get('ref')
    meta = session.get(f'decoded_file_meta_{ref}')
    if not meta:
        return abort(404)
    path = meta.get('temp_path')
    if not os.path.isfile(path):
        return abort(404)
    mimetype = meta.get('mime') or "application/octet-stream"
    return send_file(path, mimetype=mimetype, as_attachment=True, download_name=meta['filename'])

# Optional: clear decoded preview/message via endpoint (call via AJAX in a Hide/Cancel button if you want)
@decode_bp.route('/clear_preview', methods=['POST', 'GET'])
def clear_decode_preview():
    session.pop('decoded_message', None)
    session.pop('decoded_file_ref', None)
    for k in list(session.keys()):
        if k.startswith('decoded_file_meta_'):
            session.pop(k)
    if request.method == 'GET':
        return redirect(url_for('.show_decode'))
    return '', 204
