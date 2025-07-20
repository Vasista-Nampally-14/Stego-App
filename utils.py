# utils.py
import hashlib, base64

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
END_MARKER = "||END||"

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_fernet_key(password: str):
    key = hashlib.sha256(password.encode()).digest()
    return base64.urlsafe_b64encode(key)

def bits_to_kbs(bits):
    return bits / 8 / 1024
