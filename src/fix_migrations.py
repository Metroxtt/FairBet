import psycopg
conn = psycopg.connect('postgres://fairbet_user:fairbet_secure_password@db:5432/fairbet_db')
conn.autocommit = True
cur = conn.cursor()
cur.execute("DELETE FROM django_migrations WHERE app = 'admin';")
cur.execute("DELETE FROM django_migrations WHERE app = 'auth';")
cur.execute("DELETE FROM django_migrations WHERE app = 'contenttypes';")
cur.execute("DELETE FROM django_migrations WHERE app = 'sessions';")
print('Deleted all migration records')
cur.close()
conn.close()
