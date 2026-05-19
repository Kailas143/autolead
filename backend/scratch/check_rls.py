import psycopg

url = "postgresql://postgres.vjtkemnhhjvedyyfwdbx:aurvyz%402026@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres"

with psycopg.connect(url) as conn:
    with conn.cursor() as cur:
        # Check current tables
        cur.execute("""
            SELECT relname, relrowsecurity 
            FROM pg_class 
            WHERE relnamespace = 'public'::regnamespace AND relkind = 'r';
        """)
        tables = cur.fetchall()
        print("Tables in public schema:")
        for table in tables:
            print(f"- {table[0]}: RLS Enabled={table[1]}")
