create table if not exists jobs (
    id text primary key,
    thread_id text not null,
    state text not null,
    data jsonb not null,
    created_at double precision not null,
    updated_at double precision not null
);

create table if not exists outcomes (
    id bigserial primary key,
    job_id text not null references jobs(id) on delete cascade,
    price_cents integer not null,
    accepted integer not null,
    build_seconds double precision,
    verify_cost_cents integer,
    created_at double precision not null
);

create table if not exists ledger (
    id bigserial primary key,
    job_id text references jobs(id) on delete set null,
    kind text not null,
    amount_cents integer not null,
    note text,
    created_at double precision not null
);

create table if not exists decisions (
    id bigserial primary key,
    job_id text references jobs(id) on delete set null,
    kind text not null,
    summary text not null,
    detail text,
    created_at double precision not null
);

create index if not exists idx_jobs_thread on jobs(thread_id);
create index if not exists idx_jobs_state on jobs(state);
create index if not exists idx_jobs_updated on jobs(updated_at desc);
create index if not exists idx_ledger_job_kind on ledger(job_id, kind);
create index if not exists idx_ledger_created on ledger(created_at desc);
create index if not exists idx_decisions_created on decisions(created_at desc);
