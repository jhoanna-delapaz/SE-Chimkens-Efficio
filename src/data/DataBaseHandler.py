
import sqlite3
from sqlite3 import Error

def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)

    return conn

def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)

def init_db(db_file):
    database = db_file

    sql_create_tasks_table = """ CREATE TABLE IF NOT EXISTS tasks (
                                        id integer PRIMARY KEY,
                                        title text NOT NULL,
                                        description text,
                                        status text NOT NULL,
                                        created_at text NOT NULL,
                                        due_date text,
                                        priority text
                                    ); """

    sql_create_user_profile_table = """ CREATE TABLE IF NOT EXISTS user_profile (
                                        id integer PRIMARY KEY,
                                        name text NOT NULL,
                                        email text
                                    ); """

    # create a database connection
    conn = create_connection(database)

    # create tables
    if conn is not None:
        create_table(conn, sql_create_tasks_table)
        create_table(conn, sql_create_user_profile_table)
        print("Database initialized successfully.")
    else:
        print("Error! cannot create the database connection.")
