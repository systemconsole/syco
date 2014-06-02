import gzip, zlib, MySQLdb


db = MySQLdb.connect(host="localhost", # your host, usually localhost
                     user="test", # your username
                      passwd="test", # your password
                      db="test") # name of the data base

cur = db.cursor()

# Use all the SQL you like
cur.execute("SELECT log_data FROM LOG_LOGS where log_category = 'RSP' limit 1000")


f=open('/root/data_dump.sql','w')

for row in cur.fetchall() :
  ba = bytearray(row[0])
  entry = zlib.decompress(bytes(ba), 15+32)
  f.write(entry)
  f.write('\n')

f.close()
