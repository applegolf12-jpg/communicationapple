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
