function allowDrop(ev) { ev.preventDefault(); }
function handleFileDrop(ev, zoneId, inputId) {
  ev.preventDefault();
  document.getElementById(zoneId).classList.remove('dropzone-over');
  const files = ev.dataTransfer.files;
  if (files.length) {
    document.getElementById(inputId).files = files;
    document.getElementById(inputId).dispatchEvent(new Event('change'));
  }
}
function handleDrag(zoneId) {
  document.getElementById(zoneId).classList.add('dropzone-over');
}
function handleDragLeave(zoneId) {
  document.getElementById(zoneId).classList.remove('dropzone-over');
}
function handleFileInput(input, zoneId) {
  if(input.files && input.files[0]) {
    document.getElementById(zoneId).innerHTML = "<b>" + input.files[0].name + "</b> selected";
  }
}
// Capacity meter logic:
function updateCapacity() {
  let message = document.querySelector('#encodeForm textarea').value;
  let fileInput = document.getElementById('encodeFile');
  if(!fileInput.files[0]) return;
  let img = fileInput.files[0];
  let reader = new FileReader();
  reader.onload = function(e){
    let image = new window.Image();
    image.onload = function() {
      let capacity = image.width * image.height * 3;
      let bitsNeeded = (message.length + 10) * 8; // approx with marker overhead
      let percent = Math.round((bitsNeeded/capacity)*100);
      let msg = `${bitsNeeded}/${capacity} bits used (${percent}%)`;
      let barColor = percent > 95 ? "tomato" : (percent > 80 ? "#e3a20f" : "#22865c");
      document.getElementById('capacity-status').innerHTML =
        `<span style="color:${barColor};font-weight:600;">${msg}</span>` +
        (bitsNeeded > capacity ? "<br><b style='color:tomato'>Too long for this image!</b>": "");
    }
    image.src = e.target.result;
  }
  reader.readAsDataURL(img);
}
function toggleDetails(id) {
  var details = document.getElementById(id);
  if (details.style.display === "none" || details.style.display === "") {
    details.style.display = "";
  } else {
    details.style.display = "none";
  }
}
function toggleTheme() {
  let dark = document.body.classList.toggle('dark-mode');
  localStorage.setItem('darkMode', dark ? "1" : "0");
  document.getElementById('themeIcon').textContent = dark ? "🌞" : "🌙";
}
window.onload = function() {
  // Drag-drop for encode
  let encodeZone = document.getElementById('encodeDrop');
  encodeZone.ondragover = function(ev){ allowDrop(ev); handleDrag('encodeDrop'); };
  encodeZone.ondragleave = function(ev){ handleDragLeave('encodeDrop'); };
  encodeZone.ondrop = function(ev){ handleFileDrop(ev, 'encodeDrop', 'encodeFile'); updateCapacity(); };
  // Drag-drop for decode
  let decodeZone = document.getElementById('decodeDrop');
  decodeZone.ondragover = function(ev){ allowDrop(ev); handleDrag('decodeDrop'); };
  decodeZone.ondragleave = function(ev){ handleDragLeave('decodeDrop'); };
  decodeZone.ondrop = function(ev){ handleFileDrop(ev, 'decodeDrop', 'decodeFile'); };
  // Theme
  if(localStorage.getItem('darkMode')==="1") {
    document.body.classList.add('dark-mode');
    document.getElementById('themeIcon').textContent = "🌞";
  }
};
function validateEncode() {
  let file = document.getElementById('encodeFile').files[0];
  if(file && !file.name.endsWith('.png')) {
    alert("⚠️ Only PNG is safe for steganography! Use PNG for best results.");
    return false;
  }
  return true;
}
function validateDecode() {
  let file = document.getElementById('decodeFile').files[0];
  if(file && !file.name.endsWith('.png')) {
    return confirm("JPEG is NOT safe for steganography. Only PNG is recommended. Proceed?");
  }
  return true;
}
function copyDecoded() {
  navigator.clipboard.writeText(document.getElementById('decodedText').textContent)
    .then(()=>alert('Copied!'));
}
function importSession(input) {
  if(!input.files[0]) return;
  let reader = new FileReader();
  reader.onload = function(e) {
    fetch('/import_session', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: e.target.result
    }).then(_=>window.location.reload());
  };
  reader.readAsText(input.files[0]);
}
