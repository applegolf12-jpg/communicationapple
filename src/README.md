# 사이트 원본

사이트의 HTML은 이 폴더의 원본에서 생성합니다. **루트의 *.html을 직접 고치지 말고 여기를 고친 뒤 다시 생성하세요.**

```
python3 src/build.py      # 저장소 루트에 index.html 등 생성
```

| 파일 | 내용 |
|---|---|
| `build.py` | 공통 헤더·푸터·스타일, 페이지 생성, sitemap/robots |
| `*.body.html` | 각 페이지 본문 (index, academy, contact, login, mypage, privacy) |
| `ProAm.dc.html`, `Corporate.dc.html` | 프로암·기업행사 페이지 본문 (디자인 캔버스 원본) |
| `archive_all.json` | 프로암·기업행사 아카이브 목록 |
| `academy_data.py` | 아카데미 후기, 지난 아카데미, 상세 이미지 |
| `apply_js.txt`, `apply_css.txt` | 아카데미 신청서 |
| `js/` | 공용 스크립트 (Supabase 연결 `config.js`, 로그인 `sb.js`, 차수 데이터 `academy-data.js`) |
| `admin/` | 관리자 페이지 |
| `blobmap.json` | 이미지 원본 경로. 원본이 없으면 저장소의 `img/`, `video/` 파일을 그대로 씁니다 |

새 이미지를 넣을 때는 blobmap.json에 `"32자리 id": "원본 경로"`를 추가하고 본문에서 `/_blob/<id>`로 참조합니다.
