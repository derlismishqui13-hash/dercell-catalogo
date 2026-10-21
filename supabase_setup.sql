-- Ejecuta este script en Supabase > SQL Editor.
create extension if not exists pgcrypto;

create table if not exists public.phones (
  id uuid primary key default gen_random_uuid(),
  brand text not null,
  model text not null,
  price numeric(10,2) not null check (price >= 0),
  condition text default 'Nuevo',
  stock integer not null default 0,
  color text,
  short_description text,
  description text,
  storage text,
  ram text,
  processor text,
  screen text,
  camera text,
  battery text,
  os text,
  connectivity text,
  sim text,
  warranty text,
  photos jsonb not null default '[]'::jsonb,
  active boolean not null default true,
  created_at timestamptz not null default now()
);

alter table public.phones enable row level security;

-- La app usa la clave SERVICE ROLE únicamente en el servidor Streamlit.
-- No añadas la clave service role a frontend ni la publiques en GitHub.

insert into storage.buckets (id, name, public)
values ('phone-photos', 'phone-photos', true)
on conflict (id) do nothing;

-- Las imágenes del bucket son públicas para que los clientes puedan verlas.
-- Las subidas y modificaciones se realizan desde el servidor con service role.
create policy "Public can view DERCELL phone photos"
on storage.objects for select
to anon, authenticated
using (bucket_id = 'phone-photos');

-- No se crean políticas públicas de lectura/escritura para la tabla phones:
-- la app consulta y modifica la tabla desde el servidor usando service role.
