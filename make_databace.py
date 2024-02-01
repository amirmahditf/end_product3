import sqlite3
from prettytable import PrettyTable
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('users.db')
cursor = conn.cursor()

cursor.execute('SELECT * FROM users')
rows = cursor.fetchall()
table = PrettyTable()
table.field_names = ['ID', 'Username', 'First Name',
                     'Last Name', 'Email', 'Phone Number', 'Password Hash']

for row in rows:
    table.add_row(row)

print(table)

conn.close()
