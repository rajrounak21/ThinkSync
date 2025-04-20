import pymysql

def get_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="Rou@12345",
        database="Chatbot",
        cursorclass=pymysql.cursors.DictCursor  # Enables dictionary-like results
    )
