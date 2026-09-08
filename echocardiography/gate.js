(function () {
  var KEY = 'echoGateOK';
  var PASSWORD = 'esavs2026';

  if (sessionStorage.getItem(KEY) === '1') {
    document.documentElement.style.visibility = 'visible';
    return;
  }

  var overlay = document.createElement('div');
  overlay.style.cssText = 'position:fixed;inset:0;visibility:visible;z-index:99999;' +
    'background:#fdfaf2;display:flex;align-items:center;justify-content:center;flex-direction:column;' +
    'font-family:-apple-system,"Noto Sans TC","Segoe UI",sans-serif;padding:20px;text-align:center;';
  overlay.innerHTML =
    '<div style="font-size:40px;margin-bottom:14px;">🔒</div>' +
    '<div style="font-size:16px;font-weight:700;color:#8a6010;margin-bottom:4px;">內部參考資料</div>' +
    '<div style="font-size:13px;color:#4a3800;opacity:.65;margin-bottom:18px;max-width:280px;">本頁含講義原始截圖，僅供內部學習使用，請輸入密碼繼續</div>' +
    '<input id="gate-pw" type="password" placeholder="密碼" ' +
      'style="border:2px solid #e8d5a0;border-radius:10px;padding:10px 14px;font-size:14px;width:220px;text-align:center;outline:none;">' +
    '<button id="gate-btn" style="margin-top:12px;background:linear-gradient(135deg,#8a6010,#c8962a);color:#fff;border:none;' +
      'border-radius:20px;padding:9px 28px;font-size:14px;font-weight:700;cursor:pointer;">進入</button>' +
    '<div id="gate-err" style="color:#dc2626;font-size:12px;margin-top:12px;display:none;">密碼錯誤，請再試一次</div>';

  document.body.appendChild(overlay);

  var pwInput = document.getElementById('gate-pw');
  var btn = document.getElementById('gate-btn');
  var err = document.getElementById('gate-err');

  function check() {
    if (pwInput.value === PASSWORD) {
      sessionStorage.setItem(KEY, '1');
      document.documentElement.style.visibility = 'visible';
      overlay.remove();
    } else {
      err.style.display = 'block';
      pwInput.value = '';
      pwInput.focus();
    }
  }

  btn.addEventListener('click', check);
  pwInput.addEventListener('keydown', function (e) { if (e.key === 'Enter') check(); });
  pwInput.focus();
})();
