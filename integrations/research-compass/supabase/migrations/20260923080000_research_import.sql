-- Research Compass: private staging for MykoKnoks research-bank imports.
-- Everything here is reviewer-only. Nothing is readable by anonymous visitors,
-- and nothing is published until a reviewer approves it and a separate public
-- view is created (see "Publishing" at the end).

-- Reviewers are the project's existing editors and administrators
-- (public.user_roles / public.has_role from the base migration).
create or replace function public.is_research_reviewer()
returns boolean language sql stable security definer set search_path = public as $$
  select public.has_role(auth.uid(), 'editor') or public.has_role(auth.uid(), 'administrator');
$$;

create table if not exists public.research_import_batches (
  id uuid primary key default gen_random_uuid(),
  source_repo text not null,
  commit_sha text not null check (commit_sha ~ '^[0-9a-f]{40}$'),
  file_path text not null,
  payload_sha256 text not null check (payload_sha256 ~ '^[0-9a-f]{64}$'),
  dataset_id text,
  dataset_version text,
  dataset_as_of date,
  retrieved_at timestamptz not null,
  status text not null check (status in ('awaiting_review', 'reviewed', 'rejected', 'failed')),
  row_count integer not null default 0,
  errors jsonb,
  raw_payload jsonb,
  program_slug text not null default 'mykoknoks',
  imported_by uuid references auth.users (id),
  created_at timestamptz not null default now(),
  unique (commit_sha, file_path)
);

create table if not exists public.research_taxon_proposals (
  id uuid primary key default gen_random_uuid(),
  batch_id uuid not null references public.research_import_batches (id) on delete cascade,
  scientific_name text not null,
  taxonomic_status text not null,
  norway_evidence_status text not null,
  evidence_grade text not null,
  original jsonb not null,                -- the row exactly as the seed had it
  changed_since_last_review boolean,      -- null when never reviewed before
  review_state text not null default 'proposed'
    check (review_state in ('proposed', 'approved', 'rejected')),
  review_note text,
  reviewed_by uuid references auth.users (id),
  reviewed_at timestamptz,
  published boolean not null default false,
  created_at timestamptz not null default now(),
  unique (batch_id, scientific_name),
  -- a row can only be published after approval
  check (not published or review_state = 'approved')
);

-- The original values are an audit record: they can never be edited.
create or replace function public.research_proposals_guard()
returns trigger language plpgsql as $$
begin
  if new.original is distinct from old.original
     or new.scientific_name is distinct from old.scientific_name
     or new.batch_id is distinct from old.batch_id then
    raise exception 'Imported values are read-only; import a new batch instead';
  end if;
  if old.review_state <> 'proposed' and new.review_state = 'proposed' then
    raise exception 'A reviewed row cannot be reset to proposed';
  end if;
  if new.review_state <> old.review_state then
    new.reviewed_by := auth.uid();
    new.reviewed_at := now();
  end if;
  return new;
end $$;

drop trigger if exists research_proposals_guard on public.research_taxon_proposals;
create trigger research_proposals_guard before update on public.research_taxon_proposals
  for each row execute function public.research_proposals_guard();

alter table public.research_import_batches enable row level security;
alter table public.research_taxon_proposals enable row level security;

-- Reviewers read everything and review proposals. Inserts come only from the
-- edge function (service role), which bypasses RLS.
create policy "reviewers read batches" on public.research_import_batches
  for select to authenticated using (public.is_research_reviewer());
create policy "reviewers read proposals" on public.research_taxon_proposals
  for select to authenticated using (public.is_research_reviewer());
create policy "reviewers review proposals" on public.research_taxon_proposals
  for update to authenticated using (public.is_research_reviewer()) with check (public.is_research_reviewer());

create index if not exists research_proposals_batch_idx on public.research_taxon_proposals (batch_id);
create index if not exists research_proposals_name_idx on public.research_taxon_proposals (scientific_name, reviewed_at desc);

-- Publishing: deliberately not created here. When Jarle decides to publish,
-- add a view over approved + published rows that exposes only public fields
-- (never raw_payload, reviewer ids, or any locality), and grant select on that
-- view to anon.

-- Access: any user with the editor or administrator role in public.user_roles
-- can import and review. No extra setup is needed.
