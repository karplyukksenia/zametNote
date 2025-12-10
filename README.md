 # zametNote — Личная база знаний и заметки на Flask

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Flask](https://img.shields.io/badge/Flask-3.0%2B-lightgrey)
![SQLite](https://img.shields.io/badge/SQLite-3-green)

Простое, полностью локальное веб-приложение для ведения заметок и организации личных знаний.  
Никаких облаков, никаких подписок — всё хранится в одном файле SQLite у тебя на компьютере.

## Особенности (на декабрь 2025)

- Регистрация / логин / логаут (пароли надёжно хэшируются через bcrypt)  
- Создание, редактирование и удаление заметок  
- Поддержка тегов для каждой заметки  
- Удобный просмотр всех своих заметок в одной таблице  
- Полная приватность — заметки привязаны к аккаунту
- Минималистичный и чистый интерфейс  
- Работает полностью оффлайн после запуска  

## Технологии

- **Backend**: Flask (Python)  
- **База данных**: SQLite (`pkm_database.db`)  
- **Безопасность**: bcrypt  
- **Фронтенд**: HTML + CSS (шаблоны в `/templates`, стили в `/static`)

## Быстрый старт

```bash
# 1. Клонируем проект
git clone https://github.com/karplyukksenia/zametNote.git
cd zametNote

# 2. Создаём и активируем виртуальное окружение (рекомендуется)
python -m venv venv
source venv/bin/activate        # Linux / macOS
# venv\Scripts\activate         # Windows

# 3. Устанавливаем зависимости
pip install -r requirements.txt
# Если requirements.txt нет:
# pip install flask flask-bcrypt

# 4. Запускаем
python main.py
```

## Веб-версия

Доступна веб-версия приложения: https://zametnote.onrender.com/


