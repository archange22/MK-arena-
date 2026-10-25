-- Allow the bot's existing UI vocabulary ("finished") while retaining "completed".
-- Run only in the dedicated MK Arena Supabase project.
alter table public.mk_tournaments drop constraint if exists mk_tournaments_status_check;
alter table public.mk_tournaments add constraint mk_tournaments_status_check
  check (status in ('open', 'closed', 'running', 'completed', 'finished', 'cancelled'));
