import sqlite3
from collections import defaultdict
from datetime import datetime

if __name__== "__main__":
    date_format = "%Y-%m-%d"
    time_format = "%H:%M:%S"
    datetime_format = "{0} {1}".format(date_format, time_format)
    reminder_db_path = "../pytlas_reminder.sqlite"    
    db_connection = sqlite3.connect(reminder_db_path)
    db_connection.cursor()
    
    sql_command = \
    """
        INSERT INTO reminder 
        (reference_date, reference_time, recurrence_type, object, next_occurence) 
        VALUES 
        (:reference_date, :reference_time, :recurrence_type, :object, :next_occurence)
    """    
    f = lambda:None
    row = defaultdict(f,
    {
        'reference_date':datetime.now().strftime(date_format), 
        'reference_time':datetime.now().strftime(time_format), 
        'recurrence_type':'once', 
        'object':'Super', 
        'next_occurence':datetime.now().strftime(datetime_format)
    })
    sql_parameters = (row)
    db_connection.executemany(sql_command,sql_parameters)
    db_connection.commit()

    sql_command = \
    """
        SELECT object from reminder WHERE next_occurence <= ?
    """        
    sql_parameters = (datetime.now().strftime(datetime_format),)
    cur = db_connection.cursor()
    cur.execute(sql_command, sql_parameters)
    occurences = cur.fetchall()
    
    db_connection.execute("BEGIN TRANSACTION;")
    sql_commands = [
        "DELETE FROM reminder WHERE recurrence_type = 'once' AND  next_occurence <= ?;",
        "UPDATE reminder set next_occurence  = datetime(next_occurence, '+1 hour') WHERE recurrence_type = 'hour' AND next_occurence <= ?;",
        "UPDATE reminder set next_occurence  = datetime(next_occurence, '+1 day') WHERE recurrence_type = 'day' AND next_occurence <= ?;",
        "UPDATE reminder set next_occurence  = datetime(next_occurence, '+1 week' ) WHERE recurrence_type = 'weekday' AND next_occurence <= ?;",
        "UPDATE reminder set next_occurence  = datetime(next_occurence, '+1 month' ) WHERE recurrence_type = 'month' AND next_occurence <= ?;",
        "UPDATE reminder set next_occurence  = datetime(next_occurence, '+1 year' ) WHERE recurrence_type = 'month' AND next_occurence <= ?;"
    ]    
    for sql_command in sql_commands: db_connection.execute(sql_command, sql_parameters)
    db_connection.execute("END TRANSACTION;")
    db_connection.commit()

    print(occurences)