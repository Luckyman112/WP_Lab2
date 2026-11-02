(function () {
  'use strict';

  const source = document.getElementById('source');
  const language = document.getElementById('language');
  const listing = document.getElementById('listing');
  const paper = document.getElementById('paper');
  const lineCount = document.getElementById('line-count');
  const readout = document.getElementById('lexer-readout');
  const paperLang = document.getElementById('paper-lang');
  const message = document.getElementById('message');
  const titleInput = document.getElementById('job-title');
  const tearButton = document.getElementById('tear');
  const copyButton = document.getElementById('copy');
  const csrf = document.querySelector('meta[name="csrf-token"]').content;

  // raw HTML of every printed line, as the server sent it; compared against
  // fresh results so only lines that actually changed get struck again
  let printed = JSON.parse(document.getElementById('initial-lines').textContent);
  let typingTimer = null;
  let requestNo = 0;

  const lamps = {};
  document.querySelectorAll('[data-lamp]').forEach((el) => {
    lamps[el.dataset.lamp] = el;
  });

  function lamp(name, on, blink) {
    lamps[name].classList.toggle('on', on);
    lamps[name].classList.toggle('blink', Boolean(on && blink));
  }

  function say(text) {
    message.textContent = text;
  }

  const pad = (n) => String(n).padStart(4, '0');

  function setCounter(value, roll) {
    if (!roll) {
      lineCount.textContent = pad(value);
      return;
    }
    // mechanical counters tick, they don't glide
    let shown = 0;
    const step = Math.max(1, Math.ceil(value / 20));
    const timer = setInterval(() => {
      shown = Math.min(value, shown + step);
      lineCount.textContent = pad(shown);
      if (shown === value) clearInterval(timer);
    }, 40);
  }

  function post(url, body) {
    return fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
      body: JSON.stringify(body),
    }).then((response) => {
      if (!response.ok) {
        return response.json()
          .catch(() => ({}))
          .then((data) => { throw new Error(data.error || `HTTP ${response.status}`); });
      }
      return response.json();
    });
  }

  function strike(li, delay) {
    li.classList.remove('printing');
    void li.offsetWidth; // restart the animation when a line is reprinted mid-stroke
    li.style.setProperty('--d', `${delay}ms`);
    li.classList.add('printing');
  }

  listing.addEventListener('animationend', (event) => {
    const li = event.target.closest('li');
    if (li) li.classList.remove('printing');
  });

  function reprint(lines) {
    let changed = 0;
    lines.forEach((html, i) => {
      if (html === printed[i]) return;
      let li = listing.children[i];
      if (!li) {
        li = document.createElement('li');
        li.appendChild(document.createElement('code'));
        listing.appendChild(li);
      }
      li.firstChild.innerHTML = html;
      strike(li, Math.min(changed, 40) * 18);
      changed += 1;
    });
    while (listing.children.length > lines.length) listing.lastElementChild.remove();
    printed = lines;
    setCounter(lines.length);
  }

  function showLexer(data) {
    readout.textContent = (data.detected ? 'auto → ' : '') + data.label;
    paperLang.textContent = data.label.toUpperCase();
  }

  function rehighlight() {
    const ticket = ++requestNo;
    lamp('busy', true);
    post(LP.highlightUrl, { code: source.value, language: language.value })
      .then((data) => {
        if (ticket !== requestNo) return; // a newer keystroke already went out
        reprint(data.lines);
        showLexer(data);
        lamp('online', true);
        say('');
      })
      .catch((err) => {
        if (ticket !== requestNo) return;
        lamp('online', false);
        say(`Printer fault: ${err.message}`);
      })
      .finally(() => {
        if (ticket === requestNo) lamp('busy', false);
      });
  }

  source.addEventListener('input', () => {
    clearTimeout(typingTimer);
    lamp('ready', true, true);
    typingTimer = setTimeout(() => {
      lamp('ready', true);
      rehighlight();
    }, 280);
  });

  language.addEventListener('change', rehighlight);

  source.addEventListener('keydown', (event) => {
    if (event.key === 'Tab' && !event.shiftKey && !event.ctrlKey && !event.altKey) {
      event.preventDefault();
      source.setRangeText('    ', source.selectionStart, source.selectionEnd, 'end');
      source.dispatchEvent(new Event('input'));
    } else if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
      event.preventDefault();
      tearOff();
    }
  });

  // ribbon and paper switches; the choice is remembered per browser
  function remember(key, value) {
    try {
      if (value === undefined) return localStorage.getItem(`lp1170.${key}`);
      localStorage.setItem(`lp1170.${key}`, value);
    } catch (e) {
      return null;
    }
    return null;
  }

  document.querySelectorAll('.switch').forEach((group) => {
    const kind = group.dataset.target;
    const saved = remember(kind);
    const savedInput = saved && group.querySelector(`input[value="${saved}"]`);
    if (savedInput) savedInput.checked = true;

    const applySwitch = () => {
      const value = group.querySelector('input:checked').value;
      [...paper.classList]
        .filter((name) => name.startsWith(`${kind}-`))
        .forEach((name) => paper.classList.remove(name));
      paper.classList.add(`${kind}-${value}`);
      remember(kind, value);
    };
    group.addEventListener('change', applySwitch);
    applySwitch();
  });

  copyButton.addEventListener('click', () => {
    navigator.clipboard.writeText(source.value).then(() => {
      copyButton.textContent = 'Copied';
      setTimeout(() => { copyButton.textContent = 'Copy text'; }, 1200);
    }, () => say('Clipboard is not available here.'));
  });

  function tearOff() {
    if (!source.value.trim()) {
      say('Nothing to print.');
      return;
    }
    tearButton.disabled = true;
    lamp('busy', true);
    post(LP.fileUrl, { code: source.value, language: language.value, title: titleInput.value })
      .then((data) => {
        paper.classList.add('torn');
        setTimeout(() => { window.location.href = data.url; }, 600);
      })
      .catch((err) => {
        say(err.message);
        tearButton.disabled = false;
        lamp('busy', false);
      });
  }

  tearButton.addEventListener('click', tearOff);

  // page load: lamps come on one by one, then the paper feeds and the
  // listing is struck line by line
  function powerUp() {
    lamp('power', true);
    setTimeout(() => lamp('ready', true, true), 250);
    setTimeout(() => {
      lamp('ready', true);
      lamp('online', true);
      lamp('busy', true);
      paper.classList.add('feeding');
      const lines = [...listing.children];
      lines.forEach((li, i) => strike(li, Math.min(i, 80) * 45));
      listing.classList.remove('unfed');
      setCounter(lines.length, true);
      setTimeout(() => lamp('busy', false), Math.min(lines.length, 80) * 45 + 350);
    }, 700);
  }

  powerUp();
})();
