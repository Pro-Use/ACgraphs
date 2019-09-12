import sqlite3
from datetime import datetime

u_con = sqlite3.connect('../db/graphs_db.db')
u_cursor = u_con.cursor()
u_cursor.execute('''SELECT id FROM prices''')

ids = u_cursor.fetchall()

for id in ids:
    print("id = %s" % id[0])
    u_cursor.execute('''SELECT date, hour, minute FROM twitter WHERE id = ?''', [id[0]] )
    date = u_cursor.fetchall()
    date = date[0]
    date_str = "%s %02d:%02d" % (date[0], int(date[1]), int(date[2]))
    print(date_str)
    date_obj = datetime.strptime(date_str, "%d/%m/%Y %H:%M")
    print (date_obj.timestamp())
    u_cursor.execute('''UPDATE prices SET date_time = ? WHERE id = ?''', [date_obj.timestamp(), id[0]])
    u_con.commit()
