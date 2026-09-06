function toggleAcc(head) {
  const body = head.nextElementSibling;
  const open = body.classList.toggle('open');
  head.classList.toggle('open', open);
}

function showStep(i, total) {
  for (let j = 0; j < total; j++) {
    const s = document.getElementById('s'+j);
    const d = document.getElementById('d'+j);
    if (s) s.classList.remove('active');
    if (d) d.classList.remove('show');
  }
  document.getElementById('s'+i).classList.add('active');
  document.getElementById('d'+i).classList.add('show');
}

function checkSingle(btn, res) {
  const opts = btn.closest('.quiz-opts').querySelectorAll('.quiz-opt');
  opts.forEach(b => { b.disabled = true; b.classList.remove('correct','wrong'); });
  btn.classList.add(res);
}
