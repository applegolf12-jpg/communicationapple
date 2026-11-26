-- 4단계: 방문 통계 (쿠키·IP 없이 페이지 방문과 주요 행동만 기록)
-- Supabase → SQL Editor → New query 에 붙여넣고 Run. 여러 번 실행해도 안전합니다.

create table if not exists public.page_events (
  id bigint generated always as identity primary key,
  at timestamptz not null default now(),
  visitor text not null check (char_length(visitor) between 8 and 40),
  session text not null check (char_length(session) between 8 and 40),
  type text not null check (type in ('view', 'action')),
  path text not null check (char_length(path) <= 120),
  name text check (char_length(name) <= 60),
  ref text check (char_length(ref) <= 120),
  device text check (device in ('mobile', 'tablet', 'desktop'))
);
create index if not exists page_events_at on public.page_events (at);

create or replace function public.page_events_guard() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  new.at := now();
  -- 같은 방문자가 1분에 60건 넘게 보내면 무시 (조작·오류 방지)
  if (select count(*) from public.page_events where visitor = new.visitor and at > now() - interval '1 minute') >= 60 then
    return null;
  end if;
  return new;
end $$;
drop trigger if exists page_events_guard on public.page_events;
create trigger page_events_guard before insert on public.page_events
  for each row execute function public.page_events_guard();

alter table public.page_events enable row level security;
drop policy if exists "누구나 기록" on public.page_events;
create policy "누구나 기록" on public.page_events for insert to anon, authenticated with check (true);
revoke all on public.page_events from anon, authenticated;
grant insert (visitor, session, type, path, name, ref, device) on public.page_events to anon, authenticated;

-- 관리자용 집계 (기간: 최근 N일, 한국 시간 기준)
create or replace function public.admin_stats(days int default 30) returns jsonb
language plpgsql stable security definer set search_path = '' as $$
declare since timestamptz := date_trunc('day', now() at time zone 'Asia/Seoul') at time zone 'Asia/Seoul' - make_interval(days => greatest(days, 1) - 1);
begin
  if not public.is_admin() then raise exception 'not allowed'; end if;
  return (
    with e as (select * from public.page_events where at >= since),
    v as (select * from e where type = 'view')
    select jsonb_build_object(
      'visitors', (select count(distinct visitor) from v),
      'sessions', (select count(distinct session) from v),
      'views', (select count(*) from v),
      'new_visitors', (select count(*) from (select visitor from public.page_events where type = 'view' group by visitor having min(at) >= since) x),
      'daily', coalesce((select jsonb_agg(jsonb_build_object('d', d, 'visitors', u, 'views', n) order by d) from (
          select to_char(at at time zone 'Asia/Seoul', 'YYYY-MM-DD') d, count(distinct visitor) u, count(*) n from v group by 1) x), '[]'),
      'pages', coalesce((select jsonb_agg(jsonb_build_object('k', path, 'views', n, 'visitors', u) order by n desc) from (
          select path, count(*) n, count(distinct visitor) u from v group by path order by 2 desc limit 15) x), '[]'),
      'refs', coalesce((select jsonb_agg(jsonb_build_object('k', r, 'sessions', n) order by n desc) from (
          select coalesce(nullif(ref, ''), '직접 방문') r, count(distinct session) n from v group by 1 order by 2 desc limit 12) x), '[]'),
      'devices', coalesce((select jsonb_agg(jsonb_build_object('k', device, 'visitors', n) order by n desc) from (
          select coalesce(device, 'desktop') device, count(distinct visitor) n from v group by 1) x), '[]'),
      'actions', coalesce((select jsonb_agg(jsonb_build_object('k', name, 'count', n, 'visitors', u) order by n desc) from (
          select name, count(*) n, count(distinct visitor) u from e where type = 'action' group by name order by 2 desc limit 20) x), '[]'),
      'hours', coalesce((select jsonb_agg(jsonb_build_object('h', h, 'views', n) order by h) from (
          select extract(hour from at at time zone 'Asia/Seoul')::int h, count(*) n from v group by 1) x), '[]')
    )
  );
end $$;
revoke all on function public.admin_stats(int) from public, anon;
grant execute on function public.admin_stats(int) to authenticated;

-- 13개월 지난 기록 정리 (관리자 페이지에서 통계를 열 때 함께 실행)
create or replace function public.admin_purge_events() returns int
language plpgsql security definer set search_path = '' as $$
declare n int;
begin
  if not public.is_admin() then raise exception 'not allowed'; end if;
  delete from public.page_events where at < now() - interval '13 months';
  get diagnostics n = row_count;
  return n;
end $$;
revoke all on function public.admin_purge_events() from public, anon;
grant execute on function public.admin_purge_events() to authenticated;
