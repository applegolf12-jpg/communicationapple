/* Supabase 연결 정보. url/key가 비어 있으면 로그인 기능은 숨겨지고 사이트는 기존처럼 동작합니다.
   key는 publishable(공개용) 키만 넣습니다. secret/service_role 키는 절대 넣지 마세요. */
window.SB_CONFIG = { url: 'https://odrljgellyppzobwzela.supabase.co', key: 'sb_publishable_SVIYDPejjgg4koqP5KP7Bw_L0PAzCag',
  /* false로 바꾸면 사이트의 로그인·회원가입만 숨겨집니다 (신청·문의 저장과 관리자 페이지는 그대로) */
  memberOpen: true };
