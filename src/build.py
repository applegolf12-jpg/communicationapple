import re, os, json, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from academy_data import REV, PAST, G, CSS as ACSS

SRC = os.path.dirname(os.path.abspath(__file__)) + '/'
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(SRC.rstrip('/')) + '/'
BLOB = json.load(open(SRC + 'blobmap.json'))
MISSING = {'d8463f149276e6471e5686ccabbe898c', 'e10e6381c7c44eb1667ec0235140f0ce', '3a00d2b8cdf791e1e661ef16c3e5b3ff'}
used = set()

def ext(p):
    e = os.path.splitext(p)[1].lower()
    return '.jpg' if e == '.jpeg' else e

def fix(s):
    def rep(m):
        i = m.group(1)
        if i in MISSING: raise SystemExit('missing asset in output: ' + i)
        used.add(i)
        sub = 'video/' if ext(BLOB[i]) == '.mp4' else 'img/'
        return sub + i[:12] + ext(BLOB[i])
    s = re.sub(r'/_blob/([0-9a-f]{32})', rep, s)
    for a, b in {'Main': 'index', 'ProAm': 'proam', 'Corporate': 'corporate', 'Academy': 'academy', 'TV': 'tv', 'Contact': 'contact'}.items():
        s = s.replace(a + '.dc.html', b + '.html')
    s = s.replace('href="index.html#about"', 'href="index.html#about"')
    return s

NAV = [('index.html#about', '회사소개'), ('proam.html', '이벤트 프로암'), ('corporate.html', '기업·VIP 행사'),
       ('academy.html', '애플골프아카데미')]

def header(cur):
    links = ''
    for href, label in NAV:
        if href == cur:
            links += f'<a href="{href}" aria-current="page" class="nv on">{label}</a>'
        else:
            links += f'<a href="{href}" class="nv">{label}</a>'
    on = ' aria-current="page"' if cur == 'contact.html' else ''
    aon = ' aria-current="page"' if cur in ('login.html', 'mypage.html') else ''
    links += f'<a href="contact.html"{on} class="nv{" on" if on else ""}">행사 문의</a>'
    links += f'<a href="login.html" data-auth-link hidden{aon} class="nv cta">로그인/회원가입</a>'
    return f'''<header class="hd">
<a href="index.html" class="brand"><img src="/_blob/38b7d85e32bce85786fa19ae20b3a998" alt="" width="44" height="44" style="border-radius: 50%"><span>COMMUNICATION APPLE</span></a>
<button type="button" class="mbtn" aria-expanded="false" aria-controls="gnb" aria-label="메뉴 열기"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg></button>
<nav id="gnb" aria-label="주 메뉴">{links}</nav>
</header>'''

FOOTER = '''<footer style="background: #0E2A21; color: #DCE9E2; padding: 56px 24px">
<div style="max-width: 1320px; margin: 0 auto; display: flex; flex-wrap: wrap; justify-content: space-between; gap: 32px">
<div style="display: flex; flex-direction: column; gap: 12px">
<span style="font-family: 'Archivo', sans-serif; font-weight: 800; font-size: 20px; color: #FFFFFF; letter-spacing: 0.02em">COMMUNICATION APPLE</span>
<span style="font-size: 14px; line-height: 1.8">커뮤니케이션 애플 · 대표 양욱 · 사업자등록번호 220-87-75241<br>경기도 성남시 분당구 성남대로 51, 115<br>Tel 031-625-9017, 9018 · Fax 031-625-9010<br>applegolf12@gmail.com</span>
</div>
<nav aria-label="하단 메뉴" style="display: flex; flex-wrap: wrap; gap: 12px 28px; font-size: 14px; align-items: flex-start">
<a href="proam.html" style="color: #DCE9E2; text-decoration: none">이벤트 프로암</a>
<a href="corporate.html" style="color: #DCE9E2; text-decoration: none">기업·VIP 행사</a>
<a href="academy.html" style="color: #DCE9E2; text-decoration: none">애플골프아카데미</a>
<a href="contact.html" style="color: #DCE9E2; text-decoration: none">문의·오시는 길</a>
<a href="privacy.html" style="color: #FFFFFF; text-decoration: none; font-weight: 700">개인정보처리방침</a>
</nav>
</div>
<p style="max-width: 1320px; margin: 40px auto 0; font-size: 12px; color: #A9BFB4">© Communication Apple. All rights reserved.</p>
</footer>'''

BASE_CSS = '''html{scroll-behavior:smooth}*{box-sizing:border-box}body{margin:0;background:#fff;font-family:'Noto Sans KR',sans-serif;color:#141A17}
img,video{max-width:100%}[hidden]{display:none!important}
a{color:#1F4D3F}a:hover{color:#0E2A21}
a:focus-visible,button:focus-visible{outline:2px solid #1F4D3F;outline-offset:2px}
.hd{max-width:1320px;margin:0 auto;padding:20px 24px;display:flex;align-items:center;justify-content:space-between;gap:16px;position:relative}
.brand{display:flex;align-items:center;gap:12px;text-decoration:none;color:#141A17}
.brand span{font-family:'Archivo',sans-serif;font-weight:800;font-size:18px;letter-spacing:.02em}
#gnb{display:flex;flex-wrap:wrap;align-items:center;gap:8px 28px;font-size:15px;font-weight:500}
.nv{color:#141A17;text-decoration:none;padding:10px 0}
.nv.on{color:#1F4D3F;font-weight:700;text-decoration:underline;text-underline-offset:6px}
.nv.cta{color:#fff;background:#1F4D3F;padding:11px 20px;border-radius:999px}
.nv.cta[aria-current]{background:#0E2A21}
.mbtn{display:none;width:44px;height:44px;border:none;background:none;color:#141A17;cursor:pointer;align-items:center;justify-content:center}
@media (min-width:901px) and (max-width:1200px){#gnb{gap:8px 18px;font-size:14px}.nv.cta{padding:10px 16px}.brand span{font-size:15px}}
.brand span{white-space:nowrap}
@media (max-width:900px){
 .mbtn{display:flex}
 #gnb{display:none;position:absolute;top:100%;left:0;right:0;z-index:50;background:#fff;flex-direction:column;align-items:stretch;gap:0;padding:8px 24px 20px;border-bottom:1px solid #D5DAD6;box-shadow:0 12px 24px rgba(0,0,0,.06)}
 #gnb.open{display:flex}
 .nv{padding:14px 0;border-bottom:1px solid #EEF1EE}
 .nv.cta{margin-top:12px;text-align:center;border:none}
 .brand span{font-size:15px}
}
.card img{transition:transform .5s ease}.card:hover img{transform:scale(1.04)}
@media (prefers-reduced-motion:reduce){.mq,.lgt,.pst,.rvt{animation:none!important}}
input,select,textarea{font-family:inherit;font-size:16px;color:#141A17;border:1.5px solid #B9C2BD;border-radius:10px;padding:12px 14px;background:#fff;width:100%}
input:focus,select:focus,textarea:focus{outline:2px solid #1F4D3F;outline-offset:1px;border-color:#1F4D3F}
label{font-size:14px;font-weight:700}.fld{display:flex;flex-direction:column;gap:8px}'''

PHONE_JS = open(SRC + 'phone_js.txt').read()
import hashlib
JSV = hashlib.md5(b''.join(open(SRC + 'js/' + f, 'rb').read() for f in sorted(os.listdir(SRC + 'js')))).hexdigest()[:8]
MENU_JS = '''<script>(function(){var b=document.querySelector('.mbtn'),n=document.getElementById('gnb');b.addEventListener('click',function(){var o=n.classList.toggle('open');b.setAttribute('aria-expanded',o);b.setAttribute('aria-label',o?'메뉴 닫기':'메뉴 열기');});})();</script>'''

SITE = 'https://communicationapple.com/'
LD = '''<script type="application/ld+json">{"@context":"https://schema.org","@type":"Organization","name":"커뮤니케이션 애플","alternateName":["Communication Apple","애플골프아카데미"],"url":"https://communicationapple.com/","logo":"https://communicationapple.com/img/38b7d85e32bc.png","telephone":"+82-31-625-9017","email":"applegolf12@gmail.com","foundingDate":"2008","address":{"@type":"PostalAddress","streetAddress":"성남대로 51, 115","addressLocality":"성남시 분당구","addressRegion":"경기도","addressCountry":"KR"},"description":"VIP 골프 행사, 이벤트 프로암, 기업 골프 행사 대행 및 애플골프아카데미 운영"}</script>'''
def page(out, title, desc, cur, body, css='', js=''):
    path = '' if out == 'index.html' else out
    VERIFY = '<meta name="naver-site-verification" content="017a05e1aeebed675a19ed7f9dacaeb2ac8eafe5"><meta name="google-site-verification" content="fsuCkq6KaLA_Kb2KJJLGufaFnIuqKyokkDs-ncE9ifA">'
    head_extra = f'<link rel="canonical" href="{SITE}{path}">' + (VERIFY + LD if out == 'index.html' else '')
    if out in ('404.html', 'login.html', 'mypage.html'): head_extra = '<meta name="robots" content="noindex">'
    doc = f'''<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta property="og:type" content="website">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="https://communicationapple.com/og-logo.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="커뮤니케이션 애플 로고">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="https://communicationapple.com/og-logo.jpg">
<meta property="og:url" content="{SITE}{path}">
<meta property="og:site_name" content="커뮤니케이션 애플">
<meta property="og:locale" content="ko_KR">
{head_extra}
<link rel="icon" href="/_blob/38b7d85e32bce85786fa19ae20b3a998">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@600;800;900&amp;family=Noto+Sans+KR:wght@400;500;700;900&amp;display=swap" rel="stylesheet">
<style>{BASE_CSS}
{css}</style>
</head>
<body>
{header(cur)}
<main>
{body}
</main>
{FOOTER}
{MENU_JS}
{PHONE_JS if 'type="tel"' in body else ''}
<script src="js/config.js?v={JSV}"></script>
<script src="js/sb.js?v={JSV}"></script>
{js}
</body>
</html>
'''
    doc = fix(doc)
    assert '{{' not in doc and '<sc-' not in doc and '.dc.html' not in doc, out
    open(OUT + out, 'w').write(doc)

def dc_parts(name):
    s = open(SRC + name + '.dc.html').read()
    css = re.search(r'<style>(.*?)</style>', re.search(r'<helmet>(.*?)</helmet>', s, re.S).group(1), re.S).group(1)
    css = '\n'.join(l for l in css.splitlines() if not l.startswith(('body{', 'a{')))
    body = re.search(r'</header>(.*?)<footer', s, re.S).group(1)
    return css, body

# ---------- index ----------
logos = [('6b70cf942cf5fc3bcc8b8e0974384d6a', '코스트코 홀세일'), ('5f7be963a0c7acc154a8ffb572f7860f', '삼성생명'), ('3721b13b60598f7fe8dc64336aca4352', '아너스금융서비스'),
         ('d3c4bf5886fe433930bb6f57c0cd9c98', '아우디'), ('b34debb90643e041d7129837731d9613', 'NH투자증권'), ('b2cab20b9a22d89ba426c39b0a0bbf39', '현대캐피탈'),
         ('38a5760067e470cfce3ef0d2acf4e2e2', '파라다이스시티'), ('c0b648d0c6514e42bc8b38c2a86af59e', '한화손해보험'), ('@hanwhainvest', '한화투자증권'),
         ('@hyundaimarine', '현대해상'), ('@meritz', '메리츠화재'), ('@bmw', 'BMW'), ('@koreainvest', '한국투자증권'), ('@goodrich', '굿리치'),
         ('@modupro', '모두의 프로암'), ('@skchemical', 'SK케미칼'), ('@thefin', '더금융서비스'), ('@nhfire', 'NH농협손해보험')]
LOGO_DIR = '/home/claude/logos2/'  # 원본이 없으면 저장소의 img/logo_*.png를 그대로 사용
li = lambda i, a: f'<div class="lgi"><img src="' + (f'img/logo_{i[1:]}.png' if i.startswith('@') else f'/_blob/{i}') + f'" alt="{a}" loading="lazy"></div>'
lg = ''.join(li(i, a) for i, a in logos) + '<div aria-hidden="true" style="display:flex;align-items:center">' + ''.join(li(i, '') for i, a in logos) + '</div>'
body = open(SRC + 'index.body.html').read().replace('<!--LOGOS-->', lg)
page('index.html', '커뮤니케이션 애플 | 골프 행사 대행사 · VIP 골프 행사 · 이벤트 프로암',
     '2008년부터 VIP 고객 초청 골프 대회, 이벤트 프로암, 기업 임직원 골프 행사를 기획·운영해 온 골프 행사 전문 대행사 커뮤니케이션 애플. 애플골프아카데미 운영.',
     'index.html#about', body,
     css='''.hs img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:0;transition:opacity 1.6s ease-in-out;transform:scale(1.0)}
.hs img.on{opacity:1;animation:kb 7s ease-out forwards}
.hs img.was{transform:scale(1.07)}
.hs.paused img.on{animation-play-state:paused}
@keyframes kb{from{transform:scale(1.0)}to{transform:scale(1.07)}}
@media (prefers-reduced-motion:reduce){.hs img.on{animation:none}.hs img{transition-duration:.6s}}
.hs-btn{position:absolute;right:14px;bottom:14px;z-index:2;width:40px;height:40px;border-radius:999px;border:none;background:rgba(14,42,33,.55);color:#fff;font-size:13px;cursor:pointer;opacity:.75}
.hs-btn:hover,.hs-btn:focus-visible{opacity:1}
@keyframes mq{from{transform:translateX(0)}to{transform:translateX(-50%)}}.mq{animation:mq 40s linear infinite}
@keyframes lg{from{transform:translateX(0)}to{transform:translateX(-50%)}}.lgt{animation:lg 80s linear infinite}.lg:hover .lgt{animation-play-state:paused}
.lg{-webkit-mask-image:linear-gradient(90deg,transparent,#000 8%,#000 92%,transparent);mask-image:linear-gradient(90deg,transparent,#000 8%,#000 92%,transparent)}
.svb{position:relative;aspect-ratio:4/3;border-radius:20px;overflow:hidden;background:#EEF1EE}.svb img{position:absolute;inset:0;width:100%;height:100%;object-fit:contain;display:block}
.pb{position:relative;aspect-ratio:4/5;border-radius:14px;background:rgba(255,255,255,0.1);overflow:hidden}.pb img{position:absolute;inset:8px;width:calc(100% - 16px);height:calc(100% - 16px);object-fit:contain}
.lgi{flex:none;height:48px;margin-right:72px;display:flex;align-items:center;justify-content:center}.lgi img{height:48px;width:auto;max-width:220px;object-fit:contain;display:block}
@media (max-width:640px){.lgi{height:40px;margin-right:44px}.lgi img{height:40px;max-width:170px}#about h2{font-size:24px!important}}''')

# ---------- corporate / proam ----------
ROW = '<div class="row" style="display: flex; flex-wrap: wrap; align-items: center; gap: 6px 24px; padding: 24px 12px; border-bottom: 1px solid #D5DAD6; color: #141A17"><span style="flex: 0 0 170px; font-size: 14px; font-weight: 700; color: #1F4D3F">{date}</span><span style="flex: 1 1 340px; min-width: 0; font-size: 19px; font-weight: 700; line-height: 1.45">{title}</span>{meta}</div>'
def esc(t): return t.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
def merge_archive(body, out):
    start = body.index('<div style="border-top: 2px solid #141A17">')
    end = body.index('</section>', start)
    seg = body[start:end]
    A = json.load(open(SRC + 'archive_all.json'))[out.replace('.html','')]
    allrows = [ROW.format(date=esc(e['d']), title=esc(e['t']), meta=(f'<span style="flex: 0 1 280px; font-size: 14px; color: #5A645F">{esc(e["m"])}</span>' if e['m'] else '')) for e in A]
    pages = [allrows[i:i+10] for i in range(0, len(allrows), 10)]
    html = '<div style="border-top: 2px solid #141A17">\n' + '\n'.join(f'<div data-page="{n+1}"' + (' hidden' if n else '') + '>\n' + '\n'.join(p) + '</div>' for n, p in enumerate(pages)) + '\n</div>\n'
    html += '<p id="arch-count" style="margin: 20px 0 0; font-size: 14px; color: #5A645F; text-align: right">총 ' + str(len(allrows)) + '건</p>\n'
    html += '<nav id="pager" aria-label="아카이브 페이지" style="display: flex; flex-wrap: wrap; justify-content: center; align-items: center; gap: 8px; margin-top: 32px"></nav>\n</div>\n'
    return body[:start] + html + body[end:]
LEAD = {
 'proam.html': '기업 고객과 투어 프로가 함께 라운드하는 이벤트 프로암을 기획부터 현장 운영까지 대행합니다. <br>참가 프로 섭외, 골프장 예약과 조 편성, 시상·만찬까지 한 번에 맡기세요.',
 'corporate.html': 'VIP 고객 초청 골프 대회, 임직원 골프 행사, 컨퍼런스 연계 라운드까지. <br>골프장 섭외와 조 편성, 현장 진행, 시상·만찬 운영까지 골프 행사 전 과정을 대행합니다.'}
PAGER_JS = '''<script>(function(){var ps=document.querySelectorAll('[data-page]');var nav=document.getElementById('pager');if(ps.length<2){nav.remove();return;}var cur=1,n=ps.length;
function btn(t,l,f,dis){var b=document.createElement('button');b.type='button';b.className='pg';b.textContent=t;if(l)b.setAttribute('aria-label',l);if(dis)b.disabled=true;b.addEventListener('click',f);return b}
function dots(){var s=document.createElement('span');s.textContent='…';s.style.cssText='padding:0 4px;color:#5A645F';return s}
function go(p){cur=p;ps.forEach(function(e){e.hidden=(+e.dataset.page!==p)});render();var a=document.getElementById('archive');if(a&&a.getBoundingClientRect().top<0)a.scrollIntoView();}
function render(){nav.innerHTML='';nav.appendChild(btn('‹','이전 페이지',function(){go(cur-1)},cur===1));var w=window.innerWidth<640?1:2,last=0;
for(var i=1;i<=n;i++){if(i===1||i===n||Math.abs(i-cur)<=w){if(last&&i-last>1)nav.appendChild(dots());(function(i){var b=btn(String(i),i+'페이지',function(){go(i)});if(i===cur)b.setAttribute('aria-current','page');nav.appendChild(b)})(i);last=i;}}
nav.appendChild(btn('›','다음 페이지',function(){go(cur+1)},cur===n));}
render();})();</script>'''
PG_CSS = '''.lead{margin:24px 0 0;max-width:760px;font-size:17px;line-height:1.8;color:#3E4843;word-break:keep-all}
.pg{min-width:44px;min-height:44px;padding:0 14px;border-radius:10px;border:1.5px solid #B9C2BD;background:#fff;color:#141A17;font-family:inherit;font-size:15px;font-weight:700;cursor:pointer}
.pg[aria-current]{background:#141A17;border-color:#141A17;color:#fff}.pg:disabled{opacity:.35;cursor:default}
@media (max-width:640px){.pst img{width:300px!important;height:200px!important;margin-right:12px!important}}'''
for name, out, title, desc in [
    ('Corporate', 'corporate.html', '기업 골프 행사 대행 · VIP 골프 대회 | 커뮤니케이션 애플', 'VIP 고객 초청 골프 대회, 기업 임직원 골프 행사, 골프 컨퍼런스 기획·운영 대행. 삼성생명, 파라다이스시티, 아우디 등 골프 행사 진행 사례.'),
    ('ProAm', 'proam.html', '이벤트 프로암 대행 · 프로 동반 라운드 | 커뮤니케이션 애플', '기업 이벤트 프로암, 투어 프로 초청 VIP 라운드 기획·운영 대행. 프로 섭외부터 현장 운영까지 골프 행사 전문 대행사 커뮤니케이션 애플.')]:
    css, body = dc_parts(name)
    body = re.sub(r'<img src="/_blob/(?:d8463f149276e6471e5686ccabbe898c)"[^>]*>', '', body)
    body = merge_archive(body, out)
    k = [0]
    def pg(m):
        k[0] += 1
        return f'<div data-page="{k[0]}"' + (' hidden' if k[0] > 1 else '') + '>'
    body = re.sub(r'<sc-if value="\{\{p(\d)\}\}"[^>]*>(?=\s*<div class="row")', pg, body)
    body = re.sub(r'</div>\s*</sc-if>(\s*(?:<div data-page|</div>\s*<nav))', r'</div></div>\1', body)
    body = re.sub(r'<nav aria-label="아카이브 페이지".*?</nav>', '<nav id="pager" aria-label="아카이브 페이지" style="display: flex; justify-content: center; align-items: center; gap: 8px; margin-top: 40px"></nav>', body, flags=re.S)
    body = body.replace('<h2 style="margin: 0 0 36px; font-family: \'Archivo\'', '<h2 id="archive" style="margin: 0 0 36px; font-family: \'Archivo\'', 1)
    body = body.replace('</h1>\n</section>', '</h1>\n<p class="lead">' + LEAD[out] + '</p>\n</section>', 1)
    page(out, title, desc, out, body, css + '\n' + PG_CSS, PAGER_JS if 'data-page' in body else '')

# ---------- academy ----------
rc = lambda r: f'<div class="rc"><span class="rq">Q. {r[0]}</span><p class="ra">“{r[1]}”</p><span class="rn">{r[2]}</span></div>'
revs = ''.join(rc(r) for r in REV) + '<div aria-hidden="true" style="display:flex;align-items:stretch">' + ''.join(rc(r) for r in REV) + '</div>'
past = ''.join(f'''<div class="card" style="display: flex; flex-direction: column; gap: 10px"><div class="ppb"><img src="/_blob/{p[3]}" alt="{p[1]} 포스터" loading="lazy"></div><span style="font-size: 13px; font-weight: 700; color: #1F4D3F">{p[0]}</span><span style="font-size: 18px; font-weight: 700; line-height: 1.45">{p[1]}</span><span style="font-size: 14px; color: #5A645F">{p[2]}</span></div>''' for p in PAST)
body = open(SRC + 'academy.body.html').read().replace('<!--REVIEWS-->', revs).replace('<!--PAST-->', past)
body += '''<div id="lb" role="dialog" aria-modal="true" aria-labelledby="lbt" hidden style="position: fixed; inset: 0; z-index: 1000; background: rgba(10,16,13,0.94); display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 16px; padding: 24px">
<div style="width: 100%; max-width: 980px; display: flex; align-items: center; justify-content: space-between; gap: 16px; color: #FFFFFF"><span id="lbt" style="font-size: 15px; font-weight: 700"></span>
<button type="button" id="lbx" aria-label="닫기" style="width: 44px; height: 44px; border-radius: 50%; border: 1.5px solid rgba(255,255,255,0.6) !important; background: transparent"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"></path></svg></button></div>
<div style="width: 100%; max-width: 1100px; display: flex; align-items: center; justify-content: center; gap: 16px">
<button type="button" id="lbp" aria-label="이전 사진" style="width: 52px; height: 52px; border-radius: 50%; background: rgba(255,255,255,0.14)"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M15 18l-6-6 6-6"></path></svg></button>
<img id="lbi" alt="" style="display: block; min-width: 0; max-width: min(900px, 100%); max-height: calc(100vh - 140px); object-fit: contain; border-radius: 12px">
<button type="button" id="lbn" aria-label="다음 사진" style="width: 52px; height: 52px; border-radius: 50%; background: rgba(255,255,255,0.14)"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 18l6-6-6-6"></path></svg></button>
</div></div>'''
gal = json.dumps({k: {'t': v[0], 'i': ['/_blob/' + x for x in v[1]]} for k, v in G.items()}, ensure_ascii=False)
ajs = f'<script src="js/academy-data.js?v={JSV}"></script>\n' + open(SRC + 'apply_js.txt').read() + '''<script>(function(){var G=%s,lb=document.getElementById('lb'),im=document.getElementById('lbi'),tt=document.getElementById('lbt'),g=null,i=0,opener=null;
function show(){var n=G[g].i.length;im.src=G[g].i[i];im.alt=G[g].t+' 상세 안내 '+(i+1);tt.textContent=G[g].t+' · '+(i+1)+' / '+n;}
function open(k,el){g=k;i=0;opener=el;show();lb.hidden=false;document.body.style.overflow='hidden';document.getElementById('lbx').focus();}
function close(){lb.hidden=true;document.body.style.overflow='';if(opener)opener.focus();}
function step(d){var n=G[g].i.length;i=(i+d+n)%%n;show();}
document.querySelectorAll('[data-g]').forEach(function(b){b.addEventListener('click',function(){open(b.dataset.g,b)})});
document.getElementById('lbx').addEventListener('click',close);document.getElementById('lbp').addEventListener('click',function(){step(-1)});document.getElementById('lbn').addEventListener('click',function(){step(1)});
lb.addEventListener('click',function(e){if(e.target===lb)close()});
document.addEventListener('keydown',function(e){if(lb.hidden)return;if(e.key==='Escape')close();if(e.key==='ArrowLeft')step(-1);if(e.key==='ArrowRight')step(1);});
var sx=null;lb.addEventListener('touchstart',function(e){sx=e.touches[0].clientX},{passive:true});lb.addEventListener('touchend',function(e){if(sx===null)return;var dx=e.changedTouches[0].clientX-sx;if(Math.abs(dx)>50)step(dx<0?1:-1);sx=null;});
})();</script>''' % gal
page('academy.html', '애플골프아카데미 | 해외 골프 전지훈련 · 동계 골프 레슨 캠프', '투어 프로와 함께하는 해외 골프 전지훈련 애플골프아카데미. 2027 동계 태국 칸차나부리·아마타 골프 아카데미 모집 중.', 'academy.html', body,
     ACSS + '\n' + open(SRC + 'apply_css.txt').read() + '\n.ppb{position:relative;aspect-ratio:3/4;border-radius:20px;background:#E3E8E4;overflow:hidden}.ppb img{position:absolute;inset:12px;width:calc(100% - 24px);height:calc(100% - 24px);object-fit:contain;transition:transform .5s ease}\n@media (max-width:640px){#lbp,#lbn{display:none!important}}', ajs)

# ---------- contact ----------
cjs = '''<script>(function(){var URL_='https://script.google.com/macros/s/AKfycbzhxdmpaMAjDgBlKLcWKRUhzRguJeHrj44hPz4J7pTjutgs4Lx3ZFxxPX8HWqaTiKO3/exec';
var f=document.getElementById('inq'),er=document.getElementById('f-err'),btn=f.querySelector('button[type=submit]'),done=document.getElementById('inq-done');
function v(id){return document.getElementById(id).value.trim()}
f.addEventListener('submit',function(e){e.preventDefault();var miss=[];['f-name','f-phone','f-msg'].forEach(function(id){var el=document.getElementById(id);var bad=!el.value.trim();el.setAttribute('aria-invalid',bad);if(bad)miss.push(el.labels[0].textContent.replace(' *',''))});
if(miss.length){er.textContent=miss.join(', ')+' 항목을 입력해 주세요.';er.hidden=false;return;}
if(!document.getElementById('f-agree').checked){er.textContent='개인정보 수집·이용에 동의해 주세요.';er.hidden=false;return;}
er.hidden=true;btn.disabled=true;btn.textContent='보내는 중…';
var d=new URLSearchParams({name:v('f-name'),company:v('f-company'),phone:v('f-phone'),email:v('f-email'),type:v('f-type'),size:v('f-size'),date:v('f-date'),msg:v('f-msg'),website:v('f-web')});
var dbp=(!window.CA||v('f-web'))?Promise.reject('off'):CA.save('inquiries',{name:v('f-name'),company:v('f-company')||null,phone:v('f-phone'),email:v('f-email')||null,type:v('f-type')||null,size:v('f-size')||null,event_date:v('f-date')||null,message:v('f-msg')});
Promise.allSettled([dbp,fetch(URL_,{method:'POST',mode:'no-cors',body:d})]).then(function(rs){if(rs[0].status==='rejected'&&rs[1].status==='rejected')throw 0;f.hidden=true;done.hidden=false;done.focus();window.scrollTo({top:done.getBoundingClientRect().top+scrollY-120,behavior:'smooth'});})
.catch(function(){er.textContent='전송에 실패했습니다. 잠시 후 다시 시도하시거나 031-625-9017로 전화 주세요.';er.hidden=false;btn.disabled=false;btn.textContent='문의 보내기';});});
document.getElementById('inq-again').addEventListener('click',function(){f.reset();f.hidden=false;done.hidden=true;btn.disabled=false;btn.textContent='문의 보내기';});})();</script>'''
page('contact.html', '행사 문의·오시는 길 | 커뮤니케이션 애플', '골프 행사, 이벤트 프로암, 애플골프아카데미 문의. 경기도 성남시 분당구 성남대로 51.', 'contact.html', open(SRC + 'contact.body.html').read(), js=cjs)

# ---------- 회원 ----------
AUTH_CSS = open(SRC + 'auth_css.txt').read()
page('login.html', '로그인·회원가입 | 커뮤니케이션 애플', '애플골프아카데미 회원 로그인과 회원가입.', 'login.html', open(SRC + 'login.body.html').read(), AUTH_CSS, open(SRC + 'login_js.txt').read())
page('mypage.html', '마이페이지 | 커뮤니케이션 애플', '아카데미 신청 내역과 내 정보 관리.', 'mypage.html', open(SRC + 'mypage.body.html').read(), AUTH_CSS, open(SRC + 'mypage_js.txt').read())
page('privacy.html', '개인정보처리방침 | 커뮤니케이션 애플', '커뮤니케이션 애플 개인정보처리방침.', '', open(SRC + 'privacy.body.html').read(), AUTH_CSS + '\n.pv p,.pv li{font-size:15px;line-height:1.8;color:#3E4843;word-break:keep-all;margin:0}.pv h2{margin:12px 0 0;font-size:19px;font-weight:900}.pv ul{margin:0;padding-left:20px;display:flex;flex-direction:column;gap:6px}')

# ---------- 404 ----------
page('404.html', '페이지를 찾을 수 없습니다 | 커뮤니케이션 애플', '요청하신 페이지를 찾을 수 없습니다.', '', '''<section style="max-width: 760px; margin: 0 auto; padding: 120px 24px; text-align: center; display: flex; flex-direction: column; align-items: center; gap: 20px"><h1 style="margin: 0; font-size: 40px; font-weight: 900">페이지를 찾을 수 없습니다</h1><p style="margin: 0; color: #3E4843">주소가 바뀌었거나 삭제된 페이지입니다.</p><a href="index.html" style="display: inline-flex; align-items: center; min-height: 52px; padding: 0 32px; border-radius: 10px; background: #1F4D3F; color: #FFFFFF; text-decoration: none; font-weight: 700">홈으로</a></section>''')

# ---------- assets ----------
shutil.copy(SRC + 'og-logo.jpg', OUT + 'og-logo.jpg')
shutil.rmtree(OUT + 'hero', ignore_errors=True); shutil.copytree(SRC + 'hero', OUT + 'hero')
shutil.rmtree(OUT + 'js', ignore_errors=True); shutil.copytree(SRC + 'js', OUT + 'js')
shutil.rmtree(OUT + 'admin', ignore_errors=True); shutil.copytree(SRC + 'admin', OUT + 'admin')
_ad = open(OUT + 'admin/index.html').read().replace('../js/config.js', '../js/config.js?v=' + JSV).replace('../js/academy-data.js', '../js/academy-data.js?v=' + JSV)
open(OUT + 'admin/index.html', 'w').write(_ad)
# 원본 파일(blobmap.json 경로)이 있으면 복사, 없으면 저장소에 이미 있는 결과 파일을 그대로 사용
keep = set()
def put(src, dst):
    keep.add(os.path.normpath(dst))
    if os.path.exists(src):
        if not os.path.exists(dst) or open(src, 'rb').read() != open(dst, 'rb').read(): shutil.copy(src, dst)
    elif not os.path.exists(dst): raise SystemExit('asset missing: ' + dst)
for d in ('img', 'video'): os.makedirs(OUT + d, exist_ok=True)
for i in sorted(used):
    sub = 'video/' if ext(BLOB[i]) == '.mp4' else 'img/'
    put(BLOB[i], OUT + sub + i[:12] + ext(BLOB[i]))
for i, a in logos:
    if i.startswith('@'): put(LOGO_DIR + i[1:] + '.png', OUT + 'img/logo_' + i[1:] + '.png')
for d in ('img', 'video'):
    for f in os.listdir(OUT + d):
        if os.path.normpath(OUT + d + '/' + f) not in keep: os.remove(OUT + d + '/' + f)
import datetime
today = datetime.date.today().isoformat()
urls = ['', 'proam.html', 'corporate.html', 'academy.html', 'contact.html', 'privacy.html']
open(OUT + 'sitemap.xml', 'w').write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + ''.join(f'<url><loc>{SITE}{u}</loc><lastmod>{today}</lastmod></url>\n' for u in urls) + '</urlset>\n')
open(OUT + 'robots.txt', 'w').write(f'User-agent: *\nAllow: /\nDisallow: /tools/\nDisallow: /src/\nDisallow: /admin/\nDisallow: /mypage.html\n\nSitemap: {SITE}sitemap.xml\n')
print('pages ok; assets', len(used))
