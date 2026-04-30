"""
================================================================
  app.py  —  منصة مسار التعليمية
  Flask + SQLite  —  Python Backend الكامل
  ✅ مُصلح: يستخدم render_template مع ملفات HTML حقيقية
================================================================
"""

import os
import io
import sqlite3
import hashlib
import secrets
from datetime import datetime
from functools import wraps

from flask import (
    Flask, render_template, request,
    redirect, url_for, session, jsonify, flash, g, send_file
)
from werkzeug.utils import secure_filename
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

# ════════════════════════════════════════════════════════
#  APP CONFIGURATION
# ════════════════════════════════════════════════════════
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "masar-dev-secret-2026")

BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
DB_PATH       = os.path.join(BASE_DIR, "masar.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"]      = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024   # 5 MB


# ════════════════════════════════════════════════════════
#  DATABASE LAYER
# ════════════════════════════════════════════════════════
def get_db():
    db = getattr(g, "_db", None)
    if db is None:
        db = g._db = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
    return db


@app.teardown_appcontext
def close_db(_exc):
    db = getattr(g, "_db", None)
    if db:
        db.close()


def query(sql, args=(), one=False):
    cur = get_db().execute(sql, args)
    rv  = cur.fetchone() if one else cur.fetchall()
    return (dict(rv) if rv else None) if one else [dict(r) for r in rv]


def execute(sql, args=()):
    db  = get_db()
    cur = db.execute(sql, args)
    db.commit()
    return cur.lastrowid


def migrate_db():
    """Add new columns to existing database without losing data."""
    db = sqlite3.connect(DB_PATH)
    c  = db.cursor()

    # ── users ──
    existing_cols = {row[1] for row in c.execute("PRAGMA table_info(users)")}
    new_cols_users = {
        "username":     "TEXT UNIQUE",
        "city":         "TEXT",
        "level":        "TEXT",
        "goal":         "TEXT",
        "skills":       "TEXT",
        "avatar":       "TEXT",
        "role":         "TEXT DEFAULT 'student'",
        "last_updated": "TEXT",
    }
    for col, col_type in new_cols_users.items():
        if col not in existing_cols:
            c.execute(f"ALTER TABLE users ADD COLUMN {col} {col_type}")
            print(f"✅ Migration: added column '{col}' to users")

    # ── tracks ──
    existing_track_cols = {row[1] for row in c.execute("PRAGMA table_info(tracks)")}
    new_cols_tracks = {
        "level":      "TEXT",
        "duration":   "TEXT",
        "dept_id":    "INTEGER",
        "created_at": "TEXT",
    }
    for col, col_type in new_cols_tracks.items():
        if col not in existing_track_cols:
            c.execute(f"ALTER TABLE tracks ADD COLUMN {col} {col_type}")
            print(f"✅ Migration: added column '{col}' to tracks")

    # ── cvs ──
    existing_cv_cols = {row[1] for row in c.execute("PRAGMA table_info(cvs)")}
    if "trainings" not in existing_cv_cols:
        c.execute("ALTER TABLE cvs ADD COLUMN trainings TEXT")
        print("✅ Migration: added column 'trainings' to cvs")

    # ── trainings table ──
    c.execute("""
        CREATE TABLE IF NOT EXISTS trainings (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL
                            REFERENCES users(id) ON DELETE CASCADE,
            title           TEXT    NOT NULL,
            organization    TEXT,
            dept            TEXT    CHECK(dept IN ('commerce','cs','other')),
            start_date      TEXT,
            end_date        TEXT,
            description     TEXT,
            certificate_url TEXT,
            created_at      TEXT    NOT NULL
                            DEFAULT (datetime('now','localtime'))
        )
    """)

    db.commit()
    db.close()


def init_db():
    """Create tables and seed data — runs once on startup."""
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    c = db.cursor()
    c.executescript("""
        -- ════════════════════════════════════════
        --  CORE: users
        -- ════════════════════════════════════════
        CREATE TABLE IF NOT EXISTS users (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name       TEXT    NOT NULL,
            username        TEXT    UNIQUE,
            email           TEXT    NOT NULL UNIQUE COLLATE NOCASE,
            password_hash   TEXT    NOT NULL,
            city            TEXT,
            level           TEXT,
            goal            TEXT,
            skills          TEXT,
            is_paid         INTEGER NOT NULL DEFAULT 0,
            is_admin        INTEGER NOT NULL DEFAULT 0,
            streak_days     INTEGER NOT NULL DEFAULT 0,
            videos_watched  INTEGER NOT NULL DEFAULT 0,
            badges          INTEGER NOT NULL DEFAULT 0,
            avatar          TEXT,
            role            TEXT    NOT NULL DEFAULT 'student'
                            CHECK(role IN ('student','instructor','admin')),
            last_updated    TEXT    NOT NULL
                            DEFAULT (datetime('now','localtime')),
            joined_at       TEXT    NOT NULL
                            DEFAULT (datetime('now','localtime'))
        );

        -- ════════════════════════════════════════
        --  Departments — الأقسام
        -- ════════════════════════════════════════
        CREATE TABLE IF NOT EXISTS departments (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT    NOT NULL,
            description     TEXT,
            icon            TEXT,
            created_at      TEXT    NOT NULL
                            DEFAULT (datetime('now','localtime'))
        );

        -- ════════════════════════════════════════
        --  Books — الكتب
        -- ════════════════════════════════════════
        CREATE TABLE IF NOT EXISTS books (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            title           TEXT    NOT NULL,
            author          TEXT,
            dept_id         INTEGER REFERENCES departments(id) ON DELETE SET NULL,
            price           REAL,
            published_at    TEXT,
            created_at      TEXT    NOT NULL
                            DEFAULT (datetime('now','localtime'))
        );

        -- ════════════════════════════════════════
        --  Programming Languages — لغات البرمجة
        -- ════════════════════════════════════════
        CREATE TABLE IF NOT EXISTS programming_languages (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT    NOT NULL,
            dept_id         INTEGER REFERENCES departments(id) ON DELETE SET NULL,
            tools           TEXT,
            version         TEXT
        );

        -- ════════════════════════════════════════
        --  Courses — الدورات التدريبية  (tracks renamed for clarity)
        -- ════════════════════════════════════════
        CREATE TABLE IF NOT EXISTS tracks (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            slug        TEXT    NOT NULL UNIQUE,
            name_ar     TEXT    NOT NULL,
            name_en     TEXT    NOT NULL,
            description TEXT,
            level       TEXT,
            duration    TEXT,
            dept_id     INTEGER REFERENCES departments(id) ON DELETE SET NULL,
            created_at  TEXT    NOT NULL
                        DEFAULT (datetime('now','localtime'))
        );

        -- ════════════════════════════════════════
        --  Courses (from schema) — prog_lang ↔ department
        -- ════════════════════════════════════════
        CREATE TABLE IF NOT EXISTS lang_courses (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            prog_lang_id    INTEGER NOT NULL
                            REFERENCES programming_languages(id) ON DELETE CASCADE,
            name            TEXT    NOT NULL,
            dept_id         INTEGER REFERENCES departments(id) ON DELETE SET NULL,
            tools           TEXT,
            created_at      TEXT    NOT NULL
                            DEFAULT (datetime('now','localtime'))
        );

        -- ════════════════════════════════════════
        --  Exams — الامتحانات
        -- ════════════════════════════════════════
        CREATE TABLE IF NOT EXISTS exams (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            title           TEXT    NOT NULL,
            dept_id         INTEGER REFERENCES departments(id) ON DELETE SET NULL,
            duration        INTEGER,                  -- بالدقائق
            total_questions INTEGER NOT NULL DEFAULT 10,
            max_score       INTEGER NOT NULL DEFAULT 100,
            created_at      TEXT    NOT NULL
                            DEFAULT (datetime('now','localtime'))
        );

        -- ════════════════════════════════════════
        --  Questions — الأسئلة
        -- ════════════════════════════════════════
        CREATE TABLE IF NOT EXISTS questions (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_id         INTEGER NOT NULL
                            REFERENCES exams(id) ON DELETE CASCADE,
            text            TEXT    NOT NULL,
            type            TEXT    NOT NULL DEFAULT 'MCQ'
                            CHECK(type IN ('MCQ','true_false','short')),
            answer          TEXT
        );

        -- ════════════════════════════════════════
        --  CVs — السير الذاتية
        -- ════════════════════════════════════════
        CREATE TABLE IF NOT EXISTS cvs (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL UNIQUE
                            REFERENCES users(id) ON DELETE CASCADE,
            title           TEXT,
            skills          TEXT,
            experience      TEXT,
            education       TEXT,
            trainings       TEXT,
            last_updated    TEXT    NOT NULL
                            DEFAULT (datetime('now','localtime'))
        );

        -- ════════════════════════════════════════
        --  Trainings — التدريبات
        -- ════════════════════════════════════════
        CREATE TABLE IF NOT EXISTS trainings (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL
                            REFERENCES users(id) ON DELETE CASCADE,
            title           TEXT    NOT NULL,
            organization    TEXT,
            dept            TEXT    CHECK(dept IN ('commerce','cs','other')),
            start_date      TEXT,
            end_date        TEXT,
            description     TEXT,
            certificate_url TEXT,
            created_at      TEXT    NOT NULL
                            DEFAULT (datetime('now','localtime'))
        );

        -- ════════════════════════════════════════
        --  user_tracks — ربط المستخدم بالمسار
        -- ════════════════════════════════════════
        CREATE TABLE IF NOT EXISTS user_tracks (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL
                        REFERENCES users(id) ON DELETE CASCADE,
            track_id    INTEGER NOT NULL
                        REFERENCES tracks(id) ON DELETE CASCADE,
            progress    INTEGER NOT NULL DEFAULT 0,
            started_at  TEXT    NOT NULL
                        DEFAULT (datetime('now','localtime')),
            UNIQUE(user_id, track_id)
        );

        -- ════════════════════════════════════════
        --  quiz_answers
        -- ════════════════════════════════════════
        CREATE TABLE IF NOT EXISTS quiz_answers (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id       INTEGER NOT NULL
                          REFERENCES users(id) ON DELETE CASCADE,
            q1            TEXT,
            q2            TEXT,
            q3            TEXT,
            result_track  TEXT,
            taken_at      TEXT NOT NULL
                          DEFAULT (datetime('now','localtime'))
        );

        -- ════════════════════════════════════════
        --  exam_results
        -- ════════════════════════════════════════
        CREATE TABLE IF NOT EXISTS exam_results (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL
                        REFERENCES users(id) ON DELETE CASCADE,
            track_id    INTEGER REFERENCES tracks(id),
            correct     INTEGER NOT NULL DEFAULT 0,
            total       INTEGER NOT NULL DEFAULT 0,
            percent     INTEGER NOT NULL DEFAULT 0,
            taken_at    TEXT    NOT NULL
                        DEFAULT (datetime('now','localtime'))
        );

        -- ════════════════════════════════════════
        --  payments — المدفوعات
        -- ════════════════════════════════════════
        CREATE TABLE IF NOT EXISTS payments (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL
                        REFERENCES users(id) ON DELETE CASCADE,
            amount      REAL    NOT NULL DEFAULT 50.0,
            method      TEXT    CHECK(method IN ('Visa','Mastercard','Fawry','instapay')),
            status      TEXT    NOT NULL DEFAULT 'pending'
                        CHECK(status IN ('pending','done','failed')),
            paid_at     TEXT,
            created_at  TEXT    NOT NULL
                        DEFAULT (datetime('now','localtime'))
        );

        -- ════════════════════════════════════════
        --  activities
        -- ════════════════════════════════════════
        CREATE TABLE IF NOT EXISTS activities (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL
                        REFERENCES users(id) ON DELETE CASCADE,
            description TEXT    NOT NULL,
            score       TEXT,
            happened_at TEXT    NOT NULL
                        DEFAULT (datetime('now','localtime'))
        );
    """)

    c.executemany(
        "INSERT OR IGNORE INTO tracks (slug,name_ar,name_en,description) VALUES (?,?,?,?)", 
        [
            # مسارات رئيسية
            ("web",               "تطوير الويب",        "Web Development",       "HTML, CSS, JavaScript, React"),
            ("mobile",            "تطبيقات الجوال",     "Mobile Apps",           "Flutter, React Native, Android, iOS"),
            ("data",              "تحليل البيانات",     "Data Analysis",         "Python, Pandas, SQL, Power BI"),
            # لغات منفصلة - ويب
            ("html",               "HTML",                "HTML",                 "بناء هيكل صفحات الويب"),
            ("css",                "CSS",                 "CSS",                  "تنسيق وتصميم صفحات الويب"),
            ("js",                 "JS",                  "JS",                   "البرمجة التفاعلية للويب"),
            ("react",              "React",               "React",                "بناء واجهات مستخدم متطوره"),
            ("nodejs",             "NodeJS",              "NodeJS",               "برمجه خوادم الويب"),
            ("python",             "Python",              "Python",               "برمجه الانظمه والذكاء الاصطناعى "),
            ("php",                "PHP",                 "PHP",                  "تطوير مواقع الويب الديناميكية "),
            ("sql",                "SQL",                 "SQL",                  "اداره وتنظيم قواعد البيانات"),
            ("firebase",           "Firebase",            "Firebase",             "حلول قواعد البيانات السحابيه المتكامله"),
            # لغات منفصلة - جوال
            ("flutter",            "Flutter",             "Flutter",              "تطبيقات متعددة المنصات بـ Dart"),
            ("react_native",       "React Native",        "React Native",         "تطبيقات iOS و Android بـ JavaScript"),
            ("kotlin",             "Kotlin",              "Kotlin",               "تطبيقات Android الأصيلة"),
            ("java",               "JAVA" ,               "JAVA" ,                "تطبيقات الاندرويد"),
            ("xcode",              "Xcode",               "Xcode",                " البيئه الرسميه لتطوير تطبيقات ايفون"),
            ("android_studio",     "Android_Studio",      "Android_Studio",       "البيئه الرسميه لتطوير تطبيفات الاندرويد"),
            ("authentication",     "Authentication",      "Authentication",       "نظم التحقق من الهويه وتسجيل الدخول"), 
            ("local_storge",       "Local_Storge",        "Local_Storge",         "تخزين البيانات محليا على جهاز المستخدم"),
            ("push_notifications", "Push_Notifications",  "Push_Notifications",   "ارسال واستقبال التنبيهات الفوريه"),
            ("swift",              "Swift",               "Swift",                "تطبيقات iOS الأصيلة"),
            ("xml",                "XML",                 "XML" ,                 "تصميم واجهات المستخدم التقليدية للأندرويد") ,         
            ("uikit",              "UIKIT",               "UIKIT",                "الإطار الأساسي لبناء واجهات تطبيقات iOS"),
            ("jetpack_compose",    "Jetpack_Compose",     "Jetpack_Compose",      "بناء واجهات أندرويد حديثة بأسلوب برمجى متطور" ),
            ("swiftui",            "Swiftui",             "Swiftui",              "أحدث تقنيات بناء واجهات مستخدم Apple"),
            ("rest_api",           "rest_api",            "Rest_Api",             "ربط التطبيق بالسيرفر وتبادل البيانات" ),
            # لغات منفصلة - بيانات  (python و sql مُعرَّفان أعلاه بالفعل)
            # ("python", ...) ← مكرر — تم حذفه
            # ("sql",    ...) ← مكرر — تم حذفه
            ("pandas",              "Pandas",              "Pandas",               "مكتبه تحليل وهيكله البيانات"),
            ("numpy",               "Numpy",               "Numpy",                "المعالجه الرياضيه والمصفوفات الحسابيه"),
            ("matplotlib",          "matplotlib",          "matplotlib",           "تمثيل البيانات والرسوم البيانيه"),
            ("powerbi",             "Powerbi",             "Powerbi",              "تحليل بيانات الاعمال واعداد التقارير الاستراتيجيه"),
            ("tableau",             "Tableau",             "Tableau",              "تصوير وتحليل البيانات التفاعليه"),
        ],
    )

    admin_hash = hashlib.sha256("Admin@1234".encode()).hexdigest()
    c.execute(
        "INSERT OR IGNORE INTO users (full_name,email,password_hash,is_paid,is_admin) VALUES (?,?,?,1,1)",
        ("مدير مسار", "admin@masar.com", admin_hash),
    )

    student_hash = hashlib.sha256("Test@1234".encode()).hexdigest()
    c.execute(
        "INSERT OR IGNORE INTO users (full_name,email,password_hash,is_paid,streak_days,videos_watched,badges) VALUES (?,?,?,1,12,24,5)",
        ("ندى طلعت عبدالعزيز", "nada@masar.com", student_hash),
    )

    db.commit()
    db.close()
    print("✅ Database ready:", DB_PATH)


# ════════════════════════════════════════════════════════
#  HELPERS & DECORATORS
# ════════════════════════════════════════════════════════
def hash_pw(plain: str) -> str:
    return hashlib.sha256(plain.encode()).hexdigest()


def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    return query("SELECT * FROM users WHERE id=?", (uid,), one=True)


def log_activity(user_id, description, score=None):
    execute(
        "INSERT INTO activities (user_id,description,score) VALUES (?,?,?)",
        (user_id, description, score),
    )


def quiz_to_track(answers: dict):
    scores = {"web": 0, "mobile": 0, "data": 0}
    mapping = {"a": "web", "b": "mobile", "c": "data"}
    for key in ["q1","q2","q3","q4","q5","q6","q7","q8","q9","q10"]:
        val = answers.get(key, "")
        track = mapping.get(val, "")
        if track:
            scores[track] += 1
    return max(scores, key=scores.get)


def grade_msg(percent, lang="ar"):
    if lang == "ar":
        if percent >= 90: return "🏆 ممتاز! أداء استثنائي!"
        if percent >= 75: return "🌟 جيد جداً! استمر في التقدم!"
        if percent >= 60: return "👍 جيد، راجع بعض المفاهيم!"
        return "📚 لا تيأس، راجع المحتوى وحاول مرة أخرى!"
    else:
        if percent >= 90: return "🏆 Excellent!"
        if percent >= 75: return "🌟 Very Good!"
        if percent >= 60: return "👍 Good — review a few concepts!"
        return "📚 Don't give up — review and try again!"


def login_required(f):
    @wraps(f)
    def wrap(*a, **kw):
        if not session.get("user_id"):
            flash("يجب تسجيل الدخول أولاً", "warning")
            return redirect(url_for("auth", next=request.url))
        return f(*a, **kw)
    return wrap


def paid_required(f):
    @wraps(f)
    def wrap(*a, **kw):
        user = current_user()
        if not user or not user["is_paid"]:
            flash("هذا المحتوى للمشتركين المدفوعين فقط", "info")
            return redirect(url_for("payment"))
        return f(*a, **kw)
    return wrap


def admin_required(f):
    @wraps(f)
    def wrap(*a, **kw):
        user = current_user()
        if not user or not user["is_admin"]:
            flash("غير مصرح لك بالدخول", "danger")
            return redirect(url_for("index"))
        return f(*a, **kw)
    return wrap


@app.context_processor
def inject_user():
    return {"user": current_user()}


# ════════════════════════════════════════════════════════
#  EXAM SCORING
# ════════════════════════════════════════════════════════
# كل امتحان لغة عنده 10 أسئلة من q1 لـ q10
LANG_EXAM_KEYS = [f"q{i}" for i in range(1, 11)]

# الامتحانات القديمة (web/mobile/data) بأسئلة مختلفة
LEGACY_EXAM_KEYS = ["q1", "q2", "q3", "q8", "q9", "q10", "q15", "q16"]


def score_exam(form_data, lang_slug=None) -> dict:
    """يحسب نتيجة الامتحان حسب نوعه."""
    lang_slugs = {"html", "css", "js", "rest_api", "flutter", "react_native",
                  "kotlin", "swift", "python", "sql"}
    if lang_slug and lang_slug in lang_slugs:
        keys = LANG_EXAM_KEYS
    else:
        keys = LEGACY_EXAM_KEYS
    correct = sum(1 for k in keys if form_data.get(k) == "1")
    total   = len(keys)
    percent = round(correct / total * 100) if total > 0 else 0
    return {"correct": correct, "total": total, "percent": percent}


# ════════════════════════════════════════════════════════
#  ROUTES
# ════════════════════════════════════════════════════════

@app.route("/")
def index():
    return render_template("index2.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/auth", methods=["GET", "POST"])
def auth():
    if session.get("user_id"):
        return redirect(url_for("choice"))

    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("البريد الإلكتروني وكلمة المرور مطلوبان", "danger")
            return redirect(url_for("auth"))

        user = query(
            "SELECT * FROM users WHERE email=? AND password_hash=?",
            (email, hash_pw(password)),
            one=True,
        )
        if user:
            session["user_id"]   = user["id"]
            session["user_name"] = user["full_name"]
            session["is_admin"]  = bool(user["is_admin"])
            log_activity(user["id"], "تسجيل دخول")
            flash(f"أهلاً {user['full_name']}!", "success")
            next_url = request.form.get("next") or request.args.get("next")
            if user["is_admin"]:
                return redirect(url_for("admin_panel"))
            # لو فيه next_url (جاي من صفحة لغة) روح عليه، غير كده روح للـ choice
            if next_url and next_url.startswith("/"):
                return redirect(next_url)
            return redirect(url_for("choice"))
        else:
            flash("بريد إلكتروني أو كلمة مرور غير صحيحة", "danger")
            return redirect(url_for("auth"))

    return render_template("auth.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email     = request.form.get("email", "").strip().lower()
        email2    = request.form.get("email2", "").strip().lower()
        password  = request.form.get("password", "")
        password2 = request.form.get("password2", "")

        errors = []
        if not full_name:            errors.append("الاسم مطلوب")
        if not email or "@" not in email: errors.append("بريد إلكتروني غير صحيح")
        if email != email2:          errors.append("البريدان غير متطابقان")
        if len(password) < 6:        errors.append("كلمة المرور 6 أحرف على الأقل")
        if password != password2:    errors.append("كلمتا المرور غير متطابقتان")

        if errors:
            for e in errors:
                flash(e, "danger")
            return redirect(url_for("register"))

        existing = query("SELECT id FROM users WHERE email=?", (email,), one=True)
        if existing:
            flash("البريد الإلكتروني مسجّل بالفعل", "danger")
            return redirect(url_for("register"))

        uid = execute(
            "INSERT INTO users (full_name,email,password_hash) VALUES (?,?,?)",
            (full_name, email, hash_pw(password)),
        )
        session["user_id"]   = uid
        session["user_name"] = full_name
        session["is_admin"]  = False
        log_activity(uid, "إنشاء حساب جديد")
        flash("تم إنشاء حسابك بنجاح! اختر مسارك الآن 🎯", "success")
        next_url = request.form.get("next") or request.args.get("next")
        return redirect(next_url or url_for("tracks"))

    return render_template("register.html")


@app.route("/forgot", methods=["GET", "POST"])
def forgot():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        # لا نكشف إن كان البريد مسجّلاً أم لا (أمان)
        flash("إذا كان البريد مسجّلاً، ستصلك رسالة استعادة قريباً", "success")
        return redirect(url_for("forgot"))

    return render_template("forgot.html")


@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        email     = request.form.get("email", "").strip().lower()
        password  = request.form.get("password", "")
        password2 = request.form.get("password2", "")

        if password != password2:
            flash("كلمتا المرور غير متطابقتان", "danger")
            return redirect(url_for("reset_password"))
        if len(password) < 6:
            flash("كلمة المرور 6 أحرف على الأقل", "danger")
            return redirect(url_for("reset_password"))

        user = query("SELECT id FROM users WHERE email=?", (email,), one=True)
        if not user:
            flash("البريد الإلكتروني غير مسجّل", "danger")
            return redirect(url_for("reset_password"))

        execute(
            "UPDATE users SET password_hash=? WHERE email=?",
            (hash_pw(password), email),
        )
        flash("تم تحديث كلمة المرور. سجّل دخولك الآن.", "success")
        return redirect(url_for("auth"))

    return render_template("reset-pa.html")


@app.route("/choice")
def choice():
    return render_template("choice.html")


@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    if request.method == "POST":
        answers = {f"q{i}": request.form.get(f"q{i}", "") for i in range(1, 11)}

        if not all(answers.values()):
            flash("يرجى الإجابة على جميع الأسئلة", "warning")
            return redirect(url_for("quiz"))

        recommended = quiz_to_track(answers)
        user_id = session.get("user_id")
        if user_id:
            execute(
                "INSERT INTO quiz_answers (user_id,q1,q2,q3,result_track) VALUES (?,?,?,?,?)",
                (user_id, answers["q1"], answers["q2"], answers["q3"], recommended),
            )
            log_activity(user_id, "أجرى اختبار الميول", recommended)
        session["recommended_track"] = recommended
        track_names = {
            "web":    "تطوير الويب",
            "mobile": "تطبيقات الجوال",
            "data":   "تحليل البيانات",
        }
        flash(f"🎯 المسار الأنسب لك: {track_names.get(recommended, recommended)}", "success")
        return redirect(url_for("track_detail", slug=recommended))

    return render_template("quiz.html")
# ════════════════════════════════════════════════════════
#  PROJECTS / PRO PAGES ROUTES
# ════════════════════════════════════════════════════════


@app.route("/tracks")
def tracks():
    recommended = session.get("recommended_track", "")
    all_tracks  = query("SELECT * FROM tracks")
    progress    = {}
    if session.get("user_id"):
        user_id  = session["user_id"]
        progress = {
            row["track_id"]: row["progress"]
            for row in query(
                "SELECT track_id,progress FROM user_tracks WHERE user_id=?",
                (user_id,),
            )
        }
    return render_template("tracks.html", tracks=all_tracks, recommended=recommended, progress=progress)


@app.route("/track/<slug>")
def track_detail(slug):
    track = query("SELECT * FROM tracks WHERE slug=?", (slug,), one=True)
    if not track:
        flash("المسار غير موجود", "danger")
        return redirect(url_for("tracks"))

    # لو مسجل — سجّل دخوله في user_tracks
    if session.get("user_id"):
        execute(
            "INSERT OR IGNORE INTO user_tracks (user_id,track_id) VALUES (?,?)",
            (session["user_id"], track["id"]),
        )

    user    = current_user()
    is_paid = user and bool(user["is_paid"])

    # ── المسارات الرئيسية الثلاثة — نسختان (مجاني / مدفوع) ──
    main_free_map = {
        "web":    "web.html",
        "mobile": "app.html",
        "data":   "data.html",
    }
    main_paid_map = {
        "web":    "wep_p.html",
        "mobile": "app_p.html",
        "data":   "data_p.html",
    }
    if slug in main_free_map:
        tmpl = main_paid_map[slug] if is_paid else main_free_map[slug]
        return render_template(tmpl, track=track)

    # ── صفحات تفاصيل المسارات (web-track / mobile-track / data-track) ──
    track_page_map = {
        "web-track":    "wep_p.html",
        "mobile-track": "app_p.html",
        "data-track":   "data_p.html",
    }
    if slug in track_page_map:
        tmpl = track_page_map[slug] if is_paid else main_free_map.get(slug.replace("-track", ""), "web.html")
        return render_template(tmpl, track=track)

    # ── لغات ويب ──
    web_langs = {"html", "css", "js", "react", "nodejs", "php", "firebase", "sql"}
    # ── لغات جوال ──
    mobile_langs = {
        "flutter", "react_native", "kotlin", "swift", "java", "xcode",
        "android_studio", "authentication", "local_storge", "push_notifications",
        "xml", "uikit", "jetpack_compose", "swiftui", "rest_api",
    }
    # ── لغات بيانات ──
    data_langs = {"python", "pandas", "numpy", "matplotlib", "powerbi", "tableau"}

    all_langs = web_langs | mobile_langs | data_langs

    if slug in all_langs:
        # اللغات تطلب تسجيل دخول قبل الفيديوهات
        if not session.get("user_id"):
            flash("سجّل دخولك أولاً لمشاهدة الفيديوهات", "warning")
            return redirect(url_for("auth", next=url_for("lessons", slug=slug)))
        # مسجل → روح على الـ lessons مباشرة
        return redirect(url_for("lessons", slug=slug))
    return render_template("web.html", track=track)

@app.route("/lessons/<slug>")
def lessons(slug):
    # المسارات الرئيسية — متاحة بدون تسجيل (عرض اللغات فقط)
    free_slugs = {"web", "mobile", "data", "web-track", "mobile-track", "data-track"}

    free_template_map = {
        "web":         "lessonss.html",
        "mobile":      "lesson_app.html",
        "data":        "lesson_data.html",
        "web-track":   "wep_p.html",
        "mobile-track":"app_p.html",
        "data-track":  "data_p.html",
    }

    if slug in free_slugs:
        # الزائر يشوف اللغات بدون تسجيل
        track = query("SELECT * FROM tracks WHERE slug=?", (slug,), one=True)
        user = current_user()
        is_paid = user and bool(user["is_paid"])
        paid_map = {
            "web":    "wep_p.html",
            "mobile": "app_p.html",
            "data":   "data_p.html",
        }
        free_map = {
            "web":    "web.html",
            "mobile": "app.html",
            "data":   "data.html",
        }
        if is_paid:
            target_template = paid_map.get(slug, "web.html")
        else:
            target_template = free_map.get(slug, "web.html")
        return render_template(target_template, track=track)

    # باقي الصفحات (فيديوهات) — تسجيل الدخول مطلوب أولاً
    if not session.get("user_id"):
        flash("سجّل دخولك أولاً لمشاهدة الفيديوهات", "warning")
        return redirect(url_for("auth", next=url_for("lessons", slug=slug)))

    track = query("SELECT * FROM tracks WHERE slug=?", (slug,), one=True)
    if not track:
        return redirect(url_for("tracks"))

    user_id = session["user_id"]

    # تحديث التقدم
    execute(
        "UPDATE user_tracks SET progress=CASE WHEN progress<30 THEN 30 ELSE progress END WHERE user_id=? AND track_id=?",
        (user_id, track["id"]),
    )

    log_activity(user_id, f"بدأ دروس {track['name_ar']}")

    lesson_template_map = {
        # لغات ويب
        "html":               "lesson_html.html",
        "css":                "lesson_css.html",
        "js":                 "lesson_js.html",
        "react":              "lesson_react.html",
        "nodejs":             "lesson_nodejs.html",
        "php":                "lesson_php.html",
        "firebase":           "lesson_firebase.html",
        # لغات جوال
        "flutter":            "lesson_flutter.html",
        "react_native":       "lesson_react_native.html",
        "kotlin":             "lesson_kotlin.html",
        "swift":              "lesson_swift.html",
        "xml":                "lesson_xml.html",
        "uikit":              "lesson_uikit.html",
        "java":               "lesson_java.html",
        "xcode":              "lesson_xcode.html",
        "android_studio":     "lesson_android_studio.html",
        "authentication":     "lesson_authentication.html",
        "local_storge":       "lesson_local_storge.html",
        "push_notifications": "lesson_push_notifications.html",
        "jetpack_compose":    "lesson_jetpack_compose.html",
        "swiftui":            "lesson_swiftui.html",
        "rest_api":           "lesson_rest_api.html",
        # لغات بيانات
        "python":             "lesson_python.html",
        "sql":                "lesson_sql.html",
        "pandas":             "lesson_pandas.html",
        "numpy":              "lesson_numpy.html",
        "matplotlib":         "lesson_matplotlib.html",
        "powerbi":            "lesson_powerbi.html",
        "tableau":            "lesson_tableau.html",
    }

    target_template = lesson_template_map.get(slug, "lessonss.html")
    return render_template(target_template, track=track)


@app.route("/exam/<slug>", methods=["GET", "POST"])
@login_required
def exam(slug):
    track = query("SELECT * FROM tracks WHERE slug=?", (slug,), one=True)
    if not track:
        return redirect(url_for("tracks"))

    if request.method == "POST":
        result  = score_exam(request.form, lang_slug=slug)
        user_id = session["user_id"]

        exam_id = execute(
            "INSERT INTO exam_results (user_id,track_id,correct,total,percent) VALUES (?,?,?,?,?)",
            (user_id, track["id"], result["correct"], result["total"], result["percent"]),
        )
        execute(
            "UPDATE user_tracks SET progress=? WHERE user_id=? AND track_id=?",
            (min(result["percent"], 100), user_id, track["id"]),
        )
        log_activity(user_id, f"اجتاز امتحان {track['name_ar']}", f"{result['percent']}%")

        session["exam_result"] = result
        session["exam_track"]  = slug
        session["exam_id"]     = exam_id
        return redirect(url_for("result"))

    template_map = {
        # مسارات رئيسية
        "web":                "final-exam.html",
        "mobile":             "app_q.html",
        "data":               "data_q.html",
        # لغات ويب
        "html":               "html_q.html",
        "css":                "css_q.html",
        "js":                 "js_q.html",
        "react":              "react_q.html",
        "nodejs":             "nodejs_q.html",
        "php":                "php_q.html",
        "firebase":           "firebase_q.html",
        # لغات جوال
        "flutter":            "flutter_q.html",
        "react_native":       "react_native_q.html",
        "kotlin":             "kotlin_q.html",
        "xml":                "xml_q.html",
        "uikit":              "uikit_q.html",
        "java":               "java_q.html",
        "xcode":              "xcode_q.html",
        "android_studio":     "android_studio_q.html",
        "authentication":     "authentication_q.html",
        "local_storge":       "local_storge_q.html",
        "push_notifications": "push_notifications_q.html",
        "jetpack_compose":    "jetpack_compose_q.html",
        "swift":              "swift_q.html",
        "swiftui":            "swiftui_q.html",
        "rest_api":           "rest_api_q.html",
        # لغات بيانات
        "python":             "python_q.html",
        "sql":                "sql_q.html",
        "pandas":             "pandas_q.html",
        "numpy":              "numpy_q.html",
        "matplotlib":         "matplotlib_q.html",
        "powerbi":            "powerbi_q.html",
        "tableau":            "tableau_q.html",
    }
    return render_template(template_map.get(slug, "final-exam.html"), track=track)


@app.route("/result")
@login_required
def result():
    result_data = session.get("exam_result")
    if not result_data:
        return redirect(url_for("choice"))

    percent          = result_data["percent"]
    msg              = grade_msg(percent)
    show_certificate = percent >= 60   # يظهر زر الشهادة لو نجح
    exam_id          = session.get("exam_id")
    return render_template("result.html", result=result_data, msg=msg, show_certificate=show_certificate, exam_id=exam_id)

# ════════════════════════════════════════════════════════
#  CERTIFICATE — helpers + download route
#  pip install Pillow arabic-reshaper python-bidi
# ════════════════════════════════════════════════════════

def _arabic(text: str) -> str:
    """يشكّل النص العربي ويعكس الاتجاه عشان Pillow تكتبه صح"""
    return get_display(arabic_reshaper.reshape(str(text)))


def _draw_centered(draw, y, text, font, fill, img_width):
    """يكتب النص في المنتصف أفقياً"""
    bbox = draw.textbbox((0, 0), text, font=font)
    x = (img_width - (bbox[2] - bbox[0])) // 2
    draw.text((x, y), text, font=font, fill=fill)


@app.route("/certificate/download/<int:exam_id>")
@login_required
def certificate_download(exam_id):
    """يولّد الشهادة بفتح صورة الخلفية والكتابة عليها"""
    user = current_user()
    if not user:
        return redirect(url_for("auth"))

    # جلب الامتحان المحدد بالـ id
    last_exam = query(
        """SELECT er.percent, t.name_ar
           FROM exam_results er
           JOIN tracks t ON er.track_id = t.id
           WHERE er.user_id = ? AND er.id = ?""",
        (user["id"], exam_id), one=True,
    )
    if not last_exam:
        flash("الشهادة دي مش موجودة", "danger")
        return redirect(url_for("profile"))

    track_name = last_exam["name_ar"]
    score      = last_exam["percent"]

    issue_date = datetime.now().strftime("%Y/%m/%d")

    # ── فتح صورة الخلفية ──
    cert_path = os.path.join(BASE_DIR, "static", "image", "crtificatee.png")
    img  = Image.open(cert_path).convert("RGBA")
    draw = ImageDraw.Draw(img)
    W, H = img.size

    # ── اختيار الخط: بيجرّب كل الخيارات بالترتيب ──
    def load_font(size):
        candidates = [
            os.path.join(BASE_DIR, "static", "fonts", "Cairo.ttf"),
            os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "arial.ttf"),
            os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "tahoma.ttf"),
            os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "times.ttf"),
            os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "calibri.ttf"),
            os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "verdana.ttf"),
            "/usr/share/fonts/truetype/freefont/FreeSerif.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
        for fp in candidates:
            if os.path.exists(fp):
                try:
                    return ImageFont.truetype(fp, size)
                except Exception:
                    continue
        # آخر حل: الخط الافتراضي المدمج في Pillow
        return ImageFont.load_default()

    fn = load_font(30)  # اسم الطالب
    ft = load_font(25)  # اسم المسار
    fd = load_font(20)  # التاريخ

    # ── كتابة البيانات على الصورة ──
    # الصورة 641x472 — الـ y محسوبة على أساس النصوص الثابتة

    # اسم الطالب (بعد "إلى الطالب/ة:")
    _draw_centered(draw, 195, _arabic(user["full_name"]), fn, (255, 255, 255, 255), W)

    # اسم المسار (بعد "وعلى تفوقه الدراسي في:")
    _draw_centered(draw, 247,  _arabic(track_name), ft, (0, 255, 255, 255), W)

    
    # تنسيق التاريخ ليكون يوم/شهر/سنة
    formatted_date = datetime.now().strftime('%d/%m/%Y')
    #التاريخ
    draw.text((150, 415), formatted_date , font=fd, fill=(176, 232, 232, 255))

    # ── إرسال الصورة ──
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return send_file(
        buf,
        mimetype="image/png",
        as_attachment=True,
        download_name=f"شهادة-مسار-{user['full_name']}.png",
    )

@app.route("/payment", methods=["GET", "POST"])
@login_required
def payment():
    user = current_user()
    if user and user["is_paid"]:
        return redirect(url_for("success"))

    if request.method == "POST":
        card_name = request.form.get("card_name", "").strip()
        card_num  = request.form.get("card_num", "").strip()
        cvv       = request.form.get("cvv", "").strip()
        method    = request.form.get("method", "Visa")
        # normalize to match CHECK constraint: Visa, Mastercard, Fawry, instapay
        method_map = {"visa": "Visa", "mastercard": "Mastercard", "fawry": "Fawry", "instapay": "instapay"}
        method = method_map.get(method.lower(), "Visa")

        errors = []
        if not card_name:                       errors.append("اسم حامل البطاقة مطلوب")
        if len(card_num.replace(" ", "")) < 12: errors.append("رقم البطاقة غير صحيح")
        if len(cvv) < 3:                        errors.append("رمز CVV غير صحيح")

        if errors:
            for e in errors:
                flash(e, "danger")
            return redirect(url_for("payment"))

        user_id = session["user_id"]
        execute(
            "INSERT INTO payments (user_id,amount,method,status,paid_at) VALUES (?,?,?,?,?)",
            (user_id, 50.0, method, "done", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
        execute("UPDATE users SET is_paid=1 WHERE id=?", (user_id,))
        log_activity(user_id, "اشترك في المنصة", "50 جنيه")
        flash("تم الاشتراك بنجاح! مرحباً بك 🎉", "success")
        return redirect(url_for("success"))

    return render_template("payment.html")


@app.route("/success")
@login_required
def success():
    return render_template("success.html")


@app.route("/videos")
@login_required
@paid_required
def videos():
    user_id = session["user_id"]
    execute("UPDATE users SET videos_watched=videos_watched+1 WHERE id=?", (user_id,))
    log_activity(user_id, "شاهد محاضرة حصرية")
    return render_template("videos.html")


def analyze_cv_text(text: str) -> dict:
    """
    يحلل نص السيرة الذاتية ويرجع:
      - found   : الأقسام الموجودة
      - missing : الأقسام الناقصة
      - score   : نسبة الاكتمال (0-100)
      - tips    : توصيات فورية
    """
    t = text.lower()

    # ── تعريف الأقسام المطلوبة ──
    sections = {
        "الاسم والتواصل": [
            "phone", "tel", "mobile", "جوال", "هاتف",
            "email", "@", "بريد",
        ],
        "رابط LinkedIn": ["linkedin", "لينكد"],
        "الملخص المهني": [
            "ملخص", "summary", "objective", "هدف", "profile", "about",
        ],
        "الخبرة العملية": [
            "خبرة", "experience", "عمل", "worked", "شركة", "company",
            "وظيفة", "مسمى", "job",
        ],
        "التعليم": [
            "تعليم", "education", "جامعة", "university", "كلية", "college",
            "بكالوريوس", "bachelor", "دبلوم", "diploma", "ماجستير", "master",
        ],
        "المهارات": [
            "مهارات", "skills", "لغات برمجة", "python", "java", "sql",
            "excel", "word", "برمجة",
        ],
        "المشاريع أو الإنجازات": [
            "مشروع", "project", "إنجاز", "achievement", "portfolio",
        ],
        "الشهادات والدورات": [
            "شهادة", "certificate", "course", "دورة", "تدريب", "training",
        ],
    }

    found   = []
    missing = []

    for section, keywords in sections.items():
        if any(kw in t for kw in keywords):
            found.append(section)
        else:
            missing.append(section)

    total = len(sections)
    score = round(len(found) / total * 100)

    # ── توصيات بناءً على الناقص ──
    tip_map = {
        "الاسم والتواصل":        "أضف رقم هاتفك وبريدك الإلكتروني بوضوح في أعلى السيرة",
        "رابط LinkedIn":         "أضف رابط LinkedIn يعمل — يزيد مصداقيتك كثيراً",
        "الملخص المهني":         "أضف ملخصاً مهنياً من 3-4 أسطر يوضح من أنت وماذا تريد",
        "الخبرة العملية":        "أضف خبراتك العملية من الأحدث للأقدم مع أرقام وإنجازات",
        "التعليم":               "أضف قسم التعليم مع اسم الجامعة والتخصص وسنة التخرج",
        "المهارات":              "أضف قسم المهارات التقنية والناعمة بوضوح",
        "المشاريع أو الإنجازات": "أضف مشاريعك أو إنجازاتك — هذا ما يميزك عن غيرك",
        "الشهادات والدورات":     "أضف أي شهادات أو دورات أكملتها لتقوية ملفك",
    }
    tips = [tip_map[s] for s in missing[:3]]   # أهم 3 توصيات

    return {"found": found, "missing": missing, "score": score, "tips": tips}


@app.route("/cv-check", methods=["GET", "POST"])
@login_required
@paid_required
def cv_check():
    feedback = None

    if request.method == "POST":
        cv_file = request.files.get("cv_file")

        if cv_file and cv_file.filename and cv_file.filename.lower().endswith(".pdf"):
            filename = secure_filename(f"cv_{session['user_id']}_{cv_file.filename}")
            save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            cv_file.save(save_path)

            # ── استخراج النص من PDF ──
            text = ""
            try:
                import pdfplumber
                with pdfplumber.open(save_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text() or ""
                        text += page_text + "\n"
            except Exception:
                try:
                    import PyPDF2
                    with open(save_path, "rb") as f:
                        reader = PyPDF2.PdfReader(f)
                        for page in reader.pages:
                            text += (page.extract_text() or "") + "\n"
                except Exception:
                    text = ""

            if text.strip():
                result   = analyze_cv_text(text)
                feedback = result
                log_activity(session["user_id"], "حلّل سيرته الذاتية")
                flash("✅ تم تحليل سيرتك بنجاح!", "success")
            else:
                flash("⚠️ تعذّر قراءة النص من الـ PDF — تأكد أنه ليس صورة مسحوبة", "danger")
        else:
            flash("يُقبل ملفات PDF فقط", "danger")

    return render_template("cv-check.html", feedback=feedback)


@app.route("/cv-job-tips", methods=["POST"])
@login_required
def cv_job_tips():
    """توليد نصايح مخصصة بناءً على المسمى الوظيفي واسم الشركة"""
    job_title = (request.form.get("job_title") or "").strip()
    company   = (request.form.get("company") or "").strip()

    if not job_title:
        flash("من فضلك أدخل المسمى الوظيفي", "warning")
        return redirect(url_for("cv_check"))

    # نصايح مخصصة حسب كلمات مفتاحية في المسمى الوظيفي
    title_lower = job_title.lower()

    tips = []

    # تقنية / برمجة
    if any(k in title_lower for k in ["developer", "مطور", "برمج", "software", "engineer", "مهندس", "data", "بيانات", "ai", "ذكاء"]):
        tips = [
            f"📌 لوظيفة '{job_title}': ركز على المهارات التقنية كـ Python, SQL, Git في أعلى قسم المهارات",
            "🔗 أضف رابط GitHub فيه مشاريعك الحقيقية — هذا أقوى شيء لأي مطور",
            "📊 اذكر التقنيات التي تعرفها بدقة: React, Flask, TensorFlow... لا تكتب 'برمجة' فقط",
            "🏆 حاول تذكر مشروع حقيقي عملته مع نتيجة قابلة للقياس",
        ]
    # تسويق / مبيعات
    elif any(k in title_lower for k in ["marketing", "تسويق", "sales", "مبيع", "brand", "علامة", "social media", "سوشيال"]):
        tips = [
            f"📌 لوظيفة '{job_title}': اذكر حملات تسويقية نفذتها مع أرقام (نسبة تفاعل، مبيعات زادت بكم %)",
            "📱 أضف خبرتك في أدوات التسويق: Google Ads, Meta Ads, Canva, Mailchimp",
            "🎯 اكتب ملخصاً مهنياً يوضح تخصصك: B2B أم B2C؟ رقمي أم تقليدي؟",
            "📈 الأرقام هي سلاحك — 'زدت المبيعات 40%' أقوى من 'عملت في المبيعات'",
        ]
    # محاسبة / مالية
    elif any(k in title_lower for k in ["محاسب", "accounting", "مالي", "finance", "audit", "مراجع", "tax", "ضريب"]):
        tips = [
            f"📌 لوظيفة '{job_title}': اذكر البرامج التي تتقنها: Excel (Pivot), SAP, QuickBooks, الزاهر",
            "📋 وضح نوع المحاسبة: عامة، تكاليف، ضرائب، مراجعة — كل تخصص له سوق",
            "🔢 اذكر حجم الميزانيات التي تعاملت معها إن أمكن",
            "📜 شهادة CPA أو CMA تذكرها بوضوح في أعلى السيرة إن كانت موجودة",
        ]
    # موارد بشرية
    elif any(k in title_lower for k in ["hr", "موارد", "human", "توظيف", "recruit", "training", "تدريب"]):
        tips = [
            f"📌 لوظيفة '{job_title}': اذكر عدد الموظفين الذين أشرفت عليهم أو وظّفتهم",
            "💼 وضح خبرتك في: التوظيف، التدريب، الرواتب، أم شاملة؟",
            "🛠 اذكر الأنظمة التي استخدمتها: Oracle HCM, SAP HR, أو حتى Excel",
            "📊 إنجاز قابل للقياس: 'وظّفت 30 موظفاً في 3 أشهر' أفضل من 'أعمل في التوظيف'",
        ]
    # تصميم
    elif any(k in title_lower for k in ["design", "تصميم", "graphic", "جرافيك", "ui", "ux", "motion", "فيديو", "video"]):
        tips = [
            f"📌 لوظيفة '{job_title}': الـ Portfolio هو سيرتك الحقيقية — أضف رابطه بوضوح",
            "🎨 اذكر البرامج: Figma, Photoshop, Illustrator, After Effects, Premiere",
            "🖥 أضف رابط Behance أو Dribbble إن كان موجوداً",
            "✅ اذكر أنواع المشاريع: هوية بصرية، UI App، فيديو موشن...",
        ]
    # عام / غير محدد
    else:
        tips = [
            f"📌 لوظيفة '{job_title}': خصص ملخصك المهني ليذكر هذا المسمى تحديداً",
            "🔑 ابحث في إعلان الوظيفة عن الكلمات المفتاحية وأضفها في سيرتك",
            "📋 تأكد أن خبراتك مرتبة من الأحدث للأقدم",
            "💡 أضف رقماً أو إنجازاً واحداً على الأقل في كل خبرة عملية",
        ]

    # نصيحة إضافية لو فيه شركة
    if company:
        tips.append(f"🏢 بالنسبة لشركة '{company}': ابحث عنها جيداً وأضف في ملخصك جملة تُظهر أنك تعرف مجالها")

    job_tips = {
        "job_title": job_title,
        "company": company,
        "tips": tips
    }

    return render_template("cv-check.html", feedback=None, job_tips=job_tips)


# ✅ الكود الصح
@app.route("/library-pro")
@login_required
@paid_required
def library_pro():
    return render_template("library_pro.html")


@app.route("/profile")
@login_required
def profile():
    user_id    = session["user_id"]
    user       = current_user()
    if not user:
        session.clear()
        flash("انتهت جلستك، سجّل دخولك مرة أخرى", "warning")
        return redirect(url_for("auth"))
    tracks_p   = query(
        "SELECT t.name_ar, t.name_en, t.slug, ut.progress"
        " FROM user_tracks ut JOIN tracks t ON ut.track_id=t.id"
        " WHERE ut.user_id=?",
        (user_id,),
    )
    # ── عدد الاختبارات والمعدل من exam_results مباشرة ──
    exams_done_row = query(
        "SELECT COUNT(*) as cnt FROM exam_results WHERE user_id=?",
        (user_id,), one=True,
    )
    avg_score_row  = query(
        "SELECT ROUND(AVG(percent),1) as avg FROM exam_results WHERE user_id=?",
        (user_id,), one=True,
    )
    exams_done = exams_done_row["cnt"] if exams_done_row else 0
    avg_score  = (avg_score_row["avg"] or 0) if avg_score_row else 0

    # ── عدد الفيديوهات من جدول activities (كل نشاط "شاهد" = فيديو) ──
    videos_row = query(
        "SELECT COUNT(*) as cnt FROM activities WHERE user_id=? AND (description LIKE '%فيديو%' OR description LIKE '%محاضرة%' OR description LIKE '%شاهد%')",
        (user_id,), one=True,
    )
    # fallback على العمود القديم لو مفيش أنشطة مسجلة
    videos_watched = videos_row["cnt"] if (videos_row and videos_row["cnt"] > 0) else user.get("videos_watched", 0)

    # ── الأيام المتواصلة: عدد الأيام المختلفة اللي فيها نشاط ──
    streak_row = query(
        "SELECT COUNT(DISTINCT date(happened_at)) as days FROM activities WHERE user_id=?",
        (user_id,), one=True,
    )
    streak_days = streak_row["days"] if streak_row else user.get("streak_days", 0)

    # ── الشارات: محسوبة بناءً على الإنجازات الفعلية ──
    badges_earned = 0
    if videos_watched >= 1:  badges_earned += 1   # أول خطوة
    if videos_watched >= 5:  badges_earned += 1   # محب التعلم
    if exams_done    >= 1:   badges_earned += 1   # الاختبار الأول
    if avg_score     >= 90:  badges_earned += 1   # متميز
    if streak_days   >= 3:   badges_earned += 1   # منتظم
    if streak_days   >= 7:   badges_earned += 1   # لا يتوقف
    # مثالي: لو عنده امتحان 100%
    perfect_row = query(
        "SELECT COUNT(*) as cnt FROM exam_results WHERE user_id=? AND percent=100",
        (user_id,), one=True,
    )
    if perfect_row and perfect_row["cnt"] > 0: badges_earned += 1

    activities = query(
        "SELECT * FROM activities WHERE user_id=? ORDER BY happened_at DESC LIMIT 5",
        (user_id,),
    )

    # ── تفاصيل الامتحانات ──
    exam_history = query(
        """SELECT er.id, er.correct, er.total, er.percent, er.taken_at,
                  t.name_ar AS track_name, t.slug,
                  e.duration AS exam_duration_minutes
           FROM exam_results er
           LEFT JOIN tracks t ON er.track_id = t.id
           LEFT JOIN exams   e ON e.dept_id   = t.dept_id
           WHERE er.user_id = ?
           ORDER BY er.taken_at DESC""",
        (user_id,),
    )

    # ── الشهادات: الامتحانات اللي حصل فيها على 60% فأكثر ──
    certificates = [ex for ex in exam_history if ex["percent"] >= 60]

    return render_template(
        "profile.html",
        current_user=user,
        tracks_p=tracks_p,
        exams_done=exams_done,
        avg_score=avg_score,
        activities=activities,
        exam_history=exam_history,
        certificates=certificates,
        videos_watched=videos_watched,
        streak_days=streak_days,
        badges_count=badges_earned,
    )


@app.route("/upload-avatar", methods=["POST"])
@login_required
def upload_avatar():
    user_id = session["user_id"]
    file = request.files.get("avatar")
    if file and file.filename:
        ext = file.filename.rsplit(".", 1)[-1].lower()
        if ext in {"jpg", "jpeg", "png", "gif", "webp"}:
            filename = f"avatar_{user_id}.{ext}"
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            execute("UPDATE users SET avatar=? WHERE id=?", (filename, user_id))
            return jsonify({"ok": True, "filename": filename})
    return jsonify({"ok": False})


@app.route("/update-profile", methods=["POST"])
@login_required
def update_profile():
    user_id  = session["user_id"]
    full_name = request.form.get("full_name", "").strip()
    username  = request.form.get("username", "").strip()
    city      = request.form.get("city", "").strip()
    level     = request.form.get("level", "").strip()
    goal      = request.form.get("goal", "").strip()
    skills    = request.form.get("skills", "").strip()

    if not full_name:
        flash("الاسم الكامل مطلوب", "danger")
        return redirect(url_for("profile"))

    # تحقق من عدم تكرار اسم المستخدم
    if username:
        existing = query(
            "SELECT id FROM users WHERE username=? AND id!=?",
            (username, user_id), one=True
        )
        if existing:
            flash("اسم المستخدم مستخدم من قِبل شخص آخر", "danger")
            return redirect(url_for("profile"))

    execute(
        "UPDATE users SET full_name=?, username=?, city=?, level=?, goal=?, skills=? WHERE id=?",
        (full_name, username or None, city or None, level or None, goal or None, skills or None, user_id),
    )
    session["user_name"] = full_name
    log_activity(user_id, "حدّث ملفه الشخصي")
    flash("تم حفظ التغييرات بنجاح ✅", "success")
    return redirect(url_for("profile"))


@app.route("/admin")
@login_required
@admin_required
def admin_panel():
    return render_template("admin.html")


@app.route("/api/admin-stats")
@login_required
@admin_required
def api_admin_stats():
    students = query(
        "SELECT id, full_name, email, is_paid, joined_at FROM users WHERE is_admin=0 ORDER BY joined_at DESC"
    )
    total   = len(students)
    paid    = sum(1 for s in students if s["is_paid"])
    pending = total - paid
    exams_row = query("SELECT COUNT(*) as cnt FROM exam_results", one=True)
    avg_row   = query("SELECT ROUND(AVG(percent),1) as avg FROM exam_results", one=True)
    exams     = exams_row["cnt"] if exams_row else 0
    avg       = (avg_row["avg"] or 0) if avg_row else 0

    return jsonify({
        "stats":    {"total": total, "paid": paid, "pending": pending, "exams": exams, "avg": avg},
        "students": students,
    })


@app.route("/admin/toggle-payment/<int:uid>", methods=["POST"])
@login_required
@admin_required
def toggle_payment(uid):
    user = query("SELECT is_paid FROM users WHERE id=?", (uid,), one=True)
    if not user:
        return jsonify({"ok": False, "error": "user not found"}), 404
    new_val = 0 if user["is_paid"] else 1
    execute("UPDATE users SET is_paid=? WHERE id=?", (new_val, uid))
    return jsonify({"ok": True, "is_paid": new_val})


@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = query(
            "SELECT * FROM users WHERE email=? AND is_admin=1 AND password_hash=?",
            (email, hash_pw(password)), one=True
        )
        if user:
            session["user_id"]   = user["id"]
            session["user_name"] = user["full_name"]
            session["is_admin"]  = True
            log_activity(user["id"], "تسجيل دخول كمدير")
            return redirect(url_for("admin_panel"))
        return redirect(url_for("admin_login") + "?error=1")
    return render_template("admin_login.html")

@app.route("/logout")
def logout():
    user_id = session.get("user_id")
    if user_id:
        log_activity(user_id, "تسجيل خروج")
    session.clear()
    flash("تم تسجيل خروجك بنجاح", "info")
    return redirect(url_for("auth"))




# ════════════════════════════════════════════════════════
#  TRACK DETAIL PAGES — صفحات تفاصيل المسارات
# ════════════════════════════════════════════════════════

@app.route("/web-track")
def web_track():
    """صفحة تفاصيل مسار تطوير الويب — متاحة بدون تسجيل"""
    track = query("SELECT * FROM tracks WHERE slug=?", ("web",), one=True)
    user = current_user()
    tmpl = "wep_p.html" if user and user["is_paid"] else "web.html"
    return render_template(tmpl, track=track)


@app.route("/mobile-track")
def mobile_track():
    """صفحة تفاصيل مسار تطوير تطبيقات الجوال — متاحة بدون تسجيل"""
    track = query("SELECT * FROM tracks WHERE slug=?", ("mobile",), one=True)
    user = current_user()
    tmpl = "app_p.html" if user and user["is_paid"] else "app.html"
    return render_template(tmpl, track=track)


@app.route("/data-track")
def data_track():
    """صفحة تفاصيل مسار تحليل البيانات — متاحة بدون تسجيل"""
    track = query("SELECT * FROM tracks WHERE slug=?", ("data",), one=True)
    user = current_user()
    tmpl = "data_p.html" if user and user["is_paid"] else "data.html"
    return render_template(tmpl, track=track)


# ════════════════════════════════════════════════════════
#  LANGUAGE ROUTES — صفحة كل لغة
# ════════════════════════════════════════════════════════
@app.route("/lang/<slug>")
@login_required
def lang_detail(slug):
    """صفحة اختيار لغة معينة مباشرة (HTML / CSS / JS ...)"""
    lang_track_map = {
        # ويب
        "html": "web", "css": "web", "js": "web", "react": "web", "nodejs": "web",
        "php": "web", "firebase": "web",
        # جوال
        "flutter": "mobile", "java": "mobile", "react_native": "mobile",
        "kotlin": "mobile", "swift": "mobile", "xml": "mobile", "jetpack_compose": "mobile",
        "swiftui": "mobile", "uikit": "mobile", "rest_api": "mobile",
        "xcode": "mobile", "authentication": "mobile", "android_studio": "mobile",
        "local_storge": "mobile", "push_notifications": "mobile",
        # بيانات
        "python": "data", "sql": "data", "pandas": "data", "numpy": "data",
        "matplotlib": "data", "powerbi": "data", "tableau": "data",
    }
    parent_slug = lang_track_map.get(slug, slug)
    track = query("SELECT * FROM tracks WHERE slug=?", (parent_slug,), one=True)
    if not track:
        return redirect(url_for("tracks"))

    user_id = session["user_id"]
    execute(
        "INSERT OR IGNORE INTO user_tracks (user_id,track_id) VALUES (?,?)",
        (user_id, track["id"]),
    )
    return redirect(url_for("lessons", slug=slug))

# ════════════════════════════════════════════════════════
#  CHAT BOT API
# ════════════════════════════════════════════════════════
BOT_REPLIES_AR = {
    "مسار":   "مسار هي منصة تعليمية متخصصة في البرمجة والتكنولوجيا 🚀",
    "ويب":    "مسار الويب يشمل HTML وCSS وJavaScript وReact!",
    "جوال":   "مسار الجوال يشمل Flutter وReact Native وأندرويد!",
    "بيانات": "مسار البيانات يشمل Python وSQL وPower BI!",
    "مساعدة": "يمكنني مساعدتك في اختيار المسار وشرح المحتوى 😊",
    "شكرا":   "العفو! يسعدني مساعدتك دائماً 🌟",
    "مرحبا":  "أهلاً بك في مسار! كيف يمكنني مساعدتك؟ 👋",
    "اختبار": "الاختبار النهائي من أسئلة متعددة الاختيار. ادرس جيداً!",
    "دفع":    "الاشتراك بـ 50 جنيه فقط ويفتح كل المحتوى الحصري!",
}
BOT_REPLIES_EN = {
    "masar":  "Masar is an educational platform for programming 🚀",
    "web":    "Web track covers HTML, CSS, JavaScript, React!",
    "mobile": "Mobile track covers Flutter, React Native, Android!",
    "data":   "Data track covers Python, SQL, Power BI!",
    "help":   "I can help with choosing a track or explaining content 😊",
    "thanks": "You're welcome! Happy to help 🌟",
    "hello":  "Welcome to Masar! How can I help? 👋",
    "exam":   "Final exam has multiple-choice questions. Study well!",
    "pay":    "Subscribe for 50 EGP and unlock all exclusive content!",
}


@app.route("/api/chat", methods=["POST"])
def api_chat():
    data  = request.get_json(silent=True) or {}
    text  = data.get("message", "").strip()
    lang  = data.get("lang", "ar")

    if not text:
        return jsonify({"reply": "اكتب سؤالك!"})

    lower   = text.lower()
    replies = BOT_REPLIES_AR if lang == "ar" else BOT_REPLIES_EN

    for kw, reply in replies.items():
        if kw in lower:
            return jsonify({"reply": reply})

    default = ("أنا بوت مسار! اسألني عن المسارات والمحتوى 😊"
               if lang == "ar"
               else "I'm Masar Bot! Ask me about tracks and content 😊")
    return jsonify({"reply": default})


@app.route("/api/stats")
@login_required
def api_stats():
    user_id = session["user_id"]
    user    = current_user()
    if not user:
        return jsonify({"error": "المستخدم غير موجود"}), 404
    exams   = query("SELECT * FROM exam_results WHERE user_id=? ORDER BY taken_at DESC LIMIT 10", (user_id,))
    tracks  = query(
        "SELECT t.name_ar,t.slug,ut.progress FROM user_tracks ut JOIN tracks t ON ut.track_id=t.id WHERE ut.user_id=?",
        (user_id,),
    )
    return jsonify({
        "user":        {k: user[k] for k in ["full_name","email","is_paid","streak_days","videos_watched","badges","joined_at"]},
        "exams":       exams,
        "tracks":      tracks,
        "exams_count": len(exams),
        "avg_score":   round(sum(e["percent"] for e in exams) / len(exams)) if exams else 0,
    })


# ════════════════════════════════════════════════════════
#  BOOKS — الكتب
# ════════════════════════════════════════════════════════
@app.route("/api/books")
@login_required
def api_books():
    """جلب كل الكتب، مع فلترة اختيارية بـ dept_id"""
    dept_id = request.args.get("dept_id") or request.args.get("track_id")
    if dept_id:
        books = query(
            "SELECT b.*, d.name AS dept_name FROM books b "
            "LEFT JOIN departments d ON b.dept_id=d.id WHERE b.dept_id=? ORDER BY b.id DESC",
            (dept_id,),
        )
    else:
        books = query(
            "SELECT b.*, d.name AS dept_name FROM books b "
            "LEFT JOIN departments d ON b.dept_id=d.id ORDER BY b.id DESC"
        )
    return jsonify(books)


@app.route("/api/books", methods=["POST"])
@login_required
@admin_required
def api_add_book():
    """إضافة كتاب جديد (Admin فقط)"""
    data = request.get_json(silent=True) or {}
    title  = (data.get("title") or "").strip()
    if not title:
        return jsonify({"ok": False, "error": "العنوان مطلوب"}), 400
    bid = execute(
        "INSERT INTO books (title,author,dept_id,price,published_at) VALUES (?,?,?,?,?)",
        (title, data.get("author"), data.get("dept_id"), data.get("price", 0), data.get("publish_date")),
    )
    return jsonify({"ok": True, "id": bid})


@app.route("/api/books/<int:bid>", methods=["DELETE"])
@login_required
@admin_required
def api_delete_book(bid):
    execute("DELETE FROM books WHERE id=?", (bid,))
    return jsonify({"ok": True})


# ════════════════════════════════════════════════════════
#  PROGRAMMING LANGUAGES — لغات البرمجة
# ════════════════════════════════════════════════════════
@app.route("/api/languages")
@login_required
def api_languages():
    dept_id = request.args.get("dept_id") or request.args.get("track_id")
    if dept_id:
        langs = query(
            "SELECT pl.*, d.name AS dept_name FROM programming_languages pl "
            "LEFT JOIN departments d ON pl.dept_id=d.id WHERE pl.dept_id=? ORDER BY pl.name",
            (dept_id,),
        )
    else:
        langs = query(
            "SELECT pl.*, d.name AS dept_name FROM programming_languages pl "
            "LEFT JOIN departments d ON pl.dept_id=d.id ORDER BY pl.name"
        )
    return jsonify(langs)


@app.route("/api/languages", methods=["POST"])
@login_required
@admin_required
def api_add_language():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"ok": False, "error": "الاسم مطلوب"}), 400
    lid = execute(
        "INSERT OR IGNORE INTO programming_languages (name,dept_id,tools,version) VALUES (?,?,?,?)",
        (name, data.get("dept_id"), data.get("tools"), data.get("version")),
    )
    return jsonify({"ok": True, "id": lid})


# ════════════════════════════════════════════════════════
#  COURSES — الدورات التدريبية
# ════════════════════════════════════════════════════════
@app.route("/api/courses")
@login_required
def api_courses():
    dept_id = request.args.get("dept_id") or request.args.get("track_id")
    if dept_id:
        courses = query(
            "SELECT c.*, d.name AS dept_name, pl.name AS lang_name FROM lang_courses c "
            "LEFT JOIN departments d ON c.dept_id=d.id "
            "LEFT JOIN programming_languages pl ON c.prog_lang_id=pl.id "
            "WHERE c.dept_id=? ORDER BY c.id DESC",
            (dept_id,),
        )
    else:
        courses = query(
            "SELECT c.*, d.name AS dept_name, pl.name AS lang_name FROM lang_courses c "
            "LEFT JOIN departments d ON c.dept_id=d.id "
            "LEFT JOIN programming_languages pl ON c.prog_lang_id=pl.id ORDER BY c.id DESC"
        )
    return jsonify(courses)


@app.route("/api/courses", methods=["POST"])
@login_required
@admin_required
def api_add_course():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"ok": False, "error": "عنوان الدورة مطلوب"}), 400
    prog_lang_id = data.get("prog_lang_id")
    if not prog_lang_id:
        return jsonify({"ok": False, "error": "prog_lang_id مطلوب"}), 400
    cid = execute(
        "INSERT INTO lang_courses (name,prog_lang_id,dept_id,tools) VALUES (?,?,?,?)",
        (title, prog_lang_id, data.get("dept_id"), data.get("tools")),
    )
    return jsonify({"ok": True, "id": cid})


# ════════════════════════════════════════════════════════
#  EXAMS & QUESTIONS — الامتحانات والأسئلة
# ════════════════════════════════════════════════════════
@app.route("/api/exams")
@login_required
def api_exams_list():
    dept_id = request.args.get("dept_id") or request.args.get("track_id")
    if dept_id:
        exams = query(
            "SELECT e.*, d.name AS dept_name FROM exams e "
            "LEFT JOIN departments d ON e.dept_id=d.id WHERE e.dept_id=? ORDER BY e.id DESC",
            (dept_id,),
        )
    else:
        exams = query(
            "SELECT e.*, d.name AS dept_name FROM exams e "
            "LEFT JOIN departments d ON e.dept_id=d.id ORDER BY e.id DESC"
        )
    return jsonify(exams)


@app.route("/api/exams", methods=["POST"])
@login_required
@admin_required
def api_add_exam():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"ok": False, "error": "عنوان الامتحان مطلوب"}), 400
    eid = execute(
        "INSERT INTO exams (title,dept_id,duration,total_questions,max_score) VALUES (?,?,?,?,?)",
        (title, data.get("dept_id"), data.get("duration", 30),
         data.get("total_questions", 10), data.get("max_score", 100)),
    )
    return jsonify({"ok": True, "id": eid})


@app.route("/api/exams/<int:eid>/questions")
@login_required
def api_exam_questions(eid):
    questions = query(
        "SELECT * FROM questions WHERE exam_id=? ORDER BY id", (eid,)
    )
    return jsonify(questions)


@app.route("/api/exams/<int:eid>/questions", methods=["POST"])
@login_required
@admin_required
def api_add_question(eid):
    data = request.get_json(silent=True) or {}
    text   = (data.get("text") or "").strip()
    answer = (data.get("answer") or "").strip()
    if not text or not answer:
        return jsonify({"ok": False, "error": "نص السؤال والإجابة مطلوبان"}), 400
    qid = execute(
        "INSERT INTO questions (exam_id,text,type,answer) VALUES (?,?,?,?)",
        (eid, text, data.get("type", "MCQ"), answer),
    )
    return jsonify({"ok": True, "id": qid})


@app.route("/api/questions/<int:qid>", methods=["DELETE"])
@login_required
@admin_required
def api_delete_question(qid):
    execute("DELETE FROM questions WHERE id=?", (qid,))
    return jsonify({"ok": True})


# ════════════════════════════════════════════════════════
#  CVs — السير الذاتية
# ════════════════════════════════════════════════════════
@app.route("/api/cv")
@login_required
def api_get_cv():
    """جلب السيرة الذاتية للمستخدم الحالي"""
    user_id = session["user_id"]
    cv = query("SELECT * FROM cvs WHERE user_id=?", (user_id,), one=True)
    return jsonify(cv or {})


@app.route("/api/cv", methods=["POST"])
@login_required
def api_save_cv():
    """حفظ أو تحديث السيرة الذاتية"""
    user_id = session["user_id"]
    data    = request.get_json(silent=True) or {}
    existing = query("SELECT id FROM cvs WHERE user_id=?", (user_id,), one=True)
    if existing:
        execute(
            "UPDATE cvs SET title=?,skills=?,experience=?,education=?,trainings=?,last_updated=datetime('now','localtime') "
            "WHERE user_id=?",
            (data.get("title"), data.get("skills"), data.get("experience"),
             data.get("education"), data.get("trainings"), user_id),
        )
    else:
        execute(
            "INSERT INTO cvs (user_id,title,skills,experience,education,trainings) VALUES (?,?,?,?,?,?)",
            (user_id, data.get("title"), data.get("skills"),
             data.get("experience"), data.get("education"), data.get("trainings")),
        )
    log_activity(user_id, "حدّث سيرته الذاتية")
    return jsonify({"ok": True})


# ════════════════════════════════════════════════════════
#  TRAININGS — التدريبات
# ════════════════════════════════════════════════════════
@app.route("/api/trainings")
@login_required
def api_get_trainings():
    """جلب تدريبات المستخدم الحالي"""
    user_id = session["user_id"]
    dept    = request.args.get("dept")   # commerce / cs / other
    if dept:
        rows = query(
            "SELECT * FROM trainings WHERE user_id=? AND dept=? ORDER BY start_date DESC",
            (user_id, dept),
        )
    else:
        rows = query(
            "SELECT * FROM trainings WHERE user_id=? ORDER BY start_date DESC",
            (user_id,),
        )
    return jsonify(rows)


@app.route("/api/trainings", methods=["POST"])
@login_required
def api_add_training():
    """إضافة تدريب جديد للمستخدم الحالي"""
    user_id = session["user_id"]
    data    = request.get_json(silent=True) or {}
    title   = (data.get("title") or "").strip()
    if not title:
        return jsonify({"ok": False, "error": "عنوان التدريب مطلوب"}), 400
    dept = data.get("dept", "other")
    if dept not in ("commerce", "cs", "other"):
        dept = "other"
    tid = execute(
        "INSERT INTO trainings (user_id,title,organization,dept,start_date,end_date,description,certificate_url) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (user_id, title, data.get("organization"), dept,
         data.get("start_date"), data.get("end_date"),
         data.get("description"), data.get("certificate_url")),
    )
    log_activity(user_id, f"أضاف تدريباً: {title}")
    return jsonify({"ok": True, "id": tid})


@app.route("/api/trainings/<int:tid>", methods=["PUT"])
@login_required
def api_update_training(tid):
    """تعديل تدريب موجود (المستخدم نفسه أو الأدمن)"""
    user_id = session["user_id"]
    row     = query("SELECT user_id FROM trainings WHERE id=?", (tid,), one=True)
    if not row:
        return jsonify({"ok": False, "error": "التدريب غير موجود"}), 404
    user = current_user()
    if row["user_id"] != user_id and not user["is_admin"]:
        return jsonify({"ok": False, "error": "غير مصرح"}), 403
    data = request.get_json(silent=True) or {}
    dept = data.get("dept", "other")
    if dept not in ("commerce", "cs", "other"):
        dept = "other"
    execute(
        "UPDATE trainings SET title=?,organization=?,dept=?,start_date=?,end_date=?,description=?,certificate_url=? "
        "WHERE id=?",
        (data.get("title"), data.get("organization"), dept,
         data.get("start_date"), data.get("end_date"),
         data.get("description"), data.get("certificate_url"), tid),
    )
    return jsonify({"ok": True})


@app.route("/api/trainings/<int:tid>", methods=["DELETE"])
@login_required
def api_delete_training(tid):
    """حذف تدريب (المستخدم نفسه أو الأدمن)"""
    user_id = session["user_id"]
    row     = query("SELECT user_id FROM trainings WHERE id=?", (tid,), one=True)
    if not row:
        return jsonify({"ok": False, "error": "التدريب غير موجود"}), 404
    user = current_user()
    if row["user_id"] != user_id and not user["is_admin"]:
        return jsonify({"ok": False, "error": "غير مصرح"}), 403
    execute("DELETE FROM trainings WHERE id=?", (tid,))
    return jsonify({"ok": True})


# ════════════════════════════════════════════════════════
#  RUN
# ════════════════════════════════════════════════════════
app = app
if __name__ == "__main__":
    with app.app_context():
        init_db()
        migrate_db()
    print("=" * 55)
    print("  🚀 Masar Platform — Flask Server")
    print("  http://127.0.0.1:5000")
    print("  Admin: Admin@masar.com/  Admin@1234")
    print("  Student: nadazizo895@gmail.com  /  Test@1234")
    print("=" * 55)
    app.run(debug=True, host="0.0.0.0", port=5000)