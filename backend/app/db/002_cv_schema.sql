create extension if not exists vector;

create table public.cvs (
    id uuid primary key default gen_random_uuid(),
    user_id uuid,                          -- auth ke baad foreign key banega
    file_name text not null,
    file_path text,                        -- Supabase Storage mein original PDF ka path
    raw_text text not null,                -- poora extracted text
    skills text[] default '{}',
    experience_years numeric,
    education text[] default '{}',
    job_titles text[] default '{}',
    content_hash text unique,              -- same CV dobara store na ho
    embedding vector(1024),                -- jobs wala hi Voyage model
    created_at timestamptz default now()
);

create index on public.cvs using hnsw (embedding vector_cosine_ops);