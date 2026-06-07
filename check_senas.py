import sqlite3
conn = sqlite3.connect("data/traductor_lsc.db")
cur = conn.cursor()
cur.execute("SELECT nombre, sinonimos FROM senas WHERE nombre IN ('hola','saludos')")
for r in cur.fetchall():
    print(r)
conn.close()
