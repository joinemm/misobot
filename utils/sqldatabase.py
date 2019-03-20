import sqlite3
import pandas


def execute(command, variables=None):
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    if variables is None:
        cursor.execute(command)
    else:
        cursor.execute(command, variables)
    connection.commit()
    connection.close()


def query(command):
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    result = pandas.read_sql(command, connection)
    connection.commit()
    connection.close()
    return result
