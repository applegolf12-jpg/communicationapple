-- 커뮤니케이션 애플 · Supabase 스키마
-- Supabase 대시보드 → SQL Editor → New query 에 전체를 붙여넣고 Run.
-- 여러 번 실행해도 안전하게 작성되어 있습니다.

-- ───────── 회원 프로필 ─────────
create table if not exists public.profiles (
  id uuid primary key references auth.users on delete cascade,
  email text,
  name text check (char_length(name) <= 50),
  phone text check (char_length(phone) <= 20),
  marketing_sms boolean not null default false,
  marketing_agreed_at timestamptz,
  role text not null default 'member' check (role in ('member', 'admin')),
  created_at timestamptz not null default now()
);

create or replace function public.is_admin() returns boolean
language sql stable security definer set search_path = '' as $$
  select exists (select 1 from public.profiles where id = auth.uid() and role = 'admin');
$$;

-- 가입 시 프로필 자동 생성
create or replace function public.handle_new_user() returns trigger
language plpgsql security definer set search_path = '' as $$
declare m boolean := coalesce((new.raw_user_meta_data->>'marketing_sms')::boolean, false);
begin
  insert into public.profiles (id, email, name, phone, marketing_sms, marketing_agreed_at)
  values (new.id, new.email,
          left(new.raw_user_meta_data->>'name', 50),
          left(new.raw_user_meta_data->>'phone', 20),
          m, case when m then now() end)
  on conflict (id) do nothing;
  return new;
end $$;
drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created after insert on auth.users
  for each row execute function public.handle_new_user();

-- 일반 회원은 자기 등급(role)을 바꿀 수 없음. 마케팅 동의 시각 기록
create or replace function public.profiles_guard() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  if new.role is distinct from old.role and auth.uid() is not null and not public.is_admin() then
    raise exception 'role change not allowed';
  end if;
  new.id := old.id; new.email := old.email; new.created_at := old.created_at;
  if new.marketing_sms and not old.marketing_sms then new.marketing_agreed_at := now(); end if;
  if not new.marketing_sms then new.marketing_agreed_at := null; end if;
  return new;
end $$;
drop trigger if exists profiles_guard on public.profiles;
create trigger profiles_guard before update on public.profiles
  for each row execute function public.profiles_guard();

-- ───────── 아카데미 신청 ─────────
create table if not exists public.academy_applications (
  id bigint generated always as identity primary key,
  created_at timestamptz not null default now(),
  user_id uuid references auth.users on delete set null,
  place text not null check (place in ('칸차나부리', '아마타')),
  product text check (char_length(product) <= 100),
  session_no int not null check (session_no between 1 and 50),
  period text check (char_length(period) <= 60),
  pro text check (char_length(pro) <= 30),
  people int not null check (people between 1 and 20),
  single_rooms int not null default 0 check (single_rooms between 0 and 20),
  mates text check (char_length(mates) <= 300),
  total_won int check (total_won >= 0),
  breakdown text check (char_length(breakdown) <= 500),
  request text check (char_length(request) <= 2000),
  name text not null check (char_length(name) between 1 and 50),
  phone text not null check (phone ~ '^01[016789]-[0-9]{3,4}-[0-9]{4}$'),
  status text not null default '신청접수'
    check (status in ('신청접수', '결제안내', '입금확인', '예약확정', '취소')),
  paid_amount int not null default 0 check (paid_amount >= 0),
  paid_at date,
  memo text,
  updated_at timestamptz not null default now()
);
create index if not exists academy_applications_session on public.academy_applications (place, session_no);
create index if not exists academy_applications_user on public.academy_applications (user_id);

-- 손님이 넣는 신청은 상태·입금·메모를 건드릴 수 없고, 회원 ID는 로그인 정보로만 기록
create or replace function public.applications_guard() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  if tg_op = 'INSERT' then
    if not public.is_admin() then
      new.user_id := auth.uid();
      new.status := '신청접수'; new.paid_amount := 0; new.paid_at := null; new.memo := null;
    end if;
    new.created_at := now();
  end if;
  new.updated_at := now();
  return new;
end $$;
drop trigger if exists applications_guard on public.academy_applications;
create trigger applications_guard before insert or update on public.academy_applications
  for each row execute function public.applications_guard();

-- ───────── 행사 문의 ─────────
create table if not exists public.inquiries (
  id bigint generated always as identity primary key,
  created_at timestamptz not null default now(),
  name text not null check (char_length(name) between 1 and 50),
  company text check (char_length(company) <= 100),
  phone text not null check (char_length(phone) <= 20),
  email text check (char_length(email) <= 120),
  type text check (char_length(type) <= 50),
  size text check (char_length(size) <= 50),
  event_date text check (char_length(event_date) <= 50),
  message text check (char_length(message) <= 4000),
  status text not null default '신규' check (status in ('신규', '연락완료', '견적진행', '계약', '종료')),
  memo text,
  updated_at timestamptz not null default now()
);
create or replace function public.inquiries_guard() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  if tg_op = 'INSERT' and not public.is_admin() then new.status := '신규'; new.memo := null; end if;
  new.updated_at := now();
  return new;
end $$;
drop trigger if exists inquiries_guard on public.inquiries;
create trigger inquiries_guard before insert or update on public.inquiries
  for each row execute function public.inquiries_guard();

-- ───────── 접근 규칙 (RLS) ─────────
alter table public.profiles enable row level security;
alter table public.academy_applications enable row level security;
alter table public.inquiries enable row level security;

drop policy if exists "본인 또는 관리자 조회" on public.profiles;
create policy "본인 또는 관리자 조회" on public.profiles for select to authenticated
  using (id = auth.uid() or public.is_admin());
drop policy if exists "본인 또는 관리자 수정" on public.profiles;
create policy "본인 또는 관리자 수정" on public.profiles for update to authenticated
  using (id = auth.uid() or public.is_admin()) with check (id = auth.uid() or public.is_admin());

drop policy if exists "누구나 신청" on public.academy_applications;
create policy "누구나 신청" on public.academy_applications for insert to anon, authenticated with check (true);
drop policy if exists "본인 신청 또는 관리자 조회" on public.academy_applications;
create policy "본인 신청 또는 관리자 조회" on public.academy_applications for select to authenticated
  using (user_id = auth.uid() or public.is_admin());
drop policy if exists "관리자 수정" on public.academy_applications;
create policy "관리자 수정" on public.academy_applications for update to authenticated
  using (public.is_admin()) with check (public.is_admin());
drop policy if exists "관리자 삭제" on public.academy_applications;
create policy "관리자 삭제" on public.academy_applications for delete to authenticated using (public.is_admin());

drop policy if exists "누구나 문의" on public.inquiries;
create policy "누구나 문의" on public.inquiries for insert to anon, authenticated with check (true);
drop policy if exists "관리자 조회" on public.inquiries;
create policy "관리자 조회" on public.inquiries for select to authenticated using (public.is_admin());
drop policy if exists "관리자 수정" on public.inquiries;
create policy "관리자 수정" on public.inquiries for update to authenticated using (public.is_admin()) with check (public.is_admin());
drop policy if exists "관리자 삭제" on public.inquiries;
create policy "관리자 삭제" on public.inquiries for delete to authenticated using (public.is_admin());

grant select, update on public.profiles to authenticated;
grant insert on public.academy_applications, public.inquiries to anon;
grant select, insert, update, delete on public.academy_applications, public.inquiries to authenticated;

-- ───────── 회원 탈퇴 (본인만) ─────────
create or replace function public.delete_me() returns void
language plpgsql security definer set search_path = '' as $$
begin
  if auth.uid() is null then raise exception 'not signed in'; end if;
  delete from auth.users where id = auth.uid();
end $$;
revoke all on function public.delete_me() from public, anon;
grant execute on function public.delete_me() to authenticated;

-- ───────── 일시정지 방지용 핑 (구글 Apps Script가 매일 호출) ─────────
create or replace function public.ping() returns int language sql stable as $$ select 1 $$;
grant execute on function public.ping() to anon, authenticated;

revoke all on function public.is_admin() from public, anon;
grant execute on function public.is_admin() to authenticated;
