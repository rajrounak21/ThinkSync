import pymysql

def get_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="enter you password",
        database="Chatbot",
        cursorclass=pymysql.cursors.DictCursor  # Enables dictionary-like results
    )
