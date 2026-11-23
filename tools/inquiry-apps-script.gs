/**
 * 커뮤니케이션 애플 홈페이지 접수
 * - 행사 문의 → 이 구글 시트(홈페이지 문의)의 '문의' 탭
 * - 아카데미 신청 → 별도 구글 시트 '홈페이지 아카데미 신청' (setup 실행 시 자동 생성)
 * - 접수될 때마다 NOTIFY_TO 주소로 알림 메일 발송
 * 설치·수정 방법은 저장소의 tools/README.md 참고
 */
const NOTIFY_TO = 'applegolf12@gmail.com';

const INQUIRY_SHEET = '문의';
const INQUIRY_FIELDS = [
  ['name', '이름'], ['company', '회사/소속'], ['phone', '연락처'], ['email', '이메일'],
  ['type', '문의 유형'], ['size', '예상 인원'], ['date', '희망 일정·지역'], ['msg', '문의 내용'],
];

const ACADEMY_FILE_NAME = '홈페이지 아카데미 신청';
const ACADEMY_SHEET = '신청';
const ACADEMY_FIELDS = [
  ['product', '상품'], ['session', '차수'], ['period', '일정'], ['pro', '레슨 프로'],
  ['people', '참가 인원'], ['single', '1인실'], ['name', '신청자'], ['phone', '휴대폰'],
  ['mates', '동반자'], ['total', '예상 금액'], ['breakdown', '금액 내역'], ['request', '요청사항'],
];

function doPost(e) {
  const p = (e && e.parameter) || {};
  if (p.website) return json_({ ok: true }); // 스팸봇용 숨김 칸
  if (p.action === 'sendCode') return sendCode_(p);
  if (p.action === 'verifyCode') return verifyCode_(p);
  if (p.kind === 'academy' && smsReady_()) {
    const cache = CacheService.getScriptCache();
    const phone = digits_(p.phone);
    if (!p.token || cache.get('tok:' + p.token) !== phone) return json_({ ok: false, error: 'verify' });
    cache.remove('tok:' + p.token);
  }
  if (!clean_(p.name) || !clean_(p.phone)) return json_({ ok: false, error: 'missing' });

  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  let sheetUrl;
  try {
    if (p.kind === 'academy') {
      const ss = academyBook_();
      append_(ss, ACADEMY_SHEET, ACADEMY_FIELDS, p, ['처리 상태', '결제 금액', '메모']);
      sheetUrl = ss.getUrl();
    } else {
      if (!clean_(p.msg)) return json_({ ok: false, error: 'missing' });
      const ss = SpreadsheetApp.getActiveSpreadsheet();
      append_(ss, INQUIRY_SHEET, INQUIRY_FIELDS, p, ['처리 상태']);
      sheetUrl = ss.getUrl();
    }
  } finally {
    lock.releaseLock();
  }

  const isAcademy = p.kind === 'academy';
  const fields = isAcademy ? ACADEMY_FIELDS : INQUIRY_FIELDS;
  const mail = {
    to: NOTIFY_TO,
    subject: isAcademy
      ? `[아카데미 신청] - ${clean_(p.place) || '아카데미'} - ${clean_(p.name)}`
      : `[홈페이지 문의] ${clean_(p.type) || '문의'} - ${clean_(p.name)}`,
    body: fields.map(([key, label]) => `${label}: ${clean_(p[key]) || '-'}`).join('\n')
      + `\n\n시트 바로가기: ${sheetUrl}`,
  };
  const email = clean_(p.email);
  if (/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) mail.replyTo = email;
  MailApp.sendEmail(mail);

  return json_({ ok: true });
}

function append_(ss, tabName, fields, p, extraHeaders) {
  let sh = ss.getSheetByName(tabName);
  if (!sh) {
    sh = ss.insertSheet(tabName);
    const header = ['접수 시각'].concat(fields.map(([, label]) => label), extraHeaders);
    sh.appendRow(header);
    sh.setFrozenRows(1);
    sh.getRange(1, 1, 1, header.length).setFontWeight('bold');
  }
  const row = [new Date()].concat(fields.map(([key]) => safeCell_(clean_(p[key]))), ['미확인']);
  sh.appendRow(row);
}

// 아카데미 신청 시트: 처음 한 번 만들고, 이후에는 같은 파일을 계속 사용
function academyBook_() {
  const props = PropertiesService.getScriptProperties();
  const id = props.getProperty('ACADEMY_SHEET_ID');
  if (id) {
    try { return SpreadsheetApp.openById(id); } catch (err) { /* 삭제된 경우 새로 만듦 */ }
  }
  const ss = SpreadsheetApp.create(ACADEMY_FILE_NAME);
  const first = ss.getSheets()[0];
  first.setName(ACADEMY_SHEET);
  const header = ['접수 시각'].concat(ACADEMY_FIELDS.map(([, label]) => label), ['처리 상태', '결제 금액', '메모']);
  first.appendRow(header);
  first.setFrozenRows(1);
  first.getRange(1, 1, 1, header.length).setFontWeight('bold');
  props.setProperty('ACADEMY_SHEET_ID', ss.getId());
  return ss;
}

// ───────── 휴대폰 인증 (솔라피) ─────────
// 스크립트 속성: SOLAPI_API_KEY, SOLAPI_API_SECRET, SOLAPI_SENDER(등록된 발신번호, 숫자만)
const CODE_TTL = 180;        // 인증번호 유효 시간(초)
const RESEND_WAIT = 60;      // 같은 번호 재발송 대기(초)
const PER_PHONE_HOURLY = 5;  // 같은 번호 1시간 최대 발송
const DAILY_LIMIT = 200;     // 하루 전체 최대 발송

function smsReady_() {
  const pr = PropertiesService.getScriptProperties();
  return !!(pr.getProperty('SOLAPI_API_KEY') && pr.getProperty('SOLAPI_API_SECRET') && pr.getProperty('SOLAPI_SENDER'));
}

function digits_(v) { return String(v || '').replace(/\D/g, ''); }

function sendCode_(p) {
  if (!smsReady_()) return json_({ ok: false, error: 'not_configured' });
  const phone = digits_(p.phone);
  if (!/^01[016789]\d{7,8}$/.test(phone)) return json_({ ok: false, error: 'phone' });
  const cache = CacheService.getScriptCache();
  if (cache.get('wait:' + phone)) return json_({ ok: false, error: 'wait', wait: RESEND_WAIT });
  const hourKey = 'hr:' + phone, hourCount = Number(cache.get(hourKey) || 0);
  if (hourCount >= PER_PHONE_HOURLY) return json_({ ok: false, error: 'too_many' });
  const dayKey = 'day:' + Utilities.formatDate(new Date(), 'Asia/Seoul', 'yyyyMMdd');
  const props = PropertiesService.getScriptProperties();
  const dayCount = Number(props.getProperty(dayKey) || 0);
  if (dayCount >= DAILY_LIMIT) return json_({ ok: false, error: 'daily' });

  const code = String(Math.floor(100000 + Math.random() * 900000));
  const res = solapiSend_(phone, '[커뮤니케이션 애플] 인증번호 [' + code + '] 를 입력해 주세요. (3분 이내)');
  if (!res.ok) return json_({ ok: false, error: 'send_failed' });

  cache.put('code:' + phone, JSON.stringify({ c: code, n: 0 }), CODE_TTL);
  cache.put('wait:' + phone, '1', RESEND_WAIT);
  cache.put(hourKey, String(hourCount + 1), 3600);
  props.setProperty(dayKey, String(dayCount + 1));
  return json_({ ok: true, ttl: CODE_TTL });
}

function verifyCode_(p) {
  const phone = digits_(p.phone);
  const cache = CacheService.getScriptCache();
  const raw = cache.get('code:' + phone);
  if (!raw) return json_({ ok: false, error: 'expired' });
  const data = JSON.parse(raw);
  if (data.n >= 5) { cache.remove('code:' + phone); return json_({ ok: false, error: 'too_many' }); }
  if (String(p.code || '').trim() !== data.c) {
    data.n += 1;
    cache.put('code:' + phone, JSON.stringify(data), CODE_TTL);
    return json_({ ok: false, error: 'mismatch', left: 5 - data.n });
  }
  cache.remove('code:' + phone);
  const token = Utilities.getUuid().replace(/-/g, '');
  cache.put('tok:' + token, phone, 1800); // 인증 후 30분 안에 신청서 제출
  return json_({ ok: true, token: token });
}

function solapiSend_(to, text) {
  const pr = PropertiesService.getScriptProperties();
  const key = pr.getProperty('SOLAPI_API_KEY'), secret = pr.getProperty('SOLAPI_API_SECRET');
  const date = new Date().toISOString();
  const salt = Utilities.getUuid().replace(/-/g, '');
  const sig = Utilities.computeHmacSha256Signature(date + salt, secret)
    .map(function (b) { return ('0' + (b & 0xff).toString(16)).slice(-2); }).join('');
  const resp = UrlFetchApp.fetch('https://api.solapi.com/messages/v4/send', {
    method: 'post',
    contentType: 'application/json',
    headers: { Authorization: 'HMAC-SHA256 apiKey=' + key + ', date=' + date + ', salt=' + salt + ', signature=' + sig },
    payload: JSON.stringify({ message: { to: to, from: digits_(pr.getProperty('SOLAPI_SENDER')), text: text } }),
    muteHttpExceptions: true,
  });
  const ok = resp.getResponseCode() < 300;
  if (!ok) console.error('SOLAPI ' + resp.getResponseCode() + ' ' + resp.getContentText());
  return { ok: ok };
}

// 문자 발송 테스트: 아래 번호를 본인 휴대폰으로 바꾸고 이 함수를 실행
function testSms() {
  const r = solapiSend_('01000000000', '[커뮤니케이션 애플] 문자 발송 테스트입니다.');
  Logger.log(r.ok ? '발송 성공' : '발송 실패 — 실행 기록의 오류 내용을 확인하세요');
}

function clean_(v) {
  return String(v == null ? '' : v).trim().slice(0, 3000);
}

// 시트에서 수식으로 실행되지 않도록 =, +, -, @ 로 시작하는 값 앞에 ' 를 붙임
function safeCell_(v) {
  return /^[=+\-@]/.test(v) ? "'" + v : v;
}

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}

// 설치·수정 직후 한 번 실행: 권한 승인 + 아카데미 신청 시트 생성
function setup() {
  const ss = academyBook_();
  MailApp.getRemainingDailyQuota();
  Logger.log('아카데미 신청 시트: ' + ss.getUrl());
}

// ───────── Supabase 일시정지 방지 ─────────
// 스크립트 속성에 SUPABASE_URL(https://xxxx.supabase.co), SUPABASE_KEY(publishable 키)를 넣고
// installKeepAlive 를 한 번 실행하면 매일 새벽 한 번 DB를 호출합니다.
function keepSupabaseAwake() {
  const p = PropertiesService.getScriptProperties();
  const url = p.getProperty('SUPABASE_URL'), key = p.getProperty('SUPABASE_KEY');
  if (!url || !key) return;
  const res = UrlFetchApp.fetch(url.replace(/\/$/, '') + '/rest/v1/rpc/ping', {
    method: 'post', contentType: 'application/json', payload: '{}', muteHttpExceptions: true,
    headers: { apikey: key }
  });
  Logger.log('Supabase ping: ' + res.getResponseCode() + ' ' + res.getContentText());
}
function installKeepAlive() {
  ScriptApp.getProjectTriggers().filter(t => t.getHandlerFunction() === 'keepSupabaseAwake')
    .forEach(t => ScriptApp.deleteTrigger(t));
  ScriptApp.newTrigger('keepSupabaseAwake').timeBased().everyDays(1).atHour(4).create();
  keepSupabaseAwake();
}


// ───────── 직접 신청 명단(구글 시트) → 관리자 페이지 동기화 ─────────
// 스크립트 속성: ROSTER_SHEET_ID(명단 스프레드시트 주소의 /d/와 /edit 사이 값), SUPABASE_URL, SUPABASE_SECRET_KEY(sb_secret_...)
// installDirectSync 를 한 번 실행하면 10분마다 자동으로 반영됩니다. 바로 반영하려면 syncDirect 실행.
// 관리자 페이지로는 이름·연락처·그룹·지정 프로·객실 구분·입금·비고·요청사항만 보냅니다.
// 생년월일·여권번호·영문 이름·이메일은 보내지 않습니다.
function syncDirect() {
  const p = PropertiesService.getScriptProperties();
  const id = p.getProperty('ROSTER_SHEET_ID'), url = p.getProperty('SUPABASE_URL'), key = p.getProperty('SUPABASE_SECRET_KEY');
  if (!id || !url || !key) throw new Error('스크립트 속성 ROSTER_SHEET_ID, SUPABASE_URL, SUPABASE_SECRET_KEY 를 먼저 넣어 주세요.');
  const rows = [], report = [];
  SpreadsheetApp.openById(id).getSheets().forEach(sh => {
    const r = parseRosterSheet_(sh);
    if (!r) { report.push('건너뜀: ' + sh.getName()); return; }
    report.push(sh.getName() + ' → ' + r.place + ' ' + r.session + '차 ' + r.rows.length + '명');
    r.rows.forEach(x => rows.push(x));
  });
  const res = UrlFetchApp.fetch(url.replace(/\/$/, '') + '/rest/v1/rpc/replace_direct', {
    method: 'post', contentType: 'application/json', muteHttpExceptions: true,
    headers: { apikey: key }, payload: JSON.stringify({ rows: rows })
  });
  Logger.log(report.join('\n'));
  Logger.log('Supabase: ' + res.getResponseCode() + ' ' + res.getContentText().slice(0, 300));
  if (res.getResponseCode() >= 300) throw new Error('관리자 페이지 반영 실패: ' + res.getContentText().slice(0, 300));
  return rows.length;
}

function parseRosterSheet_(sh) {
  const v = sh.getDataRange().getDisplayValues();
  if (v.length < 4) return null;
  const norm = s => String(s || '').replace(/\s+/g, '');
  const title = v.slice(0, 2).map(r => r.join(' ')).join(' ');
  const m = title.match(/(아마[따타]|칸차나부리)\s*\[?\s*(\d+)\s*차/);
  if (!m) return null;
  const place = m[1].indexOf('칸') === 0 ? '칸차나부리' : '아마타', session = +m[2];
  let h = -1;
  for (let i = 0; i < Math.min(v.length, 8); i++) if (v[i].some(c => norm(c) === '성함')) { h = i; break; }
  if (h < 0) return null;
  const top = v[h - 1] || [], sub = v[h];
  const col = (name, group) => {
    let g = '';
    for (let j = 0; j < sub.length; j++) {
      if (norm(top[j])) g = norm(top[j]);
      const n = norm(sub[j]) || norm(top[j]);
      if (n === name && (!group || g === group)) return j;
    }
    return -1;
  };
  const C = { name: col('성함'), phone: col('연락처'), group: col('그룹'), pro: col('지정프로'), room: col('구분', '객실'),
    amount: col('금액'), paidAt: col('입금일자'), memo: col('비고'), req: col('요청사항') };
  if (C.name < 0) return null;
  const cell = (r, k) => (C[k] >= 0 ? String(r[C[k]] || '').trim() : '');
  const out = [];
  for (let i = h + 1; i < v.length; i++) {
    const r = v[i];
    if (r.slice(0, 4).some(c => norm(c) === '인원' || norm(c) === '예정')) break;
    const name = cell(r, 'name');
    if (!name) continue;
    const d = cell(r, 'phone').replace(/\D/g, '');
    const phone = /^01\d{8,9}$/.test(d) ? d.replace(/^(\d{3})(\d{3,4})(\d{4})$/, '$1-$2-$3') : (cell(r, 'phone') || null);
    const amount = parseInt(cell(r, 'amount').replace(/[^\d]/g, ''), 10) || 0;
    const pd = cell(r, 'paidAt').match(/(\d{1,2})\s*[\/.]\s*(\d{1,2})/);
    let paidAt = null;
    if (pd) {
      const now = new Date(), dt = new Date(now.getFullYear(), +pd[1] - 1, +pd[2]);
      if (dt - now > 45 * 864e5) dt.setFullYear(dt.getFullYear() - 1);
      paidAt = Utilities.formatDate(dt, 'Asia/Seoul', 'yyyy-MM-dd');
    }
    out.push({ place: place, session_no: session, name: name.slice(0, 50), phone: phone,
      group_label: cell(r, 'group') || null, pro: cell(r, 'pro') || null,
      single_rooms: /1\s*인/.test(cell(r, 'room')) ? 1 : 0,
      paid_amount: amount, paid_at: paidAt, status: (amount > 0 || paidAt) ? '입금확인' : '신청접수',
      memo: cell(r, 'memo') || null, request: cell(r, 'req') || null, sheet_row: i + 1 });
  }
  return { place: place, session: session, rows: out };
}

function installDirectSync() {
  ScriptApp.getProjectTriggers().filter(t => t.getHandlerFunction() === 'syncDirect').forEach(t => ScriptApp.deleteTrigger(t));
  ScriptApp.newTrigger('syncDirect').timeBased().everyMinutes(10).create();
  syncDirect();
}
