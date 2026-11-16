/**
 * 커뮤니케이션 애플 홈페이지 문의 접수
 * - 홈페이지 문의 폼 → 이 구글 시트의 '문의' 탭에 한 줄씩 저장
 * - 접수될 때마다 NOTIFY_TO 주소로 알림 메일 발송
 * 설치 방법은 저장소의 tools/README.md 참고
 */
const SHEET_NAME = '문의';
const NOTIFY_TO = 'applegolf12@gmail.com';
const FIELDS = [
  ['name', '이름'], ['company', '회사/소속'], ['phone', '연락처'], ['email', '이메일'],
  ['type', '문의 유형'], ['size', '예상 인원'], ['date', '희망 일정·지역'], ['msg', '문의 내용'],
];

function doPost(e) {
  const p = (e && e.parameter) || {};
  // 스팸봇용 숨김 칸이 채워져 있으면 저장하지 않음
  if (p.website) return json_({ ok: true });
  if (!clean_(p.name) || !clean_(p.phone) || !clean_(p.msg)) return json_({ ok: false, error: 'missing' });

  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    const sheet = sheet_();
    const values = FIELDS.map(([key]) => safeCell_(clean_(p[key])));
    sheet.appendRow([new Date()].concat(values, ['미확인']));
  } finally {
    lock.releaseLock();
  }

  const body = FIELDS.map(([key, label]) => `${label}: ${clean_(p[key]) || '-'}`).join('\n')
    + `\n\n문의 목록: ${SpreadsheetApp.getActiveSpreadsheet().getUrl()}`;
  const mail = {
    to: NOTIFY_TO,
    subject: `[홈페이지 문의] ${clean_(p.type) || '문의'} - ${clean_(p.name)}`,
    body: body,
  };
  const email = clean_(p.email);
  if (/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) mail.replyTo = email;
  MailApp.sendEmail(mail);

  return json_({ ok: true });
}

function sheet_() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sh = ss.getSheetByName(SHEET_NAME);
  if (!sh) {
    sh = ss.insertSheet(SHEET_NAME);
    sh.appendRow(['접수 시각'].concat(FIELDS.map(([, label]) => label), ['처리 상태']));
    sh.setFrozenRows(1);
    sh.getRange(1, 1, 1, FIELDS.length + 2).setFontWeight('bold');
  }
  return sh;
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

// 설치 직후 한 번 실행해서 권한 승인 + 시트 탭 생성용
function setup() {
  sheet_();
  MailApp.getRemainingDailyQuota();
}
