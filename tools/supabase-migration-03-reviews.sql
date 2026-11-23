-- 3단계: 아카데미 참가 리뷰 (로그인 없이 작성 → 관리자 승인 후 게시)
-- Supabase → SQL Editor → New query 에 붙여넣고 Run. 여러 번 실행해도 안전합니다.

create table if not exists public.reviews (
  id bigint generated always as identity primary key,
  created_at timestamptz not null default now(),
  academy text not null check (char_length(academy) between 1 and 80),
  year int not null check (year between 2010 and 2100),
  rating int not null check (rating between 1 and 5),
  body text not null check (char_length(body) between 10 and 2000),
  photos text[] not null default '{}' check (cardinality(photos) <= 3),
  name text not null check (char_length(name) between 1 and 30),
  display_name text,
  phone text check (char_length(phone) <= 20),
  user_id uuid references auth.users on delete set null,
  verified boolean not null default false,
  status text not null default '대기' check (status in ('대기', '게시', '숨김')),
  memo text,
  updated_at timestamptz not null default now()
);
create index if not exists reviews_status on public.reviews (status, created_at desc);

-- 이름은 성만 공개(김**). 손님이 넣은 상태·확인 표시·메모는 무시. 스팸 폭주 방지(1시간 대기 리뷰 30건 초과 시 거절)
create or replace function public.reviews_guard() returns trigger
language plpgsql security definer set search_path = '' as $$
declare n text := btrim(new.name);
begin
  new.display_name := left(n, 1) || repeat('*', greatest(char_length(n) - 1, 1));
  if tg_op = 'INSERT' and not public.is_admin() then
    if (select count(*) from public.reviews where status = '대기' and created_at > now() - interval '1 hour') >= 30 then
      raise exception 'too many reviews';
    end if;
    new.user_id := auth.uid(); new.status := '대기'; new.verified := false; new.memo := null; new.created_at := now();
    if exists (select 1 from unnest(new.photos) p
               where p !~ '^https://[a-z0-9]+\.supabase\.co/storage/v1/object/public/reviews/') then
      raise exception 'bad photo url';
    end if;
  end if;
  new.updated_at := now();
  return new;
end $$;
drop trigger if exists reviews_guard on public.reviews;
create trigger reviews_guard before insert or update on public.reviews
  for each row execute function public.reviews_guard();

alter table public.reviews enable row level security;
drop policy if exists "누구나 리뷰 작성" on public.reviews;
create policy "누구나 리뷰 작성" on public.reviews for insert to anon, authenticated with check (true);
drop policy if exists "게시된 리뷰 또는 관리자" on public.reviews;
create policy "게시된 리뷰 또는 관리자" on public.reviews for select to anon, authenticated
  using (status = '게시' or public.is_admin());
drop policy if exists "관리자 수정" on public.reviews;
create policy "관리자 수정" on public.reviews for update to authenticated using (public.is_admin()) with check (public.is_admin());
drop policy if exists "관리자 삭제" on public.reviews;
create policy "관리자 삭제" on public.reviews for delete to authenticated using (public.is_admin());

-- 실명·연락처·메모는 관리자 함수로만 읽기. 일반 손님·회원은 공개 칸만
revoke all on public.reviews from anon, authenticated;
grant insert (academy, year, rating, body, photos, name, phone) on public.reviews to anon, authenticated;
grant select (id, created_at, academy, year, rating, body, photos, display_name, verified, status) on public.reviews to anon, authenticated;
grant delete on public.reviews to authenticated;

create or replace function public.admin_reviews() returns setof public.reviews
language plpgsql stable security definer set search_path = '' as $$
begin
  if not public.is_admin() then raise exception 'not allowed'; end if;
  return query select * from public.reviews order by created_at desc;
end $$;
revoke all on function public.admin_reviews() from public, anon;
grant execute on function public.admin_reviews() to authenticated;

create or replace function public.admin_update_review(rid bigint, new_status text, new_verified boolean, new_memo text)
returns void language plpgsql security definer set search_path = '' as $$
begin
  if not public.is_admin() then raise exception 'not allowed'; end if;
  update public.reviews set status = new_status, verified = new_verified, memo = nullif(btrim(new_memo), '') where id = rid;
end $$;
revoke all on function public.admin_update_review(bigint, text, boolean, text) from public, anon;
grant execute on function public.admin_update_review(bigint, text, boolean, text) to authenticated;

-- 게시 여부 판단용 (손님에게는 항상 false)
grant execute on function public.is_admin() to anon;

-- ───────── 사진 저장소 ─────────
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('reviews', 'reviews', true, 3145728, array['image/jpeg', 'image/png', 'image/webp'])
on conflict (id) do update set public = true, file_size_limit = 3145728,
  allowed_mime_types = array['image/jpeg', 'image/png', 'image/webp'];

drop policy if exists "리뷰 사진 올리기" on storage.objects;
create policy "리뷰 사진 올리기" on storage.objects for insert to anon, authenticated
  with check (bucket_id = 'reviews' and (storage.foldername(name))[1] = 'new');
drop policy if exists "리뷰 사진 관리자 삭제" on storage.objects;
create policy "리뷰 사진 관리자 삭제" on storage.objects for delete to authenticated
  using (bucket_id = 'reviews' and public.is_admin());
