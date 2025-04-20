from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from db_connection import get_connection
from werkzeug.security import generate_password_hash, check_password_hash
import google.generativeai as genai
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv() 
app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Replace with real key

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.0-flash-thinking-exp-01-21')


@app.route("/chatbot")
def chatbot():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Get chat sessions
        cursor.execute("""
            SELECT cs.id, cs.title, MAX(m.created_at) AS last_activity
            FROM chat_sessions cs
            LEFT JOIN messages m ON cs.id = m.session_id
            WHERE cs.user_id = %s
            GROUP BY cs.id
            ORDER BY last_activity DESC
        """, (user_id,))
        sessions = cursor.fetchall()

        # Get messages for current session
        current_session_id = request.args.get('session')
        messages = []
        
        # If no session is selected and no sessions exist, create a new one
        if not current_session_id and not sessions:
            cursor.execute(
                "INSERT INTO chat_sessions (user_id, title) VALUES (%s, 'New Chat')",
                (user_id,)
            )
            conn.commit()
            current_session_id = cursor.lastrowid
            sessions = [{'id': current_session_id, 'title': 'New Chat', 'last_activity': None}]
        
        # If still no session selected but sessions exist, use the most recent one
        if not current_session_id and sessions:
            current_session_id = sessions[0]['id']
            
        if current_session_id:
            cursor.execute("""
                SELECT message_text, sender_type, created_at
                FROM messages
                WHERE session_id = %s
                ORDER BY created_at ASC
            """, (current_session_id,))
            messages = cursor.fetchall()

        return render_template(
            "chatbot.html",
            sessions=sessions,
            current_session=current_session_id,
            messages=messages
        )

    except Exception as e:
        return f"Database error: {str(e)}"
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


@app.route("/api/send_message", methods=["POST"])
def handle_message():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user_id = session["user_id"]
    data = request.get_json()
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Verify session ownership
        cursor.execute("""
            SELECT id FROM chat_sessions
            WHERE id = %s AND user_id = %s
        """, (data['session_id'], user_id))
        if not cursor.fetchone():
            return jsonify({"error": "Invalid session"}), 403

        # Save user message
        cursor.execute("""
            INSERT INTO messages (session_id, sender_type, message_text)
            VALUES (%s, 'user', %s)
        """, (data['session_id'], data['message']))

        # Generate response
        chat = model.start_chat(history=[
            {"role": msg['role'], "parts": [msg['content']]}
            for msg in data.get('context', [])
        ])
        response = chat.send_message(data['message'])
        ai_response = response.text

        # Save AI response
        cursor.execute("""
            INSERT INTO messages (session_id, sender_type, message_text)
            VALUES (%s, 'assistant', %s)
        """, (data['session_id'], ai_response))

        conn.commit()
        return jsonify({
            "user_message": data['message'],
            "ai_response": ai_response,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        if conn: conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


@app.route("/api/new_session", methods=["POST"])
def create_chat_session():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user_id = session["user_id"]
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO chat_sessions (user_id, title) VALUES (%s, 'New Chat')",
            (user_id,)
        )
        conn.commit()
        return jsonify({
            "session_id": cursor.lastrowid,
            "title": "New Chat",
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        if conn: conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


@app.route("/api/delete_session/<int:session_id>", methods=["DELETE"])
def delete_chat_session(session_id):
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user_id = session["user_id"]
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # First verify that the session belongs to the user
        cursor.execute(
            "SELECT id FROM chat_sessions WHERE id = %s AND user_id = %s",
            (session_id, user_id)
        )
        if not cursor.fetchone():
            return jsonify({"error": "Session not found or unauthorized"}), 404

        # Delete all messages in the session first (due to foreign key constraints)
        cursor.execute("DELETE FROM messages WHERE session_id = %s", (session_id,))

        # Then delete the session
        cursor.execute("DELETE FROM chat_sessions WHERE id = %s", (session_id,))

        conn.commit()
        return jsonify({"success": True, "message": "Session deleted successfully"})

    except Exception as e:
        if conn: conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


@app.route("/api/get_session/<int:session_id>", methods=["GET"])
def get_chat_session(session_id):
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user_id = session["user_id"]
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Verify session ownership
        cursor.execute("""
            SELECT id, title FROM chat_sessions
            WHERE id = %s AND user_id = %s
        """, (session_id, user_id))
        session_data = cursor.fetchone()
        
        if not session_data:
            return jsonify({"error": "Session not found or unauthorized"}), 404

        # Get all messages for this session
        cursor.execute("""
            SELECT message_text, sender_type, created_at
            FROM messages
            WHERE session_id = %s
            ORDER BY created_at ASC
        """, (session_id,))
        messages = cursor.fetchall()

        return jsonify({
            "session_id": session_id,
            "title": session_data["title"],
            "messages": messages
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


@app.route("/", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        hashed_password = generate_password_hash(
            password,
            method='pbkdf2:sha256',
            salt_length=16
        )

        conn = None
        cursor = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (full_name, email, password_hash) VALUES (%s, %s, %s)",
                (name, email, hashed_password)
            )
            conn.commit()
            return redirect("/login")
        except Exception as e:
            if '1062' in str(e):
                return "⚠️ Email already exists!"
            return f"Error: {str(e)}"
        finally:
            if cursor: cursor.close()
            if conn: conn.close()
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = None
        cursor = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, password_hash FROM users WHERE email = %s",
                (email,)
            )
            user = cursor.fetchone()

            if user and check_password_hash(user['password_hash'], password):
                session["user_id"] = user["id"]
                return redirect("/chatbot")
            return render_template("login.html", error="⚠️ Invalid email or password!")
        finally:
            if cursor: cursor.close()
            if conn: conn.close()
    return render_template("login.html")


if __name__ == "__main__":
    app.run(debug=True)
