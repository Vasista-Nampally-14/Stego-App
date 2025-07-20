# 🕵️ Steganography Web App

A modern, accessible Flask app to hide messages (or small files) inside PNG images using strong encryption and robust LSB steganography. You get previews, SHA-256 integrity, drag and drop, capacity meter, clipboard copy, dark/light themes, and more. Perfect for learning, private sharing, or privacy-first workflows.

---

## 🎯 What is Image Steganography?

Image steganography is the practice of invisibly embedding secrets inside digital images—so only someone who knows the method (and, in this app, the password!) can recover them.  
The most common method is **LSB (Least Significant Bit)**: hiding bits in the lowest digit of each color (red, green, blue). For users and viewers, images look identical.

---

## ⚡ Quick Features Overview

- **Drag & Drop:** Effortless file uploads for both cover image and file to hide.
- **Download Preview:** Instantly preview and download your stego image, with a SHA-256 hash fingerprint.
- **Image Capacity Meter:** See how much of your image storage you're using—get warnings if you go over.
- **Clipboard-Friendly:** Copy decoded secrets with a single click.
- **File Hiding:** Optionally embed a small file (PDF, ZIP, TXT...) instead of (or with) text.
- **Session Management:** Export/import your session history.
- **Dark & Light Mode:** Toggle for eye comfort.
- **Strict PNG Mode:** PNGs are safe and lossless—JPEGs not recommended!
- **Accessibility:** ARIA-labels, keyboard focus, and high contrast.
- **Integrity Hash:** SHA-256 on every encode for easy image verification.

---

## 🚀 How It Works

1. **LSB Steganography:**  
   Bits of your secret are written in the least significant bit of each pixel—this is the "invisible" digit that the eye can't see but a computer can store or change.
2. **Encryption:**  
   Your content (text or file) is encrypted with your password using Fernet cryptography—a super-safe digital lock.
3. **Base64 Encoding & Marker:**  
   Content is made "safe" for images by base64 encoding, and a special `||END||` marker signals where to stop extracting from the pixel data.
4. **Integrity Hash:**  
   After encoding, a SHA-256 checksum is shown so you can be sure your downloaded stego image matches what you made.
5. **Session Management:**  
   Action history and outcomes can be exported to/imported from JSON for audit or workflow continuity.

---

## 🛠️ Techniques Used

| Step                | Technique                     | Purpose                                              |
|---------------------|------------------------------|------------------------------------------------------|
| Embedding message   | LSB (Least Significant Bit)   | Reliable, undetectable pixel modifications           |
| Secret protection   | Fernet symmetric encryption   | Strong password-based message/file encryption        |
| End-marking/data    | Base64 encoding + `||END||`   | Robust, unbreakable message extraction boundaries    |
| Hidden file support | `[FILE]:filename:base64...`   | Painless embedding/recovery of files                 |
| Integrity           | SHA-256 hash                  | Lets you verify if your image is still authentic     |

---

## 🏆 App Details (Highlights)

- **Transparent Capacity Meter:**  
  Get live feedback as you type—never try to hide more than your image can store.
- **Instant Image Preview:**  
  Check your stego image visually and by hash before download.
- **Clipboard Button:**  
  Instantly put secrets into your clipboard (desktop/mobile).
- **PNG-Only Alert:**  
  You'll be warned (and usually blocked) if you try to use JPEGs, which can destroy stego data.
- **Seamless File Support:**  
  Hide not just text, but PDFs, ZIPs, text files, etc. up to 70 KB for secure retrieval.
- **Accessibility:**  
  Every input and action area is labeled and accessible for users with assistive tech.

---

## 🖥️ Screenshots

> For a preview, see in-app: drag an image, type a secret, and see the modern glassy interface, dark and light toggle, and capacity bars.

![alt text](DarkMode.png)
![alt text](LightMode.png)
---

## 💡 Best Practices

- **Always use PNGs!** JPEG != safe: JPEG compression destroys hidden data.
- Do not edit stego images after they're created.
- Download and decode directly—don't upload modified files.
- Bigger images let you hide bigger/more secrets.
- Save your secret password: without it, extraction is impossible (even for you!).

---

## 📦 Project Structure

stego_app/
├── app.py
├── requirements.txt
├── static/
│ ├── style.css
│ ├── progress.js
│ └── stego.js
└── templates/
└── index.html

---

## 🏗️ Installation

git clone <repo_url>
cd stego_app
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
---

## 🔨 Running the App

python app.py

Go to [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

---

## 📝 Usage Cheat-Sheet

### Encode

1. **Drag/drop** or select a PNG (never JPEG!).
2. Type your message *or* choose a file to hide.
3. Enter a password (required for decryption).
4. Use the capacity bar to check if your message will fit.
5. Click *Encode*—then preview and download your stego image and save the hash.

### Decode

1. **Drop or select the stego image** you exported earlier.
2. Enter your **original password**.
3. Result is shown directly (text: with copy, file: triggers download).

### Session

- **Export/Import session** for audit or cross-system workflows.
- **View/clear action history** without sharing secrets.

---

## 🧑‍🔬 Example: Hiding a File

1. Drag a PNG and a file (e.g., `secret.pdf`) onto the encode form.
2. Set password, submit, download stego image.
3. For decoding, drop image + password, and you'll get `secret.pdf` for direct download.

---

## 👨‍💻 Techniques & Implementation At a Glance

- **Python Flask backend** with templates for UI logic.
- **Pillow** for handling images pixel-by-pixel.
- **cryptography (Fernet)** for strong encryption.
- **SHA-256 hashing** for verifying stego image download.
- **Pure HTML/JS/CSS for UI**—no dependencies outside Flask and Python libraries.

---

## License

MIT License

---

## 🙋 Contact & Acknowledgments

- Designed for privacy and learning by [Your Name].
- Pull requests, suggestions, and collaborations are welcomed.

---
This Markdown can be directly copied into your README.md file and viewed on GitHub or similar platforms for visually organized documentation, user guidance, technical insight, and contributor clarity.

