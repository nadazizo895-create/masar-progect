# Masar Educational Platform

## وصف المشروع (Project Description)

منصة تعليمية مبنية باستخدام Flask و SQLite لتعليم البرمجة من خلال دروس تفاعلية واختبارات.

A Flask-based web application for learning programming through interactive lessons and quizzes.

## الميزات (Features)

- تسجيل المستخدمين و المصادقة (User registration and authentication)
- دروس برمجة متنوعة (Various programming lessons: Android Studio, Flutter, Python, etc.)
- اختبارات لكل موضوع (Quizzes for each topic)
- لوحة تحكم الإدارة (Admin panel)
- قاعدة بيانات SQLite (SQLite database)

## التثبيت (Installation)

1. استنساخ المستودع (Clone the repository)
2. تثبيت المتطلبات: `pip install flask pillow arabic-reshaper python-bidi`
3. تشغيل التطبيق: `python flask_app.py`

## الاستخدام (Usage)

الوصول إلى: http://127.0.0.1:5000

بيانات الإدارة: Admin@masar.com / Admin@1234

بيانات الطالب: nadazizo895@gmail.com / Test@1234

## هيكل المشروع (Project Structure)

- `flask_app.py`: التطبيق الرئيسي (Main application)
- `templates/`: قوالب HTML (HTML templates)
- `static/`: ملفات CSS، JS، الصور، والرفوع (CSS, JS, images, uploads)
- `masar.db`: قاعدة البيانات SQLite (SQLite database)

## التقنيات المستخدمة (Technologies Used)

- **Backend**: Flask (Python)
- **Database**: SQLite
- **Frontend**: HTML, CSS, JavaScript
- **Libraries**: Pillow (for images), arabic-reshaper, python-bidi (for Arabic text)

## المساهمة (Contributing)

Feel free to contribute by submitting issues or pull requests.

## الترخيص (License)

