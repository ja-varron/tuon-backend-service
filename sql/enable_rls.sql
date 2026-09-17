-- Tuon Row Level Security migration
--
-- Run this once as the database owner (not as either application role) after
-- sql/tuon-db-schema.sql and sql/add_refresh_tokens_table.sql.
--
-- This migration creates two NOLOGIN roles.  Give each a distinct, strong
-- password and LOGIN capability after the migration, then put their separate
-- connection URLs in DATABASE_URL and AUTH_DATABASE_URL respectively:
--
--   ALTER ROLE tuon_api LOGIN PASSWORD '<generated-secret>';
--   ALTER ROLE tuon_auth_service LOGIN PASSWORD '<generated-secret>';
--
-- `tuon_api` is the normal API role.  It is subject to RLS and receives the
-- verified JWT subject through the transaction-local app.user_id setting.
-- `tuon_auth_service` is for server-side signup, OTP, sign-in, and refresh
-- flows only. Never expose either database URL to a browser or mobile app.

BEGIN;

DO $$
DECLARE
    required_table text;
BEGIN
    FOREACH required_table IN ARRAY ARRAY[
        'users', 'profiles', 'institutions', 'otp_flows', 'refresh_tokens'
    ]
    LOOP
        IF to_regclass('public.' || required_table) IS NULL THEN
            RAISE EXCEPTION 'Required table public.% is missing', required_table;
        END IF;
    END LOOP;

    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'tuon_api') THEN
        CREATE ROLE tuon_api NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'tuon_auth_service') THEN
        CREATE ROLE tuon_auth_service NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION;
    END IF;
END
$$;

-- No browser-facing/default role may access these tables directly.
REVOKE ALL ON TABLE public.users, public.profiles, public.institutions,
    public.otp_flows, public.refresh_tokens FROM PUBLIC;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;

CREATE SCHEMA IF NOT EXISTS app_private;
REVOKE ALL ON SCHEMA app_private FROM PUBLIC;
GRANT USAGE ON SCHEMA public, app_private TO tuon_api, tuon_auth_service;

-- The only identity accepted from a request is the verified JWT subject.  The
-- regex prevents malformed session settings from being converted to UUIDs.
CREATE OR REPLACE FUNCTION app_private.current_user_id()
RETURNS uuid
LANGUAGE plpgsql
STABLE
PARALLEL SAFE
SET search_path = pg_catalog
AS $$
DECLARE
    raw_user_id text := current_setting('app.user_id', true);
BEGIN
    IF raw_user_id IS NULL
       OR raw_user_id !~* '^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$' THEN
        RETURN NULL;
    END IF;

    RETURN raw_user_id::uuid;
END;
$$;

-- These functions are SECURITY DEFINER solely to avoid recursive RLS checks
-- while consulting the current user's authoritative profile.  They expose
-- booleans only, use no dynamic SQL, and pin their search path.
CREATE OR REPLACE FUNCTION app_private.is_current_user_admin()
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
    SELECT EXISTS (
        SELECT 1
        FROM public.profiles AS profile
        WHERE profile.user_id = app_private.current_user_id()
          AND profile.role = 'admin'
    );
$$;

CREATE OR REPLACE FUNCTION app_private.is_admin_for(target_institution_id uuid)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
    SELECT EXISTS (
        SELECT 1
        FROM public.profiles AS profile
        WHERE profile.user_id = app_private.current_user_id()
          AND profile.role = 'admin'
          AND profile.institution_id = target_institution_id
    );
$$;

CREATE OR REPLACE FUNCTION app_private.can_access_institution(target_institution_id uuid)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
    SELECT EXISTS (
        SELECT 1
        FROM public.profiles AS profile
        WHERE profile.user_id = app_private.current_user_id()
          AND profile.institution_id = target_institution_id
    );
$$;

CREATE OR REPLACE FUNCTION app_private.profile_email_matches_user(
    target_user_id uuid,
    target_email text
)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
    SELECT EXISTS (
        SELECT 1
        FROM public.users AS app_user
        WHERE app_user.user_id = target_user_id
          AND app_user.email = target_email
    );
$$;

REVOKE ALL ON FUNCTION app_private.current_user_id() FROM PUBLIC;
REVOKE ALL ON FUNCTION app_private.is_current_user_admin() FROM PUBLIC;
REVOKE ALL ON FUNCTION app_private.is_admin_for(uuid) FROM PUBLIC;
REVOKE ALL ON FUNCTION app_private.can_access_institution(uuid) FROM PUBLIC;
REVOKE ALL ON FUNCTION app_private.profile_email_matches_user(uuid, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION app_private.current_user_id() TO tuon_api;
GRANT EXECUTE ON FUNCTION app_private.is_current_user_admin() TO tuon_api;
GRANT EXECUTE ON FUNCTION app_private.is_admin_for(uuid) TO tuon_api;
GRANT EXECUTE ON FUNCTION app_private.can_access_institution(uuid) TO tuon_api;
GRANT EXECUTE ON FUNCTION app_private.profile_email_matches_user(uuid, text) TO tuon_api;

-- Start from no table privileges, then add the smallest set needed by each
-- role. `tuon_auth_service` is allowed to run only the unauthenticated auth
-- workflow; `tuon_api` cannot read password/OTP hashes or mint refresh tokens.
REVOKE ALL ON TABLE public.users, public.profiles, public.institutions,
    public.otp_flows, public.refresh_tokens FROM tuon_api, tuon_auth_service;

GRANT SELECT, INSERT, UPDATE ON TABLE public.users, public.profiles,
    public.institutions, public.otp_flows, public.refresh_tokens TO tuon_auth_service;

GRANT SELECT (user_id, email, email_created_at) ON TABLE public.users TO tuon_api;
GRANT INSERT (email, encrypted_password, email_created_at) ON TABLE public.users TO tuon_api;
GRANT SELECT, INSERT ON TABLE public.profiles TO tuon_api;
GRANT UPDATE (first_name, middle_name, last_name, examinee_id_number)
    ON TABLE public.profiles TO tuon_api;
GRANT SELECT ON TABLE public.institutions TO tuon_api;
GRANT SELECT ON TABLE public.refresh_tokens TO tuon_api;
GRANT UPDATE (revoked_at) ON TABLE public.refresh_tokens TO tuon_api;

ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.institutions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.otp_flows ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.refresh_tokens ENABLE ROW LEVEL SECURITY;

-- FORCE RLS prevents a table owner from accidentally bypassing these policies.
ALTER TABLE public.users FORCE ROW LEVEL SECURITY;
ALTER TABLE public.profiles FORCE ROW LEVEL SECURITY;
ALTER TABLE public.institutions FORCE ROW LEVEL SECURITY;
ALTER TABLE public.otp_flows FORCE ROW LEVEL SECURITY;
ALTER TABLE public.refresh_tokens FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS auth_service_users ON public.users;
DROP POLICY IF EXISTS api_read_own_user ON public.users;
DROP POLICY IF EXISTS api_admin_create_user ON public.users;
CREATE POLICY auth_service_users ON public.users
    FOR ALL TO tuon_auth_service USING (true) WITH CHECK (true);
CREATE POLICY api_read_own_user ON public.users
    FOR SELECT TO tuon_api
    USING (user_id = app_private.current_user_id());
CREATE POLICY api_admin_create_user ON public.users
    FOR INSERT TO tuon_api
    WITH CHECK (
        app_private.is_current_user_admin()
        AND email_created_at IS NOT NULL
    );

DROP POLICY IF EXISTS auth_service_profiles ON public.profiles;
DROP POLICY IF EXISTS api_read_profiles ON public.profiles;
DROP POLICY IF EXISTS api_admin_create_profile ON public.profiles;
DROP POLICY IF EXISTS api_update_profiles ON public.profiles;
CREATE POLICY auth_service_profiles ON public.profiles
    FOR ALL TO tuon_auth_service USING (true) WITH CHECK (true);
CREATE POLICY api_read_profiles ON public.profiles
    FOR SELECT TO tuon_api
    USING (
        user_id = app_private.current_user_id()
        OR app_private.is_admin_for(institution_id)
    );
CREATE POLICY api_admin_create_profile ON public.profiles
    FOR INSERT TO tuon_api
    WITH CHECK (
        app_private.is_admin_for(institution_id)
        AND role IN ('instructor', 'student')
        AND app_private.profile_email_matches_user(user_id, email)
    );
CREATE POLICY api_update_profiles ON public.profiles
    FOR UPDATE TO tuon_api
    USING (
        user_id = app_private.current_user_id()
        OR app_private.is_admin_for(institution_id)
    )
    WITH CHECK (
        user_id = app_private.current_user_id()
        OR app_private.is_admin_for(institution_id)
    );

DROP POLICY IF EXISTS auth_service_institutions ON public.institutions;
DROP POLICY IF EXISTS api_read_own_institution ON public.institutions;
CREATE POLICY auth_service_institutions ON public.institutions
    FOR ALL TO tuon_auth_service USING (true) WITH CHECK (true);
CREATE POLICY api_read_own_institution ON public.institutions
    FOR SELECT TO tuon_api
    USING (app_private.can_access_institution(institution_id));

DROP POLICY IF EXISTS auth_service_otp_flows ON public.otp_flows;
CREATE POLICY auth_service_otp_flows ON public.otp_flows
    FOR ALL TO tuon_auth_service USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS auth_service_refresh_tokens ON public.refresh_tokens;
DROP POLICY IF EXISTS api_read_own_refresh_tokens ON public.refresh_tokens;
DROP POLICY IF EXISTS api_revoke_own_refresh_tokens ON public.refresh_tokens;
CREATE POLICY auth_service_refresh_tokens ON public.refresh_tokens
    FOR ALL TO tuon_auth_service USING (true) WITH CHECK (true);
CREATE POLICY api_read_own_refresh_tokens ON public.refresh_tokens
    FOR SELECT TO tuon_api
    USING (user_id = app_private.current_user_id());
CREATE POLICY api_revoke_own_refresh_tokens ON public.refresh_tokens
    FOR UPDATE TO tuon_api
    USING (user_id = app_private.current_user_id())
    WITH CHECK (user_id = app_private.current_user_id());

COMMIT;
