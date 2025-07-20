Steganography Web App
A modern Flask web app for securely hiding and revealing messages or files inside PNG images using password-based encryption and robust steganography.

Features
Drag & Drop Support: Easily upload images and secrets.

Image Preview & Download: Instantly preview and download your stego image, with SHA-256 integrity hash.

Image Capacity Meter: Live indicator shows how much message/file your image can hold.

Clipboard Copy: One-click copy for decoded messages.

File Hiding: Optionally conceal small files (≤70KB), auto-offering download after reveal.

Session Export/Import: Save and load session history as JSON.

Dark/Light Mode: Toggle for comfortable usage.

Accessibility: Keyboard focus, ARIA labels, and high-contrast support.

Clear User Guidance: In-app warnings and safe workflow tips.

How It Works
LSB Steganography: Hides secret bits in the least significant color bits of every image pixel so image looks unchanged.

Encryption: Your message (or file) is encrypted with your password using strong Fernet symmetric cryptography.

Base64 Encoding & Markers: The encrypted secret becomes base64 text for safe embedding, plus a special end marker (||END||) helps extraction.

Integrity Hash: SHA-256 hash allows you to verify your downloaded stego image hasn’t been modified.

Techniques and Algorithms
Operation |	Technique | Purpose
Hiding Data |	LSB (Least Significant Bit)	| Stealthy alteration of image pixel bits
Encryption |	Fernet symmetric encryption	| Password-protects message or file
Data Formatting |	Base64 encoding + end marker	| Robustifies storage and extraction of secrets
File Support |	[FILE]:filename:base64 tag	| Seamlessly stores and retrieves a concealed file
Integrity |	SHA-256 hash	| Lets you verify if a stego image is 

Best Practices
Always use PNG images for encode/decode. JPEG is not safe for secrets as it destroys embedded data.

Never edit or re-save a stego image in any external viewer or tool.

Always download and use the stego image exactly as exported by the app.

The longer your secret or bigger your file, the larger image you need.

If decode fails, re-check password, image, and file format.

Project Structure
text
stego_app/
├── app.py
├── requirements.txt
├── static/
│   ├── style.css
│   ├── progress.js
│   └── stego.js
└── templates/
    └── index.html
Setup & Usage
1. Install
bash
git clone <repo_url>
cd stego_app
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
2. Run
bash
python app.py
Open http://127.0.0.1:5000 in your browser.

Usage Guide
Encoding

Drag a PNG into the form, or click to browse.

Type your message — or hide a small file instead.

Enter a password for encryption.

Capacity bar will show if your secret fits.

Submit—then preview and download your stego image (+ hash).

Decoding

Drag or browse for your previously generated PNG stego image.

Enter the password used during encoding.

Revealed secrets can be copied to clipboard, or files will prompt download.

History & Export

Session history records all processed actions.

Use export/import buttons to save/load session actions as JSON.

License
MIT

This project is intended for educational, privacy, and personal security uses. Feedback and contributions are welcome.



