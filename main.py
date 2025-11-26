from flask import Flask, render_template, request, jsonify
import sqlite3
import os
from datetime import datetime


def init_db():
    conn = sqlite3.connect('pkm_database.db')
    cursor = conn.cursor()

    # Создаем таблицы как в SQL Server базе
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notes(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            tags TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tags(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            note_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            FOREIGN KEY (note_id) REFERENCES notes (id)
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Создаем демо-пользователя если нет пользователей
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            ('demo_user', 'demo@example.com', 'demo_hash')
        )

    conn.commit()
    conn.close()


def get_db_connection():
    """Подключение к SQLite базе"""
    conn = sqlite3.connect('pkm_database.db')
    conn.row_factory = sqlite3.Row
    return conn


app = Flask(__name__)
init_db()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/all-notes')
def all_notes():
    return render_template('all_notes.html')


# API для получения заметок
@app.route('/api/notes', methods=['GET'])
def get_notes_api():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT n.id, n.user_id, n.title, n.content,n.tags, n.created_at, n.updated_at
            FROM notes n
            ORDER BY n.updated_at DESC
        ''')

        notes = []
        for row in cursor:
            notes.append({
                'id': row['id'],
                'user_id': row['user_id'],
                'title': row['title'],
                'content': row['content'],
                'tags': row['tags'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            })

        print(notes, cursor.fetchall())
        return jsonify(notes)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


# API для создания заметки
@app.route('/api/notes', methods=['POST'])
def create_note_api():
    data = request.get_json()
    print(data)
    if not data or not all(k in data for k in ['user_id', 'title', 'content', 'tags']):
        return jsonify({"error": "Missing required fields: user_id, title, content"}), 400

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO notes (user_id, title, content, tags) VALUES (?, ?, ?, ?)',
            (data['user_id'], data['title'], data['content'], ' '.join(i for i in data['tags']))
        )
        cursor.execute('SELECT id FROM notes WHERE title = ?', (data['title'],))
        note_id = cursor.fetchone()[0]
        for tag in data['tags']:
            cursor.execute('INSERT INTO tags (user_id, note_id, name) VALUES (?, ?, ?)',
                           (data['user_id'], note_id, tag,))

        conn.commit()
        return jsonify({"message": "Note created successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()


# получение заметок (версия от 26.11)
@app.route('/api/notes/all', methods=['GET'])
def get_all_notes_api():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT n.id, n.user_id, n.title, n.content, n.tags, 
                   n.created_at, n.updated_at, u.username
            FROM notes n
            LEFT JOIN users u ON n.user_id = u.id
            ORDER BY n.updated_at DESC
        ''')

        notes = []
        for row in cursor:
            notes.append({
                'id': row['id'],
                'user_id': row['user_id'],
                'title': row['title'],
                'content': row['content'],
                'tags': row['tags'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at'],
                'username': row['username']
            })

        return jsonify(notes)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/graph-data', methods=['GET'])
def get_graph_data():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, title, tags
            FROM notes
            ORDER BY id
        ''')
        rows = cursor.fetchall()

        nodes = []
        note_tags = {}  # id -> set(tags)

        for row in rows:
            note_id = row['id']
            title = row['title']
            tags_str = row['tags'] or ""
            tags_list = tags_str.split() if tags_str else []
            tag_set = set(tag.lower() for tag in tags_list if tag.strip())

            nodes.append({
                "id": note_id,
                "title": title,
                "tags": list(tag_set)
            })
            note_tags[note_id] = tag_set

        # Строим связи: если у двух заметок есть хотя бы 1 общий тег
        links = []
        note_ids = list(note_tags.keys())
        for i in range(len(note_ids)):
            for j in range(i + 1, len(note_ids)):
                id1, id2 = note_ids[i], note_ids[j]
                if note_tags[id1] & note_tags[id2]:  # пересечение множеств
                    links.append({"source": id1, "target": id2})

        return jsonify({"nodes": nodes, "links": links})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()
if __name__ == '__main__':
    app.run()