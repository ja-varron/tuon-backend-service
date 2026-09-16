# Row-level security deployment

Run [`sql/enable_rls.sql`](../sql/enable_rls.sql) as the database owner after the schema and `refresh_tokens` migration. It enables and forces RLS on the five currently deployed tables: `users`, `profiles`, `institutions`, `otp_flows`, and `refresh_tokens`.

The migration creates two non-login roles. Enable login only after assigning strong, distinct generated passwords:

```sql
ALTER ROLE tuon_api LOGIN PASSWORD '<generated-api-password>';
ALTER ROLE tuon_auth_service LOGIN PASSWORD '<generated-auth-service-password>';
```

Set the following server-only environment variables and restart the API:

```env
DATABASE_URL=postgresql://tuon_api:<generated-api-password>@<host>/<database>
AUTH_DATABASE_URL=postgresql://tuon_auth_service:<generated-auth-service-password>@<host>/<database>
```

`DATABASE_URL` is the restricted application role. On every authenticated request, the API validates the JWT before storing only its `sub` in a transaction-local PostgreSQL setting. RLS resolves the role and institution from `profiles`, so stale or forged JWT role and institution claims never grant database access. The setting is recreated after every commit and cleared when the session finishes.

`AUTH_DATABASE_URL` is used exclusively by signup, OTP verification, sign-in, and refresh-token rotation. It must be available only to the deployed backend. It needs broader access because those flows happen before the caller has an authenticated identity; do not use it for normal authenticated endpoints.

The policy boundaries are:

- API users can read their own non-secret user fields, own profile and institution, and refresh tokens belonging to themselves.
- Admins can read and create instructor/student profiles only within their own institution. Profile email must match the corresponding user.
- Neither `tuon_api` nor direct clients can read password hashes or OTP hashes, create refresh tokens, change a profile's role/institution/email, or access OTP flows.
- RLS is forced even for table owners. Superusers and roles with `BYPASSRLS` remain able to bypass PostgreSQL RLS, so neither application role may receive either attribute.

Use separate database credentials and keep database access private to the backend. A client holding an application database password can impersonate the application; RLS cannot make compromised database credentials safe.

## Smoke test

Connect separately as each role. The API role must set a transaction-local test identity before querying:

```sql
BEGIN;
SELECT set_config('app.user_id', '<real-user-uuid>', true);
SELECT user_id, email FROM public.users;
SELECT * FROM public.refresh_tokens;
COMMIT;
```

The results must contain only rows owned by that UUID. Repeat with another institution's admin: profile rows from the other institution must be invisible. Connecting as `tuon_api` without setting `app.user_id` should return no rows. Connecting as `tuon_auth_service` is reserved for backend auth-flow verification.
