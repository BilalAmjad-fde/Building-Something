CREATE TABLE public.jobs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    adzuna_id text unique,
    title text,
    company text,
    location text,
    description text,
    content_hash text,
    salary_range numrange,
    posting_date date,
    "type" text CHECK ("type" IN ('remote', 'onsite')),
    redirect_url text,
    embedding vector
);
