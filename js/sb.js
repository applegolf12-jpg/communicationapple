/* 로그인 상태 공통 처리 */
(function () {
  var C = window.SB_CONFIG || {};
  var on = !!(C.url && C.key && C.memberOpen !== false);
  var CA = window.CA = { on: on, sb: null, user: null, profile: null };
  function load() {
    if (window.supabase) return Promise.resolve();
    return new Promise(function (ok, no) {
      var s = document.createElement('script');
      s.src = 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.119.0/dist/umd/supabase.js';
      s.onload = ok; s.onerror = no; document.head.appendChild(s);
    });
  }
  CA.loadProfile = function () {
    if (!CA.user) { CA.profile = null; return Promise.resolve(null); }
    return CA.sb.from('profiles').select('*').eq('id', CA.user.id).maybeSingle()
      .then(function (r) { CA.profile = r.data || null; return CA.profile; });
  };
  CA.ready = !on ? Promise.resolve(null) : load().then(function () {
    CA.sb = window.supabase.createClient(C.url, C.key);
    return CA.sb.auth.getSession();
  }).then(function (r) {
    CA.user = (r.data.session && r.data.session.user) || null;
    return CA.loadProfile();
  }).then(function () { return CA.user; }).catch(function (e) {
    console.warn('auth unavailable', e); CA.on = false; return null;
  });
  CA.ready.then(function (u) {
    document.querySelectorAll('[data-auth-link]').forEach(function (a) {
      if (!CA.on) { a.remove(); return; }
      a.hidden = false;
      if (u) { a.textContent = '마이페이지'; a.href = 'mypage.html'; }
      else { a.textContent = '로그인'; a.href = 'login.html'; }
    });
  });
  CA.err = function (e) {
    var m = (e && (e.message || e.error_description)) || '';
    if (/Invalid login credentials/i.test(m)) return '이메일 또는 비밀번호가 맞지 않습니다.';
    if (/Email not confirmed/i.test(m)) return '이메일 인증이 아직 완료되지 않았습니다. 받은 메일의 링크를 눌러 주세요.';
    if (/already registered|already been registered|User already/i.test(m)) return '이미 가입된 이메일입니다. 로그인하거나 비밀번호 찾기를 이용해 주세요.';
    if (/Password should be|weak/i.test(m)) return '비밀번호가 너무 약합니다. 8자 이상으로 영문과 숫자를 섞어 주세요.';
    if (/rate limit|too many/i.test(m)) return '요청이 너무 많습니다. 잠시 후 다시 시도해 주세요.';
    if (/same.*password|different from the old/i.test(m)) return '기존 비밀번호와 다른 비밀번호를 입력해 주세요.';
    if (/Failed to fetch|network/i.test(m)) return '서버에 연결하지 못했습니다. 인터넷 연결을 확인해 주세요.';
    return '처리 중 문제가 발생했습니다. 잠시 후 다시 시도하시거나 031-625-9017로 연락 주세요.';
  };
})();
