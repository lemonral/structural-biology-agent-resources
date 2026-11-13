(() => {
  document.querySelectorAll('[data-phase]').forEach(button => button.addEventListener('click', () => {
    const section = button.closest('.section');
    section.querySelectorAll('[data-phase]').forEach(b => b.setAttribute('aria-pressed', String(b === button)));
    section.querySelectorAll('[data-phase-panel]').forEach(panel => { panel.hidden = panel.dataset.phasePanel !== button.dataset.phase; });
  }));
  const checks = [...document.querySelectorAll('[data-readiness]')];
  const updateChecks = () => { const out = document.getElementById('readiness-count'); if (out) out.textContent = `已核对 ${checks.filter(c => c.checked).length} / ${checks.length} 项`; };
  checks.forEach(c => c.addEventListener('change', updateChecks));
  document.getElementById('reset-readiness')?.addEventListener('click', () => { checks.forEach(c => { c.checked = false; }); updateChecks(); });
  const payload = document.getElementById('production-cases');
  if (!payload) return;
  const cases = JSON.parse(payload.textContent);
  const el = (tag, value, cls) => { const node = document.createElement(tag); if (value !== undefined) node.textContent = value; if (cls) node.className = cls; return node; };
  const renderEvent = (c, index) => {
    const event = c.events[index]; const target = document.getElementById('case-event-detail'); target.replaceChildren();
    target.append(el('div', `TIME ${event.time} / EVENT ${index + 1}`, 'eyebrow'), el('h4', event.actor), el('p', event.event));
    if (event.time.includes('分支')) target.append(el('p', '这是与主线并列的另一种结果，用来说明何时必须停止自动恢复；不是主线后续必须发生的步骤。', 'small'));
    target.append(el('div', '此刻记录的状态', 'eyebrow'), el('span', typeof event.state === 'string' ? event.state : JSON.stringify(event.state, null, 2), 'p-state'));
    document.querySelectorAll('[data-event]').forEach(b => b.setAttribute('aria-pressed', String(Number(b.dataset.event) === index)));
  };
  const renderCase = index => {
    const c = cases[index];
    document.getElementById('case-title').textContent = c.title;
    document.getElementById('case-task').textContent = c.task;
    document.getElementById('case-scope').textContent = c.scope_note;
    document.querySelectorAll('[data-case]').forEach(b => b.setAttribute('aria-pressed', String(Number(b.dataset.case) === index)));
    const events = document.getElementById('case-events'); events.replaceChildren();
    c.events.forEach((event, i) => {
      const button = el('button'); button.type = 'button'; button.dataset.event = String(i); button.setAttribute('aria-pressed', String(i === 0));
      if (event.time.includes('分支')) button.classList.add('p-event-alternative');
      const info = el('span'); info.append(el('b', event.actor), el('span', typeof event.state === 'string' ? event.state : JSON.stringify(event.state)));
      button.append(el('time', event.time), info); button.addEventListener('click', () => renderEvent(c, i)); events.append(button);
    });
    const lessons = document.getElementById('case-lessons'); lessons.replaceChildren();
    for (const [key, title] of [['root_cause', '根因'], ['recovery', '恢复依据'], ['prevention', '如何预防'], ['acceptance', '验收应该证明什么']]) {
      const article = el('article'); article.append(el('h4', title));
      if (Array.isArray(c[key])) { const list = el('ul'); c[key].forEach(item => list.append(el('li', item))); article.append(list); }
      else article.append(el('p', c[key]));
      lessons.append(article);
    }
    renderEvent(c, 0);
  };
  document.querySelectorAll('[data-case]').forEach(b => b.addEventListener('click', () => renderCase(Number(b.dataset.case))));
  const hashCase = cases.findIndex(c => '#' + c.id === location.hash);
  renderCase(hashCase < 0 ? 0 : hashCase);
})();
