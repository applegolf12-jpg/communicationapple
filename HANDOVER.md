# 커뮤니케이션 애플 홈페이지 인수인계

새 작업자(또는 새 Claude)는 이 문서와 `src/README.md`를 먼저 읽으세요. 비밀번호와 비밀 키는 이 문서에 적지 않습니다. 계정 정보는 회사가 따로 보관합니다.

## 1. 전체 구조

| 구성 | 위치 | 역할 |
|---|---|---|
| 웹사이트 | GitHub `applegolf12-jpg/communicationapple` → GitHub Pages | communicationapple.com (도메인: 카페24, DNS가 GitHub Pages를 가리킴) |
| 사이트 원본 | 저장소 `src/` | `python3 src/build.py`로 루트의 HTML을 생성. **루트 *.html을 직접 고치지 말 것** |
| 회원·신청 DB | Supabase 프로젝트 `odrljgellyppzobwzela` (applegolf12-jpg GitHub 계정으로 로그인) | 회원가입·로그인, 아카데미 신청, 행사 문의, 관리자 권한 |
| 관리자 페이지 | communicationapple.com/admin | 신청자 관리, 차수별 현황, 문의, 매출·입금, 회원 |
| 접수 알림 | Apps Script ① ('홈페이지 문의' 시트에 붙은 프로젝트, 웹 앱으로 배포됨) | 홈페이지 신청·문의를 시트에 기록 + applegolf12@gmail.com 메일 |
| 직접 신청 동기화 | Apps Script ② '아카데미 신청' 프로젝트 | 전화로 받아 적는 명단 시트 → 관리자 페이지 (10분마다) |

## 2. 수정 작업 방법
1. 저장소를 받는다: `git clone https://github.com/applegolf12-jpg/communicationapple`
2. `src/`의 원본을 고친다. 파일 안내는 `src/README.md`
3. `python3 src/build.py` 실행 → 루트 HTML 재생성
4. 커밋 후 `main`에 push → 1~3분 뒤 사이트 반영
5. 새 이미지: 원본 파일을 저장하고 `src/blobmap.json`에 `"32자리id": "경로"` 추가, 본문에서 `/_blob/<id>`로 참조. 원본이 없으면 저장소의 `img/`, `video/`, `hero/` 파일을 그대로 씀

자주 고치는 곳
- 홈 슬라이드쇼 사진: `src/hero/h01.jpg~` + `src/index.body.html`의 `var N=` 개수
- 아카데미 차수·가격·프로·마감일: `src/js/academy-data.js` (신청서와 관리자 페이지가 함께 사용)
- 아카데미 상세 안내 이미지: `src/academy_data.py`의 `G`
- 아카이브(지난 행사): `src/archive_all.json`
- 헤더·푸터·공통 스타일: `src/build.py`

## 3. 키·설정 위치 (값은 문서에 없음)
- `src/js/config.js`: Supabase URL과 **publishable(공개용) 키**만. `memberOpen: false`로 바꾸면 사이트의 로그인·회원가입만 숨김
- Apps Script ① 스크립트 속성: `SUPABASE_URL`, `SUPABASE_KEY`(publishable), `ACADEMY_SHEET_ID`
- Apps Script ② 스크립트 속성: `SUPABASE_URL`, `SUPABASE_SECRET_KEY`(**비밀 키, 절대 공유 금지**), `ROSTER_SHEET_ID`(명단 파일 ID, 여러 개면 쉼표)
- Supabase SQL: `tools/supabase-schema.sql`, `tools/supabase-migration-02-direct.sql`, `-03-reviews.sql`(리뷰), `-04-analytics.sql`(방문 통계)
- Apps Script 코드: `tools/inquiry-apps-script.gs`
  - ①을 고친 뒤에는 **배포 → 배포 관리 → 수정 → 새 버전**. '새 배포'는 주소가 바뀌어 홈페이지 신청이 끊김
  - ②는 배포하지 않음

## 4. 관리자
- 관리자 계정: applegolf12@gmail.com (Supabase Authentication)
- 다른 직원을 관리자로: 사이트에서 회원가입 → 관리자 페이지 '회원' 탭에서 등급을 '관리자'로
- 직접 신청(시트 명단)은 관리자 페이지에서 보기만 가능. 수정은 시트에서

## 5. 명단 시트 규칙 (직접 신청 동기화)
- 탭 제목 줄에 `아마따 [1차]` / `칸차나부리 [1차]` 형식 유지
- 제목 칸 '성함'을 바꾸지 말 것. 합계 줄은 '인원'으로 시작
- 생년월일·여권번호·영문명·이메일은 관리자 페이지로 보내지 않음

## 6. 남은 일
- Gmail SMTP 설정(Supabase Authentication → Emails) — 하기 전에는 비밀번호 찾기 메일이 안 감
- 통신판매업 신고번호 푸터 표시
- 칸차나부리 명단 파일 ID를 `ROSTER_SHEET_ID`에 추가했는지 확인, `installDirectSync` 실행 여부 확인
- 명단 시트의 주민등록번호 뒷자리 보관 여부 검토
- 포스터 안의 옛 주소 `point-golf.com` 정리, point-golf.com 도메인 정리(Wix 해지 전 연결 확인)
- 카카오 로그인(선택)
