import psycopg

url = "postgresql://postgres.vjtkemnhhjvedyyfwdbx:aurvyz%402026@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres"

tables = ['ai_usage', 'campaigns', 'emails', 'leads', 'replies', 'sequences', 'system_logs', 'users']

with psycopg.connect(url) as conn:
    with conn.cursor() as cur:
        for table in tables:
            cur.execute(f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY;")
            print(f"Enabled RLS for public.{table}")
    conn.commit()
