/* 방문 통계: 쿠키·IP 없이 페이지 방문과 주요 행동만 기록 */
(function () {
  try {
    if (navigator.webdriver || /bot|crawl|spider|slurp|preview|lighthouse|headless/i.test(navigator.userAgent)) return;
    var ls = window.localStorage, ss = window.sessionStorage;
    var rid = function () { return (window.crypto && crypto.randomUUID ? crypto.randomUUID() : Date.now().toString(36) + Math.random().toString(36).slice(2)).replace(/-/g, '').slice(0, 24); };
    var visitor = ls.getItem('ca_v') || rid(); ls.setItem('ca_v', visitor);
    var now = Date.now(), last = +(ss.getItem('ca_t') || 0), session = ss.getItem('ca_s');
    if (!session || now - last > 30 * 60 * 1000) { session = rid(); ss.setItem('ca_s', session); }
    ss.setItem('ca_t', String(now));
  } catch (e) { return; }
  var path = location.pathname.replace(/\/index\.html$/, '/').slice(0, 120) || '/';
  var q = new URLSearchParams(location.search), ref = q.get('utm_source') || '';
  if (!ref && document.referrer) { try { var h = new URL(document.referrer).hostname.replace(/^www\.|^m\./, ''); if (h !== location.hostname.replace(/^www\./, '')) ref = h; } catch (e) {} }
  var w = Math.min(screen.width, innerWidth), device = w < 768 ? 'mobile' : (w < 1100 && 'ontouchstart' in window ? 'tablet' : 'desktop');
  var queue = [], ready = false;
  function send(type, name) {
    var row = { visitor: visitor, session: session, type: type, path: path, name: name ? String(name).slice(0, 60) : null, ref: ref ? ref.slice(0, 120) : null, device: device };
    if (!ready) { queue.push(row); return; }
    if (window.CA && CA.sb) CA.sb.from('page_events').insert(row).then(function () {}, function () {});
  }
  window.caTrack = function (name) { send('action', name); };
  (window.CA ? CA.ready : Promise.resolve()).then(function () {
    ready = true; var q2 = queue; queue = [];
    q2.forEach(function (r) { if (window.CA && CA.sb) CA.sb.from('page_events').insert(r).then(function () {}, function () {}); });
  });
  send('view');
  document.addEventListener('click', function (e) {
    var el = e.target.closest('a,button'); if (!el) return;
    var n = el.getAttribute('data-track'), href = el.getAttribute('href') || '';
    if (!n) {
      if (/^tel:/.test(href)) n = '전화 걸기';
      else if (/^mailto:/.test(href)) n = '메일 보내기';
      else if (/smartstore\.naver\.com/.test(href)) n = '스마트스토어 이동';
      else if (/pf\.kakao|kakao\.com/.test(href)) n = '카카오톡 이동';
      else if (/instagram\.com/.test(href)) n = '인스타그램 이동';
      else if (el.hasAttribute('data-apply')) n = '신청하기 버튼 (' + (el.getAttribute('data-apply') === 'k' ? '칸차나부리' : '아마타') + ')';
      else if (el.hasAttribute('data-g')) n = '상세 안내 보기';
      else if (el.id === 'ur-open') n = '리뷰 쓰기 열기';
      else if (/contact\.html/.test(href)) n = '행사 문의 페이지로';
      else if (/academy\.html#apply/.test(href)) n = '아카데미 신청서로';
    }
    if (n) send('action', n);
  }, true);
})();
