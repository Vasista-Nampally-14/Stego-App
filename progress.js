function startProgress(type) {
  let area = document.getElementById(type + '-progress');
  let barAnim = document.getElementById(type + 'ProgressBarAnim');
  let text = document.getElementById(type + 'ProgressText');
  let afterMsg = document.getElementById(type + 'AfterMsg');
  if (!area) return true;
  area.style.display = '';
  barAnim.style.width = '0%';
  text.innerText = '0%';
  afterMsg.innerText = '';
  let endpoint = '/' + type + '_progress';
  let interval = setInterval(() => {
    fetch(endpoint)
      .then(res => res.json())
      .then(data => {
        let pct = data.percent;
        barAnim.style.width = pct + '%';
        text.innerText = pct + '%';
        if (data.after_msg) {
          afterMsg.innerText = data.after_msg;
          setTimeout(() => { area.style.display = 'none'; }, 1600);
          clearInterval(interval);
        }
      });
  }, 250);
  return true;
}
