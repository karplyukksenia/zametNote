from flask import Flask, render_template, request, jsonify
import pyodbc
import os

app = Flask(__name__)


def get_db_connection():
    try:
        server = r'KSENIA-NOTEBOOK\SQLEXPRESS'
        database = 'database_PKM'

        connection_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;'
        conn = pyodbc.connect(connection_string)
        return conn
    except Exception as e:
        print(f"Ошибка подключения: {e}")
        return None


# Главная страница (как у коллеги)
@app.route('/')
def index():
    return render_template('index.html')


# API для получения заметок
@app.route('/api/notes', methods=['GET'])
def get_notes_api():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT n.id, n.user_id, n.title, n.content, n.created_at, n.updated_at
            FROM notes n
            ORDER BY n.updated_at DESC
        ''')

        notes = []
        for row in cursor:
            notes.append({
                'id': row.id,
                'user_id': row.user_id,
                'title': row.title,
                'content': row.content,
                'created_at': row.created_at.isoformat(),
                'updated_at': row.updated_at.isoformat()
            })

        return jsonify(notes)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


# API для создания заметки
@app.route('/api/notes', methods=['POST'])
def create_note_api():
    data = request.get_json()

    if not data or not all(k in data for k in ['user_id', 'title', 'content']):
        return jsonify({"error": "Missing required fields: user_id, title, content"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO notes (user_id, title, content) VALUES (?, ?, ?)',
            data['user_id'], data['title'], data['content']
        )
        conn.commit()

        return jsonify({"message": "Note created successfully"}), 201

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()


# Добавьте этот маршрут после существующих

@app.route('/all-notes')
def all_notes():
    return render_template('all_notes.html')


@app.route('/api/notes/all', methods=['GET'])
def get_all_notes_api():
    """API для получения всех заметок с полной информацией"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cursor = conn.cursor()

        # Получаем все заметки с информацией о пользователе
        cursor.execute('''
            SELECT 
                n.id, 
                n.user_id, 
                u.username,
                n.title, 
                n.content, 
                n.created_at, 
                n.updated_at
            FROM notes n
            INNER JOIN users u ON n.user_id = u.id
            ORDER BY n.updated_at DESC
        ''')

        notes = []
        for row in cursor:
            notes.append({
                'id': row.id,
                'user_id': row.user_id,
                'username': row.username,
                'title': row.title,
                'content': row.content,
                'created_at': row.created_at.isoformat(),
                'updated_at': row.updated_at.isoformat()
            })

        return jsonify(notes)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


if __name__ == '__main__':
    print("🚀 Запуск Flask PKM API...")
    print("📊 Подключение к базе данных...")

    test_conn = get_db_connection()
    if test_conn:
        test_conn.close()
        print("✅ База данных готова к работе!")
    else:
        print("❌ Проблемы с подключением к базе данных")

    print("\n🌐 Доступные URL:")
    print("http://localhost:5000/ - Главная страница")
    print("http://localhost:5000/api/notes - API заметок")
    print("\n⚡ Сервер запускается...")

    app.run(debug=True, host='0.0.0.0', port=5000)