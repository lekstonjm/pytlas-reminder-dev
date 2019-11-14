import sqlite3
from datetime import datetime

if __name__== "__main__":
    date_format = "%Y-%m-%d"
    time_format = "%H:%M:%S"
    datetime_format = "{0} {1}".format(date_format, time_format)
    reminder_db_path = "../pytlas_reminder.sqlite"
    db_connection = sqlite3.connect(reminder_db_path)
    cur = db_connection.cursor()
    sql_command = """
    SELECT object from reminder WHERE next_occurence <= ?
    """    
    sql_parameters = (datetime.now().strftime(datetime_format),)
    cur.execute(sql_command, sql_parameters)
    occurences = cur.fetchall()
    print(occurences)