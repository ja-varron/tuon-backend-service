CREATE ROLE tuon_auth_service
    LOGIN
    PASSWORD '8rmvmEO7FST39XQA'
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE
    NOREPLICATION
    NOINHERIT;

GRANT USAGE ON SCHEMA tuon_auth TO tuon_auth_service;

GRANT SELECT, INSERT, UPDATE, DELETE ON tuon_auth.users, tuon_auth.otp_flows, tuon_auth.refresh_tokens TO tuon_auth_service;