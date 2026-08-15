create sequence if not exists textshop_order_seq start 1000;

create table if not exists textshop_orders (
  order_id        text primary key default 'TS-' || nextval('textshop_order_seq')::text,
  customer_phone  text not null,
  package_name    text,
  order_details   text,
  status          text default 'new',
  amount_cents    int  default 0,
  revision_count  int  default 0,
  delivery_eta    date,
  deck_url        text,
  created_at      timestamptz default now()
);

create index if not exists idx_orders_phone
  on textshop_orders (customer_phone, created_at desc);

create table if not exists textshop_support_tickets (
  ticket_id        bigserial primary key,
  customer_phone   text not null,
  order_id         text,
  issue_type       text,
  customer_message text,
  status           text default 'open',
  created_at       timestamptz default now()
);

create table if not exists textshop_budget (
  id                serial primary key,
  daily_cap_cents   int not null,
  per_txn_cap_cents int not null
);

insert into textshop_budget (daily_cap_cents, per_txn_cap_cents)
  select 50000, 5000
  where not exists (select 1 from textshop_budget);

create table if not exists textshop_spend_log (
  spend_id       bigserial primary key,
  customer_phone text,
  order_id       text,
  purpose        text,
  amount_cents   int not null,
  justification  text,
  created_at     timestamptz default now()
);

create index if not exists idx_spend_date
  on textshop_spend_log (created_at);

create table if not exists textshop_message_log (
  id                  bigserial primary key,
  customer_phone      text not null,
  direction           text not null,
  message_text        text,
  provider_message_id text,
  status              text,
  error_text          text,
  created_at          timestamptz default now()
);

create table if not exists textshop_agent_runs (
  id              bigserial primary key,
  customer_phone  text,
  inbound_message text,
  agent_output    text,
  execution_id    text,
  status          text,
  created_at      timestamptz default now()
);

create table if not exists textshop_error_log (
  id             bigserial primary key,
  source         text,
  detail         text,
  customer_phone text,
  execution_id   text,
  created_at     timestamptz default now()
);

create table if not exists textshop_product_reviews (
  review_id    bigserial primary key,
  product_idea text,
  verdict      text,
  confidence   numeric,
  review_json  jsonb,
  created_at   timestamptz default now()
);

create table if not exists textshop_decisions (
  decision_id    bigserial primary key,
  actor          text,
  room_id        text,
  decision_type  text,
  proposal       text,
  verdict        text,
  evidence       text,
  customer_phone text,
  order_id       text,
  created_at     timestamptz default now()
);

insert into textshop_orders
  (customer_phone, package_name, order_details, status, amount_cents,
   revision_count, delivery_eta, deck_url)
select
  '+15551234567',
  'Seed Deck',
  '12-slide seed deck for a B2B SaaS',
  'delivered',
  49900,
  2,
  current_date - 3,
  'https://example.com/deck.pdf'
where not exists (
  select 1 from textshop_orders where customer_phone = '+15551234567'
);
