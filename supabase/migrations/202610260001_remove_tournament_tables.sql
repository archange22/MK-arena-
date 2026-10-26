-- Remove tournament tables from the dedicated MK Arena project.
-- The tables were verified empty before removal.
drop table if exists public.mk_tournament_registrations;
drop table if exists public.mk_tournament_config;
drop table if exists public.mk_tournaments;
