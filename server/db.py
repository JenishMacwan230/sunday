import sqlite3

con = sqlite3.connect('sunday.db')


cursor = con.cursor()


# query = "CREATE TABLE IF NOT EXISTS sys_command(id integer primary key, name VARCHAR(100), path VARCHAR(1000))" 

# cursor.execute(query)



# to insert values
# query = "INSERT INTO sys_command VALUES (null,'D drive ', 'D:\\')"
# cursor.execute(query)
# con.commit()
# con.close()  # Don't forget to close the connection when done


# query = "CREATE TABLE IF NOT EXISTS web_command(id integer primary key, name VARCHAR(100), url VARCHAR(1000))"
# cursor.execute(query)


# to insert values
query = "INSERT INTO web_command VALUES (null,'Gemini', 'https://gemini.google.com')"
cursor.execute(query)
con.commit()
con.close()  # Don't forget to close the connection when done