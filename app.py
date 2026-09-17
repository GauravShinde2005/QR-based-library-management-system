from flask import Flask, request, redirect, session, render_template_string, flash
import sqlite3
import qrcode
import os
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
app.secret_key = "qr-library-secret-2026"

DATABASE = "library.db"
QR_FOLDER = "static/qr"

os.makedirs(QR_FOLDER, exist_ok=True)


# =========================================================
# DATABASE
# =========================================================

def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db


def init_db():

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            category TEXT,
            isbn TEXT,
            quantity INTEGER NOT NULL,
            available INTEGER NOT NULL,
            qr_code TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            roll_no TEXT UNIQUE NOT NULL,
            email TEXT,
            phone TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            issue_date TEXT NOT NULL,
            due_date TEXT NOT NULL,
            return_date TEXT,
            status TEXT NOT NULL
        )
    """)

    admin = cur.execute(
        "SELECT * FROM admin WHERE username = ?",
        ("admin",)
    ).fetchone()

    if admin is None:
        cur.execute(
            "INSERT INTO admin(username,password) VALUES(?,?)",
            ("admin", "admin123")
        )

    db.commit()
    db.close()


# =========================================================
# LOGIN
# =========================================================

def login_required(func):

    @wraps(func)
    def wrapper(*args, **kwargs):

        if "admin" not in session:
            return redirect("/")

        return func(*args, **kwargs)

    return wrapper


# =========================================================
# MAIN HTML
# =========================================================

HTML = """

<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>QR Library Management System</title>


<style>

/* =====================================================
   RESET
   ===================================================== */

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

html {
    scroll-behavior: smooth;
}

body {

    font-family:
    Arial,
    Helvetica,
    sans-serif;

    background:
    linear-gradient(
        135deg,
        #f8fafc,
        #eef4ff
    );

    color: #111827;

    min-height: 100vh;
}


/* =====================================================
   ANIMATIONS
   ===================================================== */

@keyframes fadeUp {

    from {
        opacity: 0;
        transform: translateY(25px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}


@keyframes fadeLeft {

    from {
        opacity: 0;
        transform: translateX(-30px);
    }

    to {
        opacity: 1;
        transform: translateX(0);
    }
}


@keyframes zoomIn {

    from {
        opacity: 0;
        transform: scale(.88);
    }

    to {
        opacity: 1;
        transform: scale(1);
    }
}


@keyframes floating {

    0%,100% {
        transform: translateY(0);
    }

    50% {
        transform: translateY(-8px);
    }
}


@keyframes pulse {

    0% {
        box-shadow:
        0 0 0 0
        rgba(59,130,246,.4);
    }

    70% {
        box-shadow:
        0 0 0 14px
        rgba(59,130,246,0);
    }

    100% {
        box-shadow:
        0 0 0 0
        rgba(59,130,246,0);
    }
}


@keyframes gradientMove {

    0% {
        background-position: 0% 50%;
    }

    50% {
        background-position: 100% 50%;
    }

    100% {
        background-position: 0% 50%;
    }
}


.fade {
    animation:
    fadeUp .6s ease both;
}


/* =====================================================
   SIDEBAR
   ===================================================== */

.sidebar {

    position: fixed;

    top: 0;
    left: 0;

    width: 250px;

    height: 100vh;

    background:
    linear-gradient(
        180deg,
        #0f172a,
        #172554
    );

    color: white;

    padding: 22px 15px;

    z-index: 100;

    box-shadow:
    8px 0 30px
    rgba(0,0,0,.12);

    animation:
    fadeLeft .7s ease both;

    overflow-y: auto;
}


.logo {

    font-size: 22px;

    font-weight: 800;

    padding: 12px;

    margin-bottom: 28px;

    letter-spacing: -.5px;
}


.logo span {
    color: #60a5fa;
}


.menu-title {

    font-size: 10px;

    font-weight: bold;

    letter-spacing: 1.5px;

    color: #94a3b8;

    margin:
    22px 10px 8px;
}


.sidebar a {

    display: flex;

    align-items: center;

    gap: 10px;

    color: #cbd5e1;

    text-decoration: none;

    padding: 12px 13px;

    margin: 5px 0;

    border-radius: 9px;

    font-size: 14px;

    transition:
    all .25s ease;
}


.sidebar a:hover {

    color: white;

    background:
    linear-gradient(
        90deg,
        #2563eb,
        #3b82f6
    );

    transform:
    translateX(6px);

    box-shadow:
    0 8px 20px
    rgba(37,99,235,.25);
}


/* =====================================================
   MAIN
   ===================================================== */

.main {

    margin-left: 250px;

    min-height: 100vh;
}


/* =====================================================
   TOP BAR
   ===================================================== */

.topbar {

    height: 72px;

    display: flex;

    justify-content:
    space-between;

    align-items: center;

    padding:
    0 32px;

    background:
    rgba(255,255,255,.92);

    backdrop-filter:
    blur(15px);

    border-bottom:
    1px solid #e5e7eb;

    position:
    sticky;

    top: 0;

    z-index: 50;
}


.topbar h2 {

    font-size: 20px;
}


.profile {

    padding:
    9px 16px;

    border-radius:
    30px;

    background:
    #eff6ff;

    color:
    #2563eb;

    font-weight:
    bold;

    font-size:
    13px;

    animation:
    pulse 2.5s infinite;
}


/* =====================================================
   CONTENT
   ===================================================== */

.content {

    padding:
    32px;

    animation:
    fadeUp .6s ease both;
}


.page-title {

    margin-bottom:
    25px;
}


.page-title h1 {

    font-size:
    29px;

    font-weight:
    800;
}


.page-title p {

    color:
    #64748b;

    margin-top:
    7px;

    font-size:
    14px;
}


/* =====================================================
   DASHBOARD CARDS
   ===================================================== */

.cards {

    display:
    grid;

    grid-template-columns:
    repeat(4,1fr);

    gap:
    20px;
}


.card {

    background:
    rgba(255,255,255,.96);

    border:
    1px solid #e5e7eb;

    padding:
    23px;

    border-radius:
    15px;

    position:
    relative;

    overflow:
    hidden;

    transition:
    all .3s ease;

    animation:
    zoomIn .55s ease both;
}


.card:nth-child(1) {
    animation-delay: .05s;
}

.card:nth-child(2) {
    animation-delay: .12s;
}

.card:nth-child(3) {
    animation-delay: .19s;
}

.card:nth-child(4) {
    animation-delay: .26s;
}


.card::before {

    content: "";

    position:
    absolute;

    left: 0;
    top: 0;

    width: 100%;
    height: 3px;

    background:
    linear-gradient(
        90deg,
        #2563eb,
        #60a5fa
    );

    transform:
    scaleX(0);

    transform-origin:
    left;

    transition:
    transform .35s ease;
}


.card:hover {

    transform:
    translateY(-8px);

    box-shadow:
    0 18px 40px
    rgba(37,99,235,.13);

    border-color:
    #bfdbfe;
}


.card:hover::before {
    transform: scaleX(1);
}


.card-icon {

    font-size:
    30px;

    animation:
    floating 3s ease-in-out infinite;
}


.card h2 {

    font-size:
    31px;

    margin-top:
    12px;
}


.card p {

    color:
    #64748b;

    margin-top:
    5px;
}


/* =====================================================
   QUICK ACTIONS
   ===================================================== */

.actions {

    display:
    grid;

    grid-template-columns:
    repeat(4,1fr);

    gap:
    15px;

    margin-top:
    25px;
}


.action {

    background:
    white;

    border:
    1px solid #e5e7eb;

    padding:
    20px;

    border-radius:
    13px;

    color:
    #111827;

    text-decoration:
    none;

    transition:
    all .3s ease;
}


.action:hover {

    transform:
    translateY(-6px);

    border-color:
    #93c5fd;

    box-shadow:
    0 15px 30px
    rgba(37,99,235,.1);
}


.action-icon {

    font-size:
    29px;

    margin-bottom:
    8px;

    transition:
    transform .3s ease;
}


.action:hover .action-icon {

    transform:
    scale(1.2)
    rotate(-5deg);
}


.action b {
    display: block;
    margin-bottom: 5px;
}


.action small {
    color: #64748b;
}


/* =====================================================
   TABLE
   ===================================================== */

.table-box {

    background:
    rgba(255,255,255,.97);

    border:
    1px solid #e5e7eb;

    border-radius:
    15px;

    padding:
    22px;

    overflow-x:
    auto;

    box-shadow:
    0 8px 25px
    rgba(15,23,42,.04);

    animation:
    fadeUp .6s ease both;
}


table {

    width:
    100%;

    border-collapse:
    collapse;
}


th {

    text-align:
    left;

    padding:
    14px;

    background:
    #f8fafc;

    color:
    #475569;

    font-size:
    12px;

    text-transform:
    uppercase;
}


td {

    padding:
    14px;

    border-top:
    1px solid #edf2f7;

    font-size:
    13px;
}


tr {

    transition:
    all .2s ease;
}


tr:hover td {

    background:
    #f8fbff;
}


/* =====================================================
   BUTTONS
   ===================================================== */

.btn {

    display:
    inline-flex;

    align-items:
    center;

    justify-content:
    center;

    gap:
    5px;

    padding:
    10px 15px;

    border:
    none;

    border-radius:
    8px;

    text-decoration:
    none;

    cursor:
    pointer;

    font-size:
    13px;

    font-weight:
    700;

    transition:
    all .25s ease;
}


.btn:hover {

    transform:
    translateY(-2px);

    box-shadow:
    0 8px 18px
    rgba(0,0,0,.12);
}


.primary {

    color:
    white;

    background:
    linear-gradient(
        135deg,
        #2563eb,
        #3b82f6
    );
}


.primary:hover {

    background:
    linear-gradient(
        135deg,
        #1d4ed8,
        #2563eb
    );
}


.dark {

    background:
    #111827;

    color:
    white;
}


.success {

    background:
    #dcfce7;

    color:
    #15803d;
}


.danger {

    background:
    #fee2e2;

    color:
    #dc2626;
}


/* =====================================================
   FORMS
   ===================================================== */

.form-box {

    max-width:
    680px;

    background:
    rgba(255,255,255,.97);

    padding:
    28px;

    border:
    1px solid #e5e7eb;

    border-radius:
    15px;

    box-shadow:
    0 12px 35px
    rgba(15,23,42,.06);

    animation:
    zoomIn .55s ease both;
}


.form-group {

    margin-bottom:
    19px;
}


label {

    display:
    block;

    margin-bottom:
    7px;

    font-weight:
    700;

    font-size:
    13px;
}


input,
select {

    width:
    100%;

    padding:
    12px 13px;

    border:
    1px solid #d1d5db;

    border-radius:
    8px;

    font-size:
    14px;

    transition:
    all .2s ease;
}


input:focus,
select:focus {

    outline:
    none;

    border-color:
    #3b82f6;

    box-shadow:
    0 0 0 4px
    rgba(59,130,246,.1);

    transform:
    translateY(-1px);
}


/* =====================================================
   SEARCH
   ===================================================== */

.search-bar {

    display:
    flex;

    gap:
    10px;

    margin-bottom:
    20px;
}


.search-bar input {

    max-width:
    450px;
}


/* =====================================================
   QR
   ===================================================== */

.qr {

    width:
    78px;

    height:
    78px;

    padding:
    4px;

    background:
    white;

    border:
    1px solid #e5e7eb;

    border-radius:
    8px;

    transition:
    all .3s ease;
}


.qr:hover {

    transform:
    scale(1.15)
    rotate(2deg);

    box-shadow:
    0 10px 25px
    rgba(0,0,0,.15);
}


/* =====================================================
   ALERT
   ===================================================== */

.alert {

    margin:
    18px 32px 0;

    padding:
    13px 18px;

    border-radius:
    9px;

    background:
    #dcfce7;

    color:
    #166534;

    border:
    1px solid #bbf7d0;

    animation:
    fadeUp .5s ease both;
}


/* =====================================================
   LOGIN PAGE
   ===================================================== */

.login-page {

    min-height:
    100vh;

    display:
    flex;

    align-items:
    center;

    justify-content:
    center;

    padding:
    20px;

    position:
    relative;

    overflow:
    hidden;

    background:

    linear-gradient(
        rgba(5,15,30,.68),
        rgba(5,15,30,.72)
    ),

    url("https://images.unsplash.com/photo-1521587760476-6c12a4b040da?auto=format&fit=crop&w=2000&q=85");

    background-size:
    cover;

    background-position:
    center;

    animation:
    gradientMove 12s ease infinite;
}


/* moving light */

.login-page::before {

    content:
    "";

    position:
    absolute;

    width:
    350px;

    height:
    350px;

    border-radius:
    50%;

    background:
    rgba(59,130,246,.15);

    top:
    -100px;

    left:
    -100px;

    filter:
    blur(5px);

    animation:
    floating 5s ease-in-out infinite;
}


.login-page::after {

    content:
    "";

    position:
    absolute;

    width:
    280px;

    height:
    280px;

    border-radius:
    50%;

    background:
    rgba(96,165,250,.13);

    bottom:
    -80px;

    right:
    -80px;

    filter:
    blur(5px);

    animation:
    floating 6s ease-in-out infinite;
}


/* =====================================================
   LOGIN BOX
   ===================================================== */

.login-box {

    width:
    420px;

    max-width:
    100%;

    padding:
    40px;

    background:
    rgba(255,255,255,.96);

    border:
    1px solid
    rgba(255,255,255,.7);

    border-radius:
    20px;

    box-shadow:
    0 30px 90px
    rgba(0,0,0,.35);

    position:
    relative;

    z-index:
    2;

    animation:
    zoomIn .8s ease both;
}


.login-logo {

    text-align:
    center;

    font-size:
    29px;

    font-weight:
    850;

    margin-bottom:
    10px;
}


.login-logo span {
    color:
    #2563eb;
}


.login-subtitle {

    text-align:
    center;

    color:
    #64748b;

    font-size:
    13px;

    margin-bottom:
    28px;
}


.login-box button {

    width:
    100%;

    padding:
    13px;

    border:
    none;

    border-radius:
    9px;

    color:
    white;

    background:
    linear-gradient(
        135deg,
        #2563eb,
        #3b82f6
    );

    font-size:
    15px;

    font-weight:
    700;

    cursor:
    pointer;

    transition:
    all .3s ease;
}


.login-box button:hover {

    transform:
    translateY(-3px);

    box-shadow:
    0 12px 25px
    rgba(37,99,235,.3);
}


.login-info {

    text-align:
    center;

    color:
    #64748b;

    font-size:
    12px;

    line-height:
    1.7;

    margin-top:
    20px;
}


/* =====================================================
   SCANNER
   ===================================================== */

.scanner {

    max-width:
    680px;

    padding:
    28px;

    background:
    white;

    border:
    1px solid #e5e7eb;

    border-radius:
    15px;

    box-shadow:
    0 12px 35px
    rgba(0,0,0,.06);

    animation:
    zoomIn .55s ease both;
}


#reader {

    width:
    100%;

    margin-top:
    20px;

    border-radius:
    12px;

    overflow:
    hidden;
}


/* =====================================================
   BOOK DETAILS
   ===================================================== */

.book-card {

    max-width:
    680px;

    padding:
    30px;

    background:
    white;

    border:
    1px solid #e5e7eb;

    border-radius:
    15px;

    box-shadow:
    0 12px 35px
    rgba(0,0,0,.05);

    animation:
    zoomIn .55s ease both;
}


.book-card h2 {

    font-size:
    25px;

    margin-bottom:
    20px;
}


.book-row {

    padding:
    14px 0;

    border-bottom:
    1px solid #edf2f7;

    font-size:
    14px;
}


/* =====================================================
   MOBILE
   ===================================================== */

@media(max-width:1100px) {

    .cards {

        grid-template-columns:
        repeat(2,1fr);
    }

    .actions {

        grid-template-columns:
        repeat(2,1fr);
    }

}


@media(max-width:700px) {

    .sidebar {

        position:
        relative;

        width:
        100%;

        height:
        auto;
    }

    .main {

        margin-left:
        0;
    }

    .cards,
    .actions {

        grid-template-columns:
        1fr;
    }

    .content {

        padding:
        18px;
    }

    .topbar {

        padding:
        0 18px;
    }

    .topbar h2 {

        font-size:
        17px;
    }

    .alert {

        margin:
        15px 18px 0;
    }

    .search-bar {

        flex-direction:
        column;
    }

    .search-bar input {

        max-width:
        100%;
    }

    .login-box {

        padding:
        30px 22px;
    }

}

</style>

</head>


<body>


{% if session.get("admin") %}

<div class="sidebar">

    <div class="logo">
        📚 <span>QR</span> Library
    </div>


    <div class="menu-title">
        MAIN MENU
    </div>

    <a href="/dashboard">
        🏠 Dashboard
    </a>

    <a href="/books">
        📚 Books
    </a>

    <a href="/students">
        👨‍🎓 Students
    </a>


    <div class="menu-title">
        LIBRARY
    </div>

    <a href="/issue">
        📖 Issue Book
    </a>

    <a href="/returns">
        ↩️ Return Book
    </a>

    <a href="/scan">
        📷 Scan QR
    </a>

    <a href="/history">
        📋 History
    </a>


    <div class="menu-title">
        ACCOUNT
    </div>

    <a href="/logout">
        🚪 Logout
    </a>

</div>


<div class="main">

<div class="topbar">

    <h2>
        QR Library Management
    </h2>

    <div class="profile">
        👤 Admin
    </div>

</div>

{% endif %}


{% with messages = get_flashed_messages() %}

{% for message in messages %}

<div class="alert">
    ✅ {{ message }}
</div>

{% endfor %}

{% endwith %}


{% if session.get("admin") %}

<div class="content">

{{ content|safe }}

</div>

</div>

{% else %}

{{ content|safe }}

{% endif %}


</body>

</html>
"""


def render_page(content):

    return render_template_string(
        HTML,
        content=content
    )


# =========================================================
# LOGIN
# =========================================================

@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username", "")
        password = request.form.get("password", "")

        db = get_db()

        user = db.execute("""
            SELECT *
            FROM admin
            WHERE username=?
            AND password=?
        """, (username, password)).fetchone()

        db.close()

        if user:

            session["admin"] = username

            return redirect("/dashboard")

        return render_page("""

        <div class="login-page">

            <div class="login-box">

                <div class="login-logo">
                    📚 <span>QR Library</span>
                </div>

                <div class="login-subtitle">
                    Library Management System
                </div>

                <p style="
                    text-align:center;
                    color:#dc2626;
                    margin-bottom:18px;
                    font-size:13px;
                ">
                    ❌ Invalid username or password
                </p>


                <form method="POST">

                    <div class="form-group">

                        <label>
                            Username
                        </label>

                        <input
                            name="username"
                            placeholder="Enter username"
                            required>

                    </div>


                    <div class="form-group">

                        <label>
                            Password
                        </label>

                        <input
                            type="password"
                            name="password"
                            placeholder="Enter password"
                            required>

                    </div>


                    <button type="submit">
                        Login →
                    </button>

                </form>


                <div class="login-info">

                    Default Login<br>

                    Username:
                    <b>admin</b><br>

                    Password:
                    <b>admin123</b>

                </div>

            </div>

        </div>

        """)


    return render_page("""

    <div class="login-page">

        <div class="login-box">

            <div class="login-logo">
                📚 <span>QR Library</span>
            </div>

            <div class="login-subtitle">
                Modern Library Management System
            </div>


            <form method="POST">

                <div class="form-group">

                    <label>
                        Username
                    </label>

                    <input
                        name="username"
                        placeholder="Enter username"
                        required>

                </div>


                <div class="form-group">

                    <label>
                        Password
                    </label>

                    <input
                        type="password"
                        name="password"
                        placeholder="Enter password"
                        required>

                </div>


                <button type="submit">
                    Login →
                </button>

            </form>


            <div class="login-info">

                Default Login<br>

                Username:
                <b>admin</b><br>

                Password:
                <b>admin123</b>

            </div>

        </div>

    </div>

    """)


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
@login_required
def dashboard():

    db = get_db()

    total_books = db.execute(
        "SELECT COUNT(*) FROM books"
    ).fetchone()[0]

    total_students = db.execute(
        "SELECT COUNT(*) FROM students"
    ).fetchone()[0]

    issued = db.execute(
        "SELECT COUNT(*) FROM transactions WHERE status='Issued'"
    ).fetchone()[0]

    returned = db.execute(
        "SELECT COUNT(*) FROM transactions WHERE status='Returned'"
    ).fetchone()[0]


    recent = db.execute("""
        SELECT
            transactions.*,
            books.title,
            students.name

        FROM transactions

        JOIN books
        ON transactions.book_id = books.id

        JOIN students
        ON transactions.student_id = students.id

        ORDER BY transactions.id DESC

        LIMIT 5

    """).fetchall()

    db.close()


    rows = ""

    for item in recent:

        if item["status"] == "Returned":

            status = """
                <span class="btn success">
                    Returned
                </span>
            """

        else:

            status = """
                <span class="btn"
                style="
                    background:#dbeafe;
                    color:#1d4ed8;
                ">
                    Issued
                </span>
            """


        rows += f"""

        <tr>

            <td>
                <b>{item["title"]}</b>
            </td>

            <td>
                {item["name"]}
            </td>

            <td>
                {item["issue_date"]}
            </td>

            <td>
                {status}
            </td>

        </tr>

        """


    content = f"""

    <div class="page-title">

        <h1>
            Dashboard
        </h1>

        <p>
            Welcome back, Admin!
            Here's your library overview.
        </p>

    </div>


    <div class="cards">


        <div class="card">

            <div class="card-icon">
                📚
            </div>

            <h2>
                {total_books}
            </h2>

            <p>
                Total Books
            </p>

        </div>


        <div class="card">

            <div class="card-icon">
                👨‍🎓
            </div>

            <h2>
                {total_students}
            </h2>

            <p>
                Total Students
            </p>

        </div>


        <div class="card">

            <div class="card-icon">
                📖
            </div>

            <h2>
                {issued}
            </h2>

            <p>
                Issued Books
            </p>

        </div>


        <div class="card">

            <div class="card-icon">
                ↩️
            </div>

            <h2>
                {returned}
            </h2>

            <p>
                Returned Books
            </p>

        </div>

    </div>


    <div class="actions">


        <a
            class="action"
            href="/books/add">

            <div class="action-icon">
                ➕
            </div>

            <b>
                Add New Book
            </b>

            <small>
                Add book and generate QR
            </small>

        </a>


        <a
            class="action"
            href="/students/add">

            <div class="action-icon">
                👨‍🎓
            </div>

            <b>
                Add Student
            </b>

            <small>
                Register library student
            </small>

        </a>


        <a
            class="action"
            href="/issue">

            <div class="action-icon">
                📖
            </div>

            <b>
                Issue Book
            </b>

            <small>
                Issue a book
            </small>

        </a>


        <a
            class="action"
            href="/scan">

            <div class="action-icon">
                📷
            </div>

            <b>
                Scan QR
            </b>

            <small>
                Scan book QR code
            </small>

        </a>


    </div>


    <br>


    <div class="table-box">

        <h2 style="margin-bottom:15px">
            Recent Transactions
        </h2>


        <table>

            <tr>

                <th>
                    Book
                </th>

                <th>
                    Student
                </th>

                <th>
                    Issue Date
                </th>

                <th>
                    Status
                </th>

            </tr>

            {rows}

        </table>

    </div>

    """

    return render_page(content)


# =========================================================
# BOOKS
# =========================================================

@app.route("/books")
@login_required
def books():

    search = request.args.get(
        "search",
        ""
    )

    db = get_db()

    if search:

        data = db.execute("""
            SELECT *
            FROM books

            WHERE title LIKE ?
            OR author LIKE ?
            OR category LIKE ?
            OR isbn LIKE ?

            ORDER BY id DESC

        """, (
            f"%{search}%",
            f"%{search}%",
            f"%{search}%",
            f"%{search}%"
        )).fetchall()

    else:

        data = db.execute("""
            SELECT *
            FROM books
            ORDER BY id DESC
        """).fetchall()

    db.close()


    rows = ""

    for book in data:

        rows += f"""

        <tr>

            <td>
                #{book["id"]}
            </td>

            <td>

                <img
                    class="qr"
                    src="/static/qr/{book["qr_code"]}">

            </td>

            <td>
                <b>
                    {book["title"]}
                </b>
            </td>

            <td>
                {book["author"]}
            </td>

            <td>
                {book["category"] or "-"}
            </td>

            <td>
                {book["quantity"]}
            </td>

            <td>
                <b style="color:#15803d">
                    {book["available"]}
                </b>
            </td>

            <td>

                <a
                    class="btn danger"
                    href="/books/delete/{book["id"]}"
                    onclick="
                    return confirm('Delete this book?')
                    ">

                    Delete

                </a>

            </td>

        </tr>

        """


    content = f"""

    <div class="page-title">

        <h1>
            📚 Books
        </h1>

        <p>
            Manage books and generated QR codes.
        </p>

    </div>


    <a
        class="btn primary"
        href="/books/add">

        ➕ Add New Book

    </a>


    <br><br>


    <form
        class="search-bar"
        method="GET">

        <input
            name="search"
            value="{search}"
            placeholder="Search books...">

        <button
            class="btn dark">

            🔍 Search

        </button>

    </form>


    <div class="table-box">

        <table>

            <tr>

                <th>ID</th>
                <th>QR</th>
                <th>Book</th>
                <th>Author</th>
                <th>Category</th>
                <th>Total</th>
                <th>Available</th>
                <th>Action</th>

            </tr>

            {rows}

        </table>

    </div>

    """

    return render_page(content)


# =========================================================
# ADD BOOK
# =========================================================

@app.route(
    "/books/add",
    methods=["GET", "POST"]
)
@login_required
def add_book():

    if request.method == "POST":

        title = request.form["title"]
        author = request.form["author"]
        category = request.form["category"]
        isbn = request.form["isbn"]

        quantity = int(
            request.form["quantity"]
        )


        db = get_db()

        cur = db.cursor()


        cur.execute("""
            INSERT INTO books
            (
                title,
                author,
                category,
                isbn,
                quantity,
                available
            )

            VALUES(?,?,?,?,?,?)

        """, (
            title,
            author,
            category,
            isbn,
            quantity,
            quantity
        ))


        book_id = cur.lastrowid


        # QR contains local book URL
        qr_data = (
            f"http://127.0.0.1:5000/book/{book_id}"
        )


        qr = qrcode.make(qr_data)


        filename = (
            f"book_{book_id}.png"
        )


        qr.save(
            os.path.join(
                QR_FOLDER,
                filename
            )
        )


        cur.execute("""
            UPDATE books
            SET qr_code=?
            WHERE id=?
        """, (
            filename,
            book_id
        ))


        db.commit()
        db.close()


        flash(
            "Book added and QR generated successfully!"
        )

        return redirect("/books")


    content = """

    <div class="page-title">

        <h1>
            ➕ Add New Book
        </h1>

        <p>
            Enter book details and generate QR automatically.
        </p>

    </div>


    <div class="form-box">

        <form method="POST">


            <div class="form-group">

                <label>
                    Book Title *
                </label>

                <input
                    name="title"
                    placeholder="Enter book title"
                    required>

            </div>


            <div class="form-group">

                <label>
                    Author *
                </label>

                <input
                    name="author"
                    placeholder="Enter author name"
                    required>

            </div>


            <div class="form-group">

                <label>
                    Category
                </label>

                <input
                    name="category"
                    placeholder="Programming / Science / Novel">

            </div>


            <div class="form-group">

                <label>
                    ISBN
                </label>

                <input
                    name="isbn"
                    placeholder="Enter ISBN">

            </div>


            <div class="form-group">

                <label>
                    Quantity *
                </label>

                <input
                    type="number"
                    name="quantity"
                    value="1"
                    min="1"
                    required>

            </div>


            <button
                class="btn primary">

                📚 Add Book & Generate QR

            </button>


            <a
                href="/books"
                class="btn dark">

                Cancel

            </a>

        </form>

    </div>

    """

    return render_page(content)


# =========================================================
# DELETE BOOK
# =========================================================

@app.route(
    "/books/delete/<int:id>"
)
@login_required
def delete_book(id):

    db = get_db()

    book = db.execute(
        "SELECT * FROM books WHERE id=?",
        (id,)
    ).fetchone()


    if book:

        if book["qr_code"]:

            qr_path = os.path.join(
                QR_FOLDER,
                book["qr_code"]
            )

            if os.path.exists(qr_path):

                os.remove(qr_path)


        db.execute(
            "DELETE FROM books WHERE id=?",
            (id,)
        )

        db.commit()


    db.close()


    flash(
        "Book deleted successfully!"
    )

    return redirect("/books")


# =========================================================
# STUDENTS
# =========================================================

@app.route("/students")
@login_required
def students():

    db = get_db()

    data = db.execute("""
        SELECT *
        FROM students
        ORDER BY id DESC
    """).fetchall()

    db.close()


    rows = ""

    for student in data:

        rows += f"""

        <tr>

            <td>
                #{student["id"]}
            </td>

            <td>
                <b>
                    {student["name"]}
                </b>
            </td>

            <td>
                {student["roll_no"]}
            </td>

            <td>
                {student["email"] or "-"}
            </td>

            <td>
                {student["phone"] or "-"}
            </td>

        </tr>

        """


    content = f"""

    <div class="page-title">

        <h1>
            👨‍🎓 Students
        </h1>

        <p>
            Manage registered students.
        </p>

    </div>


    <a
        class="btn primary"
        href="/students/add">

        ➕ Add Student

    </a>


    <br><br>


    <div class="table-box">

        <table>

            <tr>

                <th>ID</th>
                <th>Name</th>
                <th>Roll Number</th>
                <th>Email</th>
                <th>Phone</th>

            </tr>

            {rows}

        </table>

    </div>

    """

    return render_page(content)


# =========================================================
# ADD STUDENT
# =========================================================

@app.route(
    "/students/add",
    methods=["GET", "POST"]
)
@login_required
def add_student():

    if request.method == "POST":

        name = request.form["name"]
        roll = request.form["roll"]
        email = request.form["email"]
        phone = request.form["phone"]


        db = get_db()


        try:

            db.execute("""
                INSERT INTO students
                (
                    name,
                    roll_no,
                    email,
                    phone
                )

                VALUES(?,?,?,?)

            """, (
                name,
                roll,
                email,
                phone
            ))


            db.commit()

            flash(
                "Student registered successfully!"
            )


        except sqlite3.IntegrityError:

            flash(
                "This roll number already exists!"
            )


        db.close()

        return redirect("/students")


    content = """

    <div class="page-title">

        <h1>
            👨‍🎓 Add Student
        </h1>

        <p>
            Register a student.
        </p>

    </div>


    <div class="form-box">

        <form method="POST">


            <div class="form-group">

                <label>
                    Student Name *
                </label>

                <input
                    name="name"
                    placeholder="Enter student name"
                    required>

            </div>


            <div class="form-group">

                <label>
                    Roll Number *
                </label>

                <input
                    name="roll"
                    placeholder="Enter roll number"
                    required>

            </div>


            <div class="form-group">

                <label>
                    Email
                </label>

                <input
                    type="email"
                    name="email"
                    placeholder="student@example.com">

            </div>


            <div class="form-group">

                <label>
                    Phone
                </label>

                <input
                    name="phone"
                    placeholder="Enter phone number">

            </div>


            <button
                class="btn primary">

                👨‍🎓 Register Student

            </button>

        </form>

    </div>

    """

    return render_page(content)


# =========================================================
# ISSUE BOOK
# =========================================================

@app.route(
    "/issue",
    methods=["GET", "POST"]
)
@login_required
def issue_book():

    db = get_db()


    if request.method == "POST":

        book_id = request.form["book"]
        student_id = request.form["student"]


        book = db.execute(
            "SELECT * FROM books WHERE id=?",
            (book_id,)
        ).fetchone()


        if not book:

            db.close()

            flash(
                "Book not found!"
            )

            return redirect("/issue")


        if book["available"] <= 0:

            db.close()

            flash(
                "Book is not available!"
            )

            return redirect("/issue")


        issue_date = datetime.now().strftime(
            "%Y-%m-%d"
        )


        due_date = (
            datetime.now()
            + timedelta(days=14)
        ).strftime(
            "%Y-%m-%d"
        )


        db.execute("""
            INSERT INTO transactions
            (
                book_id,
                student_id,
                issue_date,
                due_date,
                status
            )

            VALUES(?,?,?,?,?)

        """, (
            book_id,
            student_id,
            issue_date,
            due_date,
            "Issued"
        ))


        db.execute("""
            UPDATE books
            SET available=available-1
            WHERE id=?
        """, (
            book_id,
        ))


        db.commit()
        db.close()


        flash(
            "Book issued successfully!"
        )

        return redirect("/issue")


    books = db.execute("""
        SELECT *
        FROM books
        WHERE available > 0
        ORDER BY title
    """).fetchall()


    students = db.execute("""
        SELECT *
        FROM students
        ORDER BY name
    """).fetchall()


    db.close()


    book_options = ""

    for book in books:

        book_options += f"""

        <option value="{book["id"]}">
            {book["title"]}
            — Available: {book["available"]}
        </option>

        """


    student_options = ""

    for student in students:

        student_options += f"""

        <option value="{student["id"]}">
            {student["name"]}
            — {student["roll_no"]}
        </option>

        """


    content = f"""

    <div class="page-title">

        <h1>
            📖 Issue Book
        </h1>

        <p>
            Issue a book to a registered student.
        </p>

    </div>


    <div class="form-box">

        <form method="POST">


            <div class="form-group">

                <label>
                    Select Book
                </label>

                <select
                    name="book"
                    required>

                    <option value="">
                        Select available book
                    </option>

                    {book_options}

                </select>

            </div>


            <div class="form-group">

                <label>
                    Select Student
                </label>

                <select
                    name="student"
                    required>

                    <option value="">
                        Select student
                    </option>

                    {student_options}

                </select>

            </div>


            <div class="form-group">

                <label>
                    Issue Period
                </label>

                <input
                    value="14 Days"
                    disabled>

            </div>


            <button
                class="btn primary">

                📖 Issue Book

            </button>

        </form>

    </div>

    """

    return render_page(content)


# =========================================================
# RETURN LIST
# =========================================================

@app.route("/returns")
@login_required
def returns():

    db = get_db()


    data = db.execute("""
        SELECT
            transactions.id,
            books.title,
            students.name,
            students.roll_no,
            transactions.issue_date,
            transactions.due_date

        FROM transactions

        JOIN books
        ON transactions.book_id=books.id

        JOIN students
        ON transactions.student_id=students.id

        WHERE transactions.status='Issued'

        ORDER BY transactions.id DESC

    """).fetchall()


    db.close()


    rows = ""

    for item in data:

        rows += f"""

        <tr>

            <td>
                {item["title"]}
            </td>

            <td>
                {item["name"]}
            </td>

            <td>
                {item["roll_no"]}
            </td>

            <td>
                {item["issue_date"]}
            </td>

            <td>
                {item["due_date"]}
            </td>

            <td>

                <a
                    class="btn success"
                    href="/return/{item["id"]}">

                    ↩️ Return

                </a>

            </td>

        </tr>

        """


    content = f"""

    <div class="page-title">

        <h1>
            ↩️ Return Book
        </h1>

        <p>
            Currently issued books.
        </p>

    </div>


    <div class="table-box">

        <table>

            <tr>

                <th>Book</th>
                <th>Student</th>
                <th>Roll No</th>
                <th>Issue Date</th>
                <th>Due Date</th>
                <th>Action</th>

            </tr>

            {rows}

        </table>

    </div>

    """

    return render_page(content)


# =========================================================
# RETURN BOOK
# =========================================================

@app.route(
    "/return/<int:id>"
)
@login_required
def return_book(id):

    db = get_db()


    transaction = db.execute("""
        SELECT book_id
        FROM transactions
        WHERE id=?
        AND status='Issued'
    """, (
        id,
    )).fetchone()


    if transaction:

        return_date = datetime.now().strftime(
            "%Y-%m-%d"
        )


        db.execute("""
            UPDATE transactions

            SET return_date=?,
                status='Returned'

            WHERE id=?

        """, (
            return_date,
            id
        ))


        db.execute("""
            UPDATE books

            SET available=available+1

            WHERE id=?

        """, (
            transaction["book_id"],
        ))


        db.commit()


        flash(
            "Book returned successfully!"
        )


    db.close()


    return redirect("/returns")


# =========================================================
# HISTORY
# =========================================================

@app.route("/history")
@login_required
def history():

    db = get_db()


    data = db.execute("""
        SELECT
            transactions.*,
            books.title,
            students.name,
            students.roll_no

        FROM transactions

        JOIN books
        ON transactions.book_id=books.id

        JOIN students
        ON transactions.student_id=students.id

        ORDER BY transactions.id DESC

    """).fetchall()


    db.close()


    rows = ""

    for item in data:

        if item["status"] == "Returned":

            status = """
                <span class="btn success">
                    Returned
                </span>
            """

        else:

            status = """
                <span class="btn"
                style="
                    background:#dbeafe;
                    color:#1d4ed8;
                ">
                    Issued
                </span>
            """


        rows += f"""

        <tr>

            <td>
                #{item["id"]}
            </td>

            <td>
                {item["title"]}
            </td>

            <td>
                {item["name"]}
            </td>

            <td>
                {item["roll_no"]}
            </td>

            <td>
                {item["issue_date"]}
            </td>

            <td>
                {item["due_date"]}
            </td>

            <td>
                {item["return_date"] or "-"}
            </td>

            <td>
                {status}
            </td>

        </tr>

        """


    content = f"""

    <div class="page-title">

        <h1>
            📋 Transaction History
        </h1>

        <p>
            Complete issue and return history.
        </p>

    </div>


    <div class="table-box">

        <table>

            <tr>

                <th>ID</th>
                <th>Book</th>
                <th>Student</th>
                <th>Roll No</th>
                <th>Issue</th>
                <th>Due</th>
                <th>Return</th>
                <th>Status</th>

            </tr>

            {rows}

        </table>

    </div>

    """

    return render_page(content)


# =========================================================
# QR SCANNER
# =========================================================

@app.route("/scan")
@login_required
def scan():

    content = """

    <div class="page-title">

        <h1>
            📷 QR Scanner
        </h1>

        <p>
            Scan a book QR code using your laptop webcam.
        </p>

    </div>


    <div class="scanner">

        <h3>
            Scan Book QR Code
        </h3>

        <p style="
            color:#64748b;
            margin-top:7px;
            font-size:13px;
        ">

            Allow camera permission
            when the browser asks.

        </p>


        <div id="reader"></div>

    </div>


    <script src="
    https://unpkg.com/html5-qrcode">
    </script>


    <script>

    function onScanSuccess(decodedText, decodedResult)
    {

        window.location.href =
        decodedText;

    }


    function onScanFailure(error)
    {
        // Continue scanning
    }


    const scanner =
    new Html5QrcodeScanner(
        "reader",
        {
            fps: 10,
            qrbox: 250
        }
    );


    scanner.render(
        onScanSuccess,
        onScanFailure
    );

    </script>

    """

    return render_page(content)


# =========================================================
# BOOK DETAILS FROM QR
# =========================================================

@app.route(
    "/book/<int:id>"
)
def book_details(id):

    db = get_db()


    book = db.execute(
        "SELECT * FROM books WHERE id=?",
        (id,)
    ).fetchone()


    db.close()


    if not book:

        return """

        <div style="
            padding:60px;
            text-align:center;
            font-family:Arial;
        ">

            <h1>
                ❌ Book Not Found
            </h1>

        </div>

        """


    if book["available"] > 0:

        status = """

        <span class="btn success">
            ✅ Available
        </span>

        """

    else:

        status = """

        <span class="btn danger">
            ❌ Not Available
        </span>

        """


    content = f"""

    <div class="page-title">

        <h1>
            📚 Book Details
        </h1>

    </div>


    <div class="book-card">

        <h2>
            {book["title"]}
        </h2>


        <div class="book-row">

            <b>
                Author:
            </b>

            {book["author"]}

        </div>


        <div class="book-row">

            <b>
                Category:
            </b>

            {book["category"] or "-"}

        </div>


        <div class="book-row">

            <b>
                ISBN:
            </b>

            {book["isbn"] or "-"}

        </div>


        <div class="book-row">

            <b>
                Total Quantity:
            </b>

            {book["quantity"]}

        </div>


        <div class="book-row">

            <b>
                Available:
            </b>

            {book["available"]}

        </div>


        <br>

        {status}

    </div>

    """

    return render_page(content)


# =========================================================
# START APPLICATION
# =========================================================

if __name__ == "__main__":

    init_db()

    print()
    print("==============================================")
    print("       QR LIBRARY MANAGEMENT SYSTEM")
    print("==============================================")
    print()
    print("Username : admin")
    print("Password : admin123")
    print()
    print("Open Browser:")
    print("http://127.0.0.1:5000")
    print()
    print("==============================================")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
