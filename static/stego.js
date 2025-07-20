// Safe Dropzone + Form Handling for Encode/Decode

// ENCODE
document.addEventListener("DOMContentLoaded", function() {
  // --- Encode Dropzone Logic ---
  const encodeDrop = document.getElementById('encodeDrop');
  const encodeFile = document.getElementById('encodeFile');
  const chosenImageName = document.getElementById('chosenImageName');
  let encodeMaxChars = 0;

  function updateChosenFile() {
    if (encodeFile && encodeFile.files && encodeFile.files.length) {
      chosenImageName.textContent = encodeFile.files[0].name + " selected";
    } else {
      chosenImageName.textContent = "Click or drag image here (PNG/JPG)";
    }
  }

  if (encodeDrop && encodeFile && chosenImageName) {
    encodeDrop.addEventListener('click', () => encodeFile.click());
    encodeDrop.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        encodeFile.click();
      }
    });
    encodeDrop.addEventListener('dragover', (e) => {
      e.preventDefault();
      encodeDrop.classList.add('dragover');
    });
    encodeDrop.addEventListener('dragleave', (e) => {
      encodeDrop.classList.remove('dragover');
    });
    encodeDrop.addEventListener('drop', (e) => {
      e.preventDefault();
      encodeDrop.classList.remove('dragover');
      if (e.dataTransfer.files.length) {
        let file = e.dataTransfer.files[0];
        if (file.type === 'image/png' || file.type === 'image/jpeg') {
          encodeFile.files = e.dataTransfer.files;
          encodeFile.dispatchEvent(new Event('change'));
        } else {
          chosenImageName.textContent = "Only PNG/JPEG allowed!";
          encodeFile.value = "";
        }
      }
    });
    encodeFile.addEventListener('change', function () {
      updateChosenFile();
      updateEncodeCapacity();
    });
    updateChosenFile();
  }

  // Encode capacity meter
  function updateEncodeMessageCounter() {
    const msgInput = document.getElementById('encodeMessage');
    const msgCounter = document.getElementById('encodeMessageCounter');
    const count = msgInput.value.length;
    if (encodeMaxChars > 0) {
      msgCounter.textContent = `Text: ${count}/${encodeMaxChars} chars`;
    } else {
      msgCounter.textContent = '';
    }
  }
  window.updateEncodeCapacity = function() {
    const fileInputHide = document.getElementById('hideFile');
    const msgInput = document.getElementById('encodeMessage');
    const status = document.getElementById('encode-usage-status');
    let info = document.getElementById('capacity-info');
    if (!encodeFile || !encodeFile.files || !encodeFile.files[0]) { if(status) status.innerText=''; updateEncodeMessageCounter(); return; }
    let reader = new FileReader();
    reader.onload = function(e) {
      let img = new window.Image();
      img.onload = function() {
        let maxBits = img.width * img.height * 3;
        let usableChars = Math.floor(maxBits / 8);
        encodeMaxChars = usableChars;
        msgInput.maxLength = encodeMaxChars;
        updateEncodeMessageCounter();
        let sizeStr, unit="bytes", b=usableChars;
        if(b>1024*1024){sizeStr=(b/1048576).toFixed(2);unit="MB";}
        else if(b>1024){sizeStr=(b/1024).toFixed(1);unit="KB";}
        else{sizeStr=b;}
        if(info) info.innerHTML=`<b>Image capacity:</b> <strong>${sizeStr} ${unit}</strong> (${img.width}x${img.height} = ${maxBits} bits)`;
        let msgLen=msgInput.value.length, msgBits=msgLen*8, fileBits=0, fileKB=0, fileChars=0;
        if(fileInputHide && fileInputHide.files.length>0) {
          const f=fileInputHide.files[0];
          fileKB=Math.ceil(f.size/1024);
          fileBits=Math.ceil(f.size*8*4/3);
          fileChars=Math.ceil(f.size*4/3);
        }
        let secretBits = (msgLen>0&&fileInputHide.files.length>0)?msgBits+fileBits
          :(fileInputHide.files.length>0)?fileBits:msgBits;
        let secretKB = secretBits / 8 / 1024;
        let usedBits = secretBits;
        let displayMsg="";
        if(fileInputHide.files.length>0) displayMsg += `File: ${fileKB} KB (${fileChars} base64 chars)`;
        if(displayMsg) displayMsg+="<br>";
        displayMsg += `<b>${usedBits}</b> bits (${secretKB.toFixed(2)} KB) of <b>${maxBits}</b> bits (${Math.floor(maxBits/8/1024)} KB) used`;
        if(usedBits>maxBits) displayMsg+=`<br><span style="color:tomato;font-weight:bold;">❌ Too large! Secret data exceeds image capacity.</span>`;
        if(status) status.innerHTML = displayMsg;
        updateEncodeMessageCounter();
      }
      img.src=e.target.result;
    };
    reader.readAsDataURL(encodeFile.files[0]);
  }
  if(document.getElementById('encodeMessage')) {
    document.getElementById('encodeMessage').addEventListener('input', window.updateEncodeCapacity);
  }
  if(document.getElementById('hideFile')) {
    document.getElementById('hideFile').addEventListener('change', window.updateEncodeCapacity);
  }
  window.cancelEncodeOp = function() {
    document.getElementById('encodeForm').reset();
    document.getElementById('capacity-info').innerText = '';
    document.getElementById('encode-usage-status').innerText = '';
    if (chosenImageName) chosenImageName.textContent = 'Click or drag image here (PNG/JPG)';
    encodeMaxChars = 0;
    updateEncodeMessageCounter();
    document.getElementById('encodeMessage').maxLength = "";
  };
  window.validateEncode = function() {
    const fileInput = document.getElementById('encodeFile');
    const message = document.getElementById('encodeMessage').value.trim();
    const hideFile = document.getElementById('hideFile');
    if (!fileInput.files.length) {
      alert("Please select an image.");
      return false;
    }
    if (!message && (!hideFile.files || !hideFile.files.length)) {
      alert("Provide either a message or file to hide.");
      return false;
    }
    let status = document.getElementById('encode-usage-status');
    if (status && status.innerHTML.includes("❌")) {
      alert("Secret is too big for this image. Please shorten it or use a larger PNG.");
      return false;
    }
    return true;
  }
});

// --- Decode Dropzone Logic ---
document.addEventListener("DOMContentLoaded", function() {
  const decodeDrop = document.getElementById('decodeDrop');
  const decodeInput = document.getElementById('decodeFile');
  if (decodeDrop && decodeInput) {
    decodeDrop.addEventListener('click', function () { decodeInput.click(); });
    decodeDrop.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') { decodeInput.click(); }
    });
    decodeDrop.addEventListener('dragover', function (e) {
      e.preventDefault();
      decodeDrop.classList.add('dragover');
    });
    decodeDrop.addEventListener('dragleave', function (e) {
      decodeDrop.classList.remove('dragover');
    });
    decodeDrop.addEventListener('drop', function (e) {
      e.preventDefault();
      decodeDrop.classList.remove('dragover');
      if (e.dataTransfer.files.length) {
        decodeInput.files = e.dataTransfer.files;
        decodeInput.dispatchEvent(new Event('change'));
      }
    });
    decodeInput.addEventListener('change', function () {
      if (decodeInput.files && decodeInput.files[0]) {
        decodeDrop.innerHTML = "<b>" + decodeInput.files[0].name + "</b> selected";
      }
    });
  }
  window.validateDecode = function() {
    let file = decodeInput ? decodeInput.files[0] : null;
    if(file && !file.name.endsWith('.png')) {
      return confirm("JPEG is NOT safe for steganography. Only PNG is recommended. Proceed?");
    }
    return true;
  }
  window.cancelDecodeOp = function() {
    if(document.getElementById('decodeForm')) document.getElementById('decodeForm').reset();
    if(decodeDrop) decodeDrop.innerHTML = "Drag &amp; drop a PNG here or click to browse.";
  };
});

// Clipboard, details, and other global helpers
function toggleDetails(id) {
  var details = document.getElementById(id);
  if (details.style.display === "none" || details.style.display === "") {
    details.style.display = "";
  } else {
    details.style.display = "none";
  }
}
function copyDecoded() {
  navigator.clipboard.writeText(document.getElementById('decodedText').textContent)
    .then(()=>alert('Copied!'));
}
