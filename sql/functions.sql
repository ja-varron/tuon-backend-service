-- current_user_id function
select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid;

-- is_admin function

  select exists (
    select 1
    from public.profiles
    where user_id = public.current_user_id()
      and role = 'admin'
  );
