-- 2단계: 직접 신청(전화 등으로 받아 구글 시트에 적은 명단)을 관리자 페이지에 합치기
-- Supabase → SQL Editor → New query 에 붙여넣고 Run. 여러 번 실행해도 안전합니다.

alter table public.academy_applications add column if not exists source text not null default 'web';
alter table public.academy_applications add column if not exists group_label text;
alter table public.academy_applications add column if not exists sheet_row int;

alter table public.academy_applications drop constraint if exists academy_applications_source_check;
alter table public.academy_applications add constraint academy_applications_source_check
  check (source in ('web', 'direct'));

-- 직접 신청은 시트에 번호가 비어 있을 수 있으므로 형식 검사는 홈페이지 신청에만 적용
alter table public.academy_applications drop constraint if exists academy_applications_phone_check;
alter table public.academy_applications alter column phone drop not null;
alter table public.academy_applications add constraint academy_applications_phone_check
  check (source = 'direct' or (phone is not null and phone ~ '^01[016789]-[0-9]{3,4}-[0-9]{4}$'));

create index if not exists academy_applications_source on public.academy_applications (source);

-- 손님이 넣는 신청은 항상 '홈페이지(web)'. 시트 동기화(서버 비밀 키)와 관리자만 그 밖의 값을 넣을 수 있음
create or replace function public.applications_guard() returns trigger
language plpgsql security definer set search_path = '' as $$
declare trusted boolean := public.is_admin() or coalesce(auth.role(), '') = 'service_role';
begin
  if tg_op = 'INSERT' then
    if not trusted then
      new.user_id := auth.uid();
      new.source := 'web'; new.group_label := null; new.sheet_row := null;
      new.status := '신청접수'; new.paid_amount := 0; new.paid_at := null; new.memo := null;
    end if;
    new.created_at := coalesce(case when trusted then new.created_at end, now());
  end if;
  new.updated_at := now();
  return new;
end $$;

-- 구글 시트 명단으로 '직접 신청' 전체를 한 번에 교체 (서버 비밀 키로만 실행 가능, 실패하면 아무것도 바뀌지 않음)
create or replace function public.replace_direct(rows jsonb) returns int
language plpgsql security definer set search_path = '' as $$
declare n int;
begin
  if coalesce(auth.role(), '') <> 'service_role' then raise exception 'not allowed'; end if;
  delete from public.academy_applications where source = 'direct';
  insert into public.academy_applications
    (source, place, product, session_no, period, pro, people, single_rooms, total_won, name, phone,
     group_label, sheet_row, status, paid_amount, paid_at, request, memo)
  select 'direct', r.place, r.product, r.session_no, r.period, r.pro, 1, r.single_rooms, r.total_won, r.name, r.phone,
         r.group_label, r.sheet_row, r.status, coalesce(r.paid_amount, 0), r.paid_at, r.request, r.memo
  from jsonb_to_recordset(rows) as r(place text, product text, session_no int, period text, pro text, single_rooms int,
       total_won int, name text, phone text, group_label text, sheet_row int, status text, paid_amount int,
       paid_at date, request text, memo text);
  get diagnostics n = row_count;
  return n;
end $$;
revoke all on function public.replace_direct(jsonb) from public, anon, authenticated;
grant execute on function public.replace_direct(jsonb) to service_role;
