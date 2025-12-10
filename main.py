from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import sqlite3
import os
from datetime import datetime
import bcrypt
from dotenv import load_dotenv


def init_db():
    conn = sqlite3.connect('pkm_database.db')
    cursor = conn.cursor()

    # Создаем таблицы как в SQL Server базе
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
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
        # Хешируем пароль для демо-пользователя
        demo_password_hash = bcrypt.hashpw('demo'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            ('demo_user', 'demo@example.com', demo_password_hash)
        )

    conn.commit()
    conn.close()


def get_db_connection():
    """Подключение к SQLite базе"""
    conn = sqlite3.connect('pkm_database.db')
    conn.row_factory = sqlite3.Row
    return conn


load_dotenv()

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'fallback_secret_key_if_not_set')
init_db()


# Маршруты аутентификации
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Проверка длины пароля
        if len(password) < 6:
            flash('Пароль должен содержать не менее 6 символов')
            return render_template('register.html')

        # Проверка на существующий EMAIL
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cur.fetchone():
            flash('Пользователь с таким email уже существует')
            cur.close()
            conn.close()
            return render_template('register.html')

        # Хеширование пароля
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Создание пользователя
        cur.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, password_hash)
        )

        conn.commit()
        cur.close()
        conn.close()

        flash('Регистрация успешна! Теперь вы можете войти.')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cur = conn.cursor()

        # Ищем пользователя по email
        cur.execute(
            "SELECT id, username, password_hash FROM users WHERE email = ?",
            (email,)
        )
        user = cur.fetchone()

        if user and bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')):
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['email'] = email
            cur.close()
            conn.close()
            # РЕДИРЕКТ НА ГЛАВНУЮ СТРАНИЦУ (index)
            return redirect(url_for('index'))
        else:
            flash('Неверный email или пароль')

        cur.close()
        conn.close()
        return render_template('login.html')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# Обновляем главную страницу
@app.route('/')
def index():
    if 'user_id' in session:
        return render_template('index.html')
    return render_template('login.html')


# Обновляем API для заметок с учетом авторизации
@app.route('/api/notes', methods=['GET'])
def get_notes_api():
    if 'user_id' not in session:
        return jsonify({"error": "Not authorized"}), 401

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT n.id, n.user_id, n.title, n.content,n.tags, n.created_at, n.updated_at
            FROM notes n
            WHERE n.user_id = ?
            ORDER BY n.updated_at DESC
        ''', (session['user_id'],))

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
    if 'user_id' not in session:
        return jsonify({"error": "Not authorized"}), 401

    data = request.get_json()
    print(data)
    if not data or not all(k in data for k in ['title', 'content', 'tags']):
        return jsonify({"error": "Missing required fields: title, content"}), 400

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO notes (user_id, title, content, tags) VALUES (?, ?, ?, ?)',
            (session['user_id'], data['title'], data['content'], ' '.join(i for i in data['tags']))
        )
        cursor.execute('SELECT id FROM notes WHERE title = ?', (data['title'],))
        note_id = cursor.fetchone()[0]
        for tag in data['tags']:
            cursor.execute('INSERT INTO tags (user_id, note_id, name) VALUES (?, ?, ?)',
                           (session['user_id'], note_id, tag,))

        conn.commit()
        return jsonify({"message": "Note created successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()


# получение заметок (версия от 26.11)
@app.route('/api/notes/all', methods=['GET'])
def get_all_notes_api():
    if 'user_id' not in session:
        return jsonify({"error": "Not authorized"}), 401

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT n.id, n.user_id, n.title, n.content, n.tags, 
                   n.created_at, n.updated_at, u.username
            FROM notes n
            LEFT JOIN users u ON n.user_id = u.id
            WHERE n.user_id = ?
            ORDER BY n.updated_at DESC
        ''', (session['user_id'],))

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


@app.route('/note/<int:note_id>')
def view_note(note_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('view_note.html', note_id=note_id)

# API для получения одной заметки
@app.route('/api/notes/<int:note_id>', methods=['GET'])
def get_note_api(note_id):
    if 'user_id' not in session:
        return jsonify({"error": "Not authorized"}), 401

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT n.id, n.user_id, n.title, n.content, n.tags, 
                   n.created_at, n.updated_at, u.username
            FROM notes n
            LEFT JOIN users u ON n.user_id = u.id
            WHERE n.id = ? AND n.user_id = ?
        ''', (note_id, session['user_id']))

        row = cursor.fetchone()
        if not row:
            return jsonify({"error": "Note not found"}), 404

        note = {
            'id': row['id'],
            'user_id': row['user_id'],
            'title': row['title'],
            'content': row['content'],
            'tags': row['tags'],
            'created_at': row['created_at'],
            'updated_at': row['updated_at'],
            'username': row['username']
        }

        return jsonify(note)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


# возможность изменения заметки
@app.route('/api/notes/<int:note_id>', methods=['PUT'])
def update_note_api(note_id):
    if 'user_id' not in session:
        return jsonify({"error": "Not authorized"}), 401

    data = request.get_json()
    print(f"Updating note {note_id} with data:", data)

    if not data or not all(k in data for k in ['title', 'content', 'tags']):
        return jsonify({"error": "Missing required fields: title, content, tags"}), 400

    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # Обновляем основную информацию заметки
        cursor.execute('''
            UPDATE notes 
            SET title = ?, content = ?, tags = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
        ''', (data['title'], data['content'], ' '.join(i for i in data['tags']), note_id, session['user_id']))

        # Обновляем теги в таблице tags
        # Сначала удаляем старые теги
        cursor.execute('DELETE FROM tags WHERE note_id = ? AND user_id = ?', (note_id, session['user_id']))

        # Добавляем новые теги
        for tag in data['tags']:
            cursor.execute('INSERT INTO tags (user_id, note_id, name) VALUES (?, ?, ?)',
                           (session['user_id'], note_id, tag))

        conn.commit()

        return jsonify({"message": "Note updated successfully"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()

@app.route('/api/graph-data', methods=['GET'])
def get_graph_data():
    if 'user_id' not in session:
        return jsonify({"error": "Not authorized"}), 401

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT id, title, tags FROM notes WHERE user_id = ? ORDER BY id', (session['user_id'],))
        rows = cursor.fetchall()

        nodes = []
        note_tags = {}

        for row in rows:
            note_id = row['id']
            title = row['title']
            tags_str = row['tags'] or ""
            tags_list = [t.strip().lower() for t in tags_str.split() if t.strip()]
            tag_set = set(tags_list)

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
                common_tags = note_tags[id1] & note_tags[id2]  # пересечение множеств
                if common_tags:
                    # Используем первый общий тег для связи
                    links.append({
                        "source": id1,
                        "target": id2,
                        "via_tag": list(common_tags)[0]
                    })

        return jsonify({"nodes": nodes, "links": links})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route('/all-notes')
def all_notes():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('all_notes.html')


if __name__ == '__main__':
    app.run()