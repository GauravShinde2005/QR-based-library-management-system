from flask import Flask, request, redirect, session, render_template_string, flash, get_flashed_messages
import sqlite3
import qrcode
import os
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
app.secret_key = "qr_library_2026"

DB = "library.db"
QR_FOLDER = "static/qr"
os.makedirs(QR_FOLDER, exist_ok=True)


# =========================================================
# DATABASE
# =========================================================

def get_db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    con = get_db()
    cur = con.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS admin(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS books(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            category TEXT,
            isbn TEXT,
            quantity INTEGER DEFAULT 1,
            available INTEGER DEFAULT 1,
            qr_code TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS students(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            roll_no TEXT UNIQUE NOT NULL,
            email TEXT,
            phone TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER,
            student_id INTEGER,
            issue_date TEXT,
            due_date TEXT,
            return_date TEXT,
            status TEXT
        )
    """)

    if not cur.execute(
        "SELECT id FROM admin WHERE username=?",
        ("admin",)
    ).fetchone():
        cur.execute(
            "INSERT INTO admin(username,password) VALUES(?,?)",
            ("admin", "admin123")
        )

    con.commit()
    con.close()


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "admin" not in session:
            return redirect("/")
        return func(*args, **kwargs)
    return wrapper


# =========================================================
# ADVANCED CSS
# =========================================================

CSS = r"""
<style>

*{
    margin:0;
    padding:0;
    box-sizing:border-box;
}

body{
    font-family:Arial,Helvetica,sans-serif;
    background:#f4f7fb;
    color:#172033;
    overflow-x:hidden;
}

/* Animated background */
body::before,
body::after{
    content:"";
    position:fixed;
    width:450px;
    height:450px;
    border-radius:50%;
    filter:blur(110px);
    opacity:.13;
    z-index:-5;
}

body::before{
    background:#2563eb;
    top:-180px;
    left:-150px;
    animation:blob1 8s ease-in-out infinite alternate;
}

body::after{
    background:#7c3aed;
    right:-160px;
    bottom:-180px;
    animation:blob2 9s ease-in-out infinite alternate;
}

@keyframes blob1{
    to{
        transform:translate(130px,100px) scale(1.3);
    }
}

@keyframes blob2{
    to{
        transform:translate(-120px,-100px) scale(1.25);
    }
}


/* =========================================================
   SIDEBAR
   ========================================================= */

.sidebar{
    position:fixed;
    left:0;
    top:0;
    width:250px;
    height:100vh;
    padding:20px 15px;
    color:white;
    background:
        linear-gradient(
            160deg,
            #020617,
            #172554,
            #111827
        );
    box-shadow:10px 0 35px rgba(0,0,0,.12);
    z-index:1000;
    animation:sidebarIn .7s ease;
}

@keyframes sidebarIn{
    from{
        transform:translateX(-100%);
        opacity:0;
    }
    to{
        transform:translateX(0);
        opacity:1;
    }
}

.logo{
    font-size:23px;
    font-weight:bold;
    padding:12px 10px 28px;
}

.logo span{
    color:#60a5fa;
}

.menu-title{
    color:#64748b;
    font-size:10px;
    font-weight:bold;
    letter-spacing:1.5px;
    margin:20px 10px 8px;
}

.sidebar a{
    display:flex;
    align-items:center;
    gap:10px;
    color:#cbd5e1;
    text-decoration:none;
    padding:12px 14px;
    margin:5px 0;
    border-radius:10px;
    transition:.3s;
}

.sidebar a:hover{
    color:white;
    background:linear-gradient(
        90deg,
        #2563eb,
        #4f46e5
    );
    transform:translateX(7px);
    box-shadow:0 8px 25px rgba(37,99,235,.35);
}


/* =========================================================
   MAIN
   ========================================================= */

.main{
    margin-left:250px;
    min-height:100vh;
}

.topbar{
    height:72px;
    padding:0 30px;
    display:flex;
    align-items:center;
    justify-content:space-between;
    background:rgba(255,255,255,.82);
    backdrop-filter:blur(18px);
    border-bottom:1px solid #e5e7eb;
    position:sticky;
    top:0;
    z-index:500;
    animation:topIn .6s ease;
}

@keyframes topIn{
    from{
        opacity:0;
        transform:translateY(-30px);
    }
    to{
        opacity:1;
        transform:none;
    }
}

.admin{
    background:#eff6ff;
    color:#2563eb;
    padding:9px 16px;
    border-radius:50px;
    font-weight:bold;
}

.content{
    padding:32px;
    animation:contentIn .6s ease;
}

@keyframes contentIn{
    from{
        opacity:0;
        transform:translateY(20px);
    }
    to{
        opacity:1;
        transform:none;
    }
}

.page-title{
    margin-bottom:25px;
}

.page-title h1{
    font-size:30px;
}

.page-title p{
    color:#64748b;
    margin-top:7px;
}


/* =========================================================
   DASHBOARD CARDS
   ========================================================= */

.cards{
    display:grid;
    grid-template-columns:repeat(4,1fr);
    gap:20px;
}

.card{
    background:rgba(255,255,255,.94);
    border:1px solid #e5e7eb;
    border-radius:18px;
    padding:22px;
    box-shadow:0 12px 35px rgba(15,23,42,.07);
    animation:cardIn .7s ease backwards;
    transition:.35s;
}

.card:nth-child(1){animation-delay:.1s}
.card:nth-child(2){animation-delay:.2s}
.card:nth-child(3){animation-delay:.3s}
.card:nth-child(4){animation-delay:.4s}

.card:hover{
    transform:translateY(-8px) scale(1.02);
    box-shadow:0 22px 45px rgba(37,99,235,.18);
}

@keyframes cardIn{
    from{
        opacity:0;
        transform:translateY(30px) scale(.9);
    }
    to{
        opacity:1;
        transform:none;
    }
}

.card-icon{
    width:52px;
    height:52px;
    display:flex;
    align-items:center;
    justify-content:center;
    border-radius:14px;
    background:linear-gradient(
        135deg,
        #eff6ff,
        #eef2ff
    );
    font-size:25px;
}

.card h2{
    margin-top:15px;
    font-size:32px;
}

.card p{
    color:#64748b;
    margin-top:5px;
}


/* =========================================================
   QUICK ACTIONS
   ========================================================= */

.actions{
    display:grid;
    grid-template-columns:repeat(4,1fr);
    gap:16px;
    margin:25px 0;
}

.action{
    background:white;
    padding:20px;
    border-radius:15px;
    border:1px solid #e5e7eb;
    text-decoration:none;
    color:#172033;
    transition:.3s;
    animation:contentIn .7s;
}

.action:hover{
    transform:translateY(-7px);
    border-color:#93c5fd;
    box-shadow:0 15px 35px rgba(37,99,235,.15);
}

.action-icon{
    font-size:30px;
    margin-bottom:12px;
    transition:.3s;
}

.action:hover .action-icon{
    transform:scale(1.25) rotate(-6deg);
}

.action small{
    display:block;
    color:#64748b;
    margin-top:5px;
}


/* =========================================================
   TABLE
   ========================================================= */

.table-box{
    background:rgba(255,255,255,.95);
    padding:22px;
    border-radius:17px;
    box-shadow:0 10px 35px rgba(15,23,42,.07);
    overflow-x:auto;
    animation:contentIn .7s;
}

table{
    width:100%;
    border-collapse:separate;
    border-spacing:0 7px;
}

th{
    text-align:left;
    padding:12px;
    font-size:12px;
    color:#64748b;
    text-transform:uppercase;
}

td{
    padding:13px;
    background:white;
    border-top:1px solid #f1f5f9;
    border-bottom:1px solid #f1f5f9;
    transition:.25s;
}

tbody tr{
    animation:rowIn .5s ease backwards;
}

tbody tr:nth-child(1){animation-delay:.05s}
tbody tr:nth-child(2){animation-delay:.10s}
tbody tr:nth-child(3){animation-delay:.15s}
tbody tr:nth-child(4){animation-delay:.20s}
tbody tr:nth-child(5){animation-delay:.25s}
tbody tr:nth-child(6){animation-delay:.30s}

tbody tr:hover td{
    background:#f8fbff;
}

@keyframes rowIn{
    from{
        opacity:0;
        transform:translateX(-20px);
    }
    to{
        opacity:1;
        transform:none;
    }
}


/* =========================================================
   BUTTONS
   ========================================================= */

.btn{
    display:inline-flex;
    align-items:center;
    justify-content:center;
    gap:6px;
    padding:10px 15px;
    border:0;
    border-radius:9px;
    text-decoration:none;
    cursor:pointer;
    font-weight:bold;
    position:relative;
    overflow:hidden;
    transition:.2s;
}

.btn:hover{
    transform:translateY(-2px);
    box-shadow:0 8px 20px rgba(0,0,0,.12);
}

.btn:active{
    transform:scale(.95);
}

.primary{
    color:white;
    background:linear-gradient(
        135deg,
        #2563eb,
        #4f46e5
    );
}

.dark{
    color:white;
    background:#111827;
}

.success{
    color:#15803d;
    background:#dcfce7;
}

.danger{
    color:#dc2626;
    background:#fee2e2;
}


/* =========================================================
   FORM
   ========================================================= */

.form-box{
    max-width:700px;
    background:rgba(255,255,255,.96);
    padding:28px;
    border-radius:18px;
    box-shadow:0 15px 40px rgba(15,23,42,.08);
    animation:formIn .6s ease;
}

@keyframes formIn{
    from{
        opacity:0;
        transform:translateY(25px) scale(.97);
    }
    to{
        opacity:1;
        transform:none;
    }
}

.form-group{
    margin-bottom:18px;
}

label{
    display:block;
    font-weight:bold;
    font-size:13px;
    margin-bottom:7px;
}

input,
select{
    width:100%;
    padding:13px;
    border:1px solid #dbe2ea;
    border-radius:9px;
    font-size:14px;
    transition:.25s;
}

input:focus,
select:focus{
    outline:none;
    border-color:#2563eb;
    box-shadow:0 0 0 4px rgba(37,99,235,.1);
    transform:translateY(-1px);
}


/* =========================================================
   QR
   ========================================================= */

.qr-image{
    width:75px;
    height:75px;
    padding:5px;
    background:white;
    border-radius:10px;
    transition:.4s;
}

.qr-image:hover{
    transform:scale(1.25) rotate(3deg);
    box-shadow:0 15px 35px rgba(37,99,235,.2);
}


/* =========================================================
   QR SCANNER
   ========================================================= */

.scanner-box{
    max-width:700px;
    background:white;
    padding:25px;
    border-radius:20px;
    box-shadow:0 20px 50px rgba(15,23,42,.08);
    animation:scannerIn .7s;
}

@keyframes scannerIn{
    from{
        opacity:0;
        transform:scale(.9);
    }
    to{
        opacity:1;
        transform:scale(1);
    }
}

.qr-frame{
    position:relative;
    border-radius:15px;
    padding:10px;
    overflow:hidden;
    background:#020617;
}

.qr-frame::after{
    content:"";
    position:absolute;
    left:8%;
    width:84%;
    height:3px;
    background:linear-gradient(
        90deg,
        transparent,
        #22c55e,
        transparent
    );
    box-shadow:0 0 15px #22c55e;
    animation:scanLine 2s infinite;
    z-index:10;
}

@keyframes scanLine{
    0%{top:8%}
    50%{top:90%}
    100%{top:8%}
}

.corner{
    position:absolute;
    width:35px;
    height:35px;
    border-color:#22c55e;
    z-index:20;
}

.c1{
    top:18px;
    left:18px;
    border-top:4px solid;
    border-left:4px solid;
}

.c2{
    top:18px;
    right:18px;
    border-top:4px solid;
    border-right:4px solid;
}

.c3{
    bottom:18px;
    left:18px;
    border-bottom:4px solid;
    border-left:4px solid;
}

.c4{
    bottom:18px;
    right:18px;
    border-bottom:4px solid;
    border-right:4px solid;
}


/* =========================================================
   LOGIN
   ========================================================= */

.login-page{
    min-height:100vh;
    display:flex;
    justify-content:center;
    align-items:center;
    background:
        radial-gradient(
            circle at 20% 20%,
            #2563eb,
            transparent 30%
        ),
        radial-gradient(
            circle at 80% 80%,
            #7c3aed,
            transparent 30%
        ),
        #020617;
    overflow:hidden;
}

.login-box{
    width:420px;
    padding:40px;
    border-radius:22px;
    background:rgba(255,255,255,.96);
    box-shadow:0 30px 80px rgba(0,0,0,.4);
    animation:loginIn .8s cubic-bezier(.2,.8,.2,1);
}

@keyframes loginIn{
    from{
        opacity:0;
        transform:translateY(60px) scale(.85) rotateX(10deg);
    }
    to{
        opacity:1;
        transform:none;
    }
}

.login-logo{
    text-align:center;
    font-size:30px;
    font-weight:800;
    margin-bottom:8px;
}

.login-logo span{
    color:#2563eb;
}

.login-subtitle{
    text-align:center;
    color:#64748b;
    margin-bottom:28px;
}

.login-button{
    width:100%;
    padding:14px;
    border:0;
    border-radius:10px;
    color:white;
    font-size:15px;
    font-weight:bold;
    cursor:pointer;
    background:linear-gradient(
        135deg,
        #2563eb,
        #4f46e5
    );
    transition:.3s;
}

.login-button:hover{
    transform:translateY(-3px);
    box-shadow:0 12px 30px rgba(37,99,235,.4);
}


/* =========================================================
   ALERT
   ========================================================= */

.alert{
    position:fixed;
    top:85px;
    right:25px;
    background:#dcfce7;
    color:#166534;
    padding:14px 20px;
    border-radius:10px;
    z-index:5000;
    box-shadow:0 15px 35px rgba(0,0,0,.15);
    animation:
        alertIn .5s,
        alertOut .5s 3.5s forwards;
}

@keyframes alertIn{
    from{
        opacity:0;
        transform:translateX(120%);
    }
    to{
        opacity:1;
        transform:none;
    }
}

@keyframes alertOut{
    to{
        opacity:0;
        transform:translateX(120%);
    }
}


/* =========================================================
   MOBILE / SMALL SCREEN
   ========================================================= */

@media(max-width:1100px){
    .cards{
        grid-template-columns:repeat(2,1fr);
    }

    .actions{
        grid-template-columns:repeat(2,1fr);
    }
}

@media(max-width:700px){
    .sidebar{
        position:relative;
        width:100%;
        height:auto;
    }

    .main{
        margin-left:0;
    }

    .cards,
    .actions{
        grid-template-columns:1fr;
    }

    .content{
        padding:18px;
    }

    .login-box{
        width:90%;
    }
}

</style>
"""


# =========================================================
# JAVASCRIPT ANIMATIONS
# =========================================================

JS = r"""
<script>

/* Floating particles */
for(let i=0;i<20;i++){

    const p=document.createElement("div");

    p.style.position="fixed";
    p.style.left=(Math.random()*100)+"%";
    p.style.bottom="-15px";

    const size=3+Math.random()*4;

    p.style.width=size+"px";
    p.style.height=size+"px";
    p.style.borderRadius="50%";
    p.style.background="#2563eb";
    p.style.opacity=".15";
    p.style.pointerEvents="none";
    p.style.zIndex="-1";

    p.style.animation=
        "floatParticle "+
        (8+Math.random()*10)+
        "s linear "+
        (Math.random()*5)+
        "s infinite";

    document.body.appendChild(p);
}


/* Count-up animation */
document.querySelectorAll(".counter").forEach(function(el){

    const target=Number(el.dataset.target || 0);
    const start=performance.now();
    const duration=1000;

    function animate(now){

        const progress=Math.min(
            (now-start)/duration,
            1
        );

        el.textContent=
            Math.floor(progress*target);

        if(progress<1){
            requestAnimationFrame(animate);
        }
    }

    requestAnimationFrame(animate);
});


/* Button ripple effect */
document.querySelectorAll(".btn").forEach(function(button){

    button.addEventListener("click",function(e){

        const ripple=document.createElement("span");

        ripple.style.position="absolute";
        ripple.style.width="10px";
        ripple.style.height="10px";
        ripple.style.borderRadius="50%";
        ripple.style.background="rgba(255,255,255,.4)";
        ripple.style.left=e.offsetX+"px";
        ripple.style.top=e.offsetY+"px";
        ripple.style.transform="translate(-50%,-50%)";
        ripple.style.pointerEvents="none";
        ripple.style.animation="ripple .6s ease";

        button.appendChild(ripple);

        setTimeout(function(){
            ripple.remove();
        },600);

    });

});

</script>

<style>

@keyframes floatParticle{
    to{
        transform:
            translateY(-110vh)
            translateX(80px);
        opacity:0;
    }
}

@keyframes ripple{
    to{
        transform:
            translate(-50%,-50%)
            scale(25);
        opacity:0;
    }
}

</style>
"""


# =========================================================
# PAGE TEMPLATE
# =========================================================

def page(content):

    messages = get_flashed_messages()

    alerts = ""

    for message in messages:
        alerts += f"""
        <div class="alert">
            ✅ {message}
        </div>
        """

    if "admin" not in session:
        return render_template_string(
            CSS + content + JS
        )

    html = f"""

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
            QR LIBRARY
        </div>

        <a href="/issue">
            📖 Issue Book
        </a>

        <a href="/returns">
            ↩️ Return Book
        </a>

        <a href="/scan">
            📷 QR Scanner
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

            <div>
                <b>QR Library Management System</b>
            </div>

            <div class="admin">
                👤 Admin
            </div>

        </div>

        {alerts}

        <div class="content">
            {content}
        </div>

    </div>

    """

    return render_template_string(
        CSS + html + JS
    )


# =========================================================
# LOGIN
# =========================================================

@app.route("/", methods=["GET", "POST"])
def login():

    error = ""

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        con = get_db()

        user = con.execute(
            """
            SELECT * FROM admin
            WHERE username=? AND password=?
            """,
            (username, password)
        ).fetchone()

        con.close()

        if user:

            session["admin"] = username

            return redirect("/dashboard")

        error = """
        <p style="
            color:#dc2626;
            text-align:center;
            margin-bottom:15px;
        ">
            ❌ Invalid username or password
        </p>
        """

    content = f"""

    <div class="login-page">

        <div class="login-box">

            <div class="login-logo">
                📚 <span>QR Library</span>
            </div>

            <div class="login-subtitle">
                Smart Library Management System
            </div>

            {error}

            <form method="POST">

                <div class="form-group">

                    <label>
                        Username
                    </label>

                    <input
                        name="username"
                        placeholder="Enter username"
                        required
                    >

                </div>

                <div class="form-group">

                    <label>
                        Password
                    </label>

                    <input
                        type="password"
                        name="password"
                        placeholder="Enter password"
                        required
                    >

                </div>

                <button class="login-button">
                    🔐 Login
                </button>

            </form>

            <div style="
                text-align:center;
                color:#64748b;
                font-size:12px;
                margin-top:20px;
            ">

                Demo Login<br><br>

                Username:
                <b>admin</b>

                <br>

                Password:
                <b>admin123</b>

            </div>

        </div>

    </div>

    """

    return page(content)


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

    con = get_db()

    books = con.execute(
        "SELECT COUNT(*) FROM books"
    ).fetchone()[0]

    students = con.execute(
        "SELECT COUNT(*) FROM students"
    ).fetchone()[0]

    issued = con.execute(
        """
        SELECT COUNT(*)
        FROM transactions
        WHERE status='Issued'
        """
    ).fetchone()[0]

    returned = con.execute(
        """
        SELECT COUNT(*)
        FROM transactions
        WHERE status='Returned'
        """
    ).fetchone()[0]

    recent = con.execute(
        """
        SELECT t.*,b.title,s.name
        FROM transactions t
        JOIN books b ON t.book_id=b.id
        JOIN students s ON t.student_id=s.id
        ORDER BY t.id DESC
        LIMIT 6
        """
    ).fetchall()

    con.close()

    rows = ""

    for r in recent:

        if r["status"] == "Returned":
            status = """
            <span class="btn success">
                ✓ Returned
            </span>
            """
        else:
            status = """
            <span class="btn"
            style="background:#dbeafe;color:#1d4ed8">
                ● Issued
            </span>
            """

        rows += f"""

        <tr>

            <td>
                <b>{r["title"]}</b>
            </td>

            <td>
                {r["name"]}
            </td>

            <td>
                {r["issue_date"]}
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
            Welcome back, Admin 👋
        </p>

    </div>


    <div class="cards">

        <div class="card">

            <div class="card-icon">
                📚
            </div>

            <h2
                class="counter"
                data-target="{books}">
                0
            </h2>

            <p>
                Total Books
            </p>

        </div>


        <div class="card">

            <div class="card-icon">
                👨‍🎓
            </div>

            <h2
                class="counter"
                data-target="{students}">
                0
            </h2>

            <p>
                Total Students
            </p>

        </div>


        <div class="card">

            <div class="card-icon">
                📖
            </div>

            <h2
                class="counter"
                data-target="{issued}">
                0
            </h2>

            <p>
                Issued Books
            </p>

        </div>


        <div class="card">

            <div class="card-icon">
                ↩️
            </div>

            <h2
                class="counter"
                data-target="{returned}">
                0
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
                Add Book
            </b>

            <small>
                Generate QR code
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
                Issue to student
            </small>

        </a>


        <a
            class="action"
            href="/returns">

            <div class="action-icon">
                ↩️
            </div>

            <b>
                Return Book
            </b>

            <small>
                Process returns
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
                Scan book instantly
            </small>

        </a>

    </div>


    <div class="table-box">

        <h2 style="margin-bottom:15px">
            Recent Transactions
        </h2>

        <table>

            <thead>

                <tr>
                    <th>Book</th>
                    <th>Student</th>
                    <th>Issue Date</th>
                    <th>Status</th>
                </tr>

            </thead>

            <tbody>
                {rows}
            </tbody>

        </table>

    </div>

    """

    return page(content)


# =========================================================
# BOOKS
# =========================================================

@app.route("/books")
@login_required
def books_page():

    search = request.args.get("search", "")

    con = get_db()

    if search:

        pattern = f"%{search}%"

        books = con.execute(
            """
            SELECT * FROM books
            WHERE title LIKE ?
            OR author LIKE ?
            OR category LIKE ?
            OR isbn LIKE ?
            ORDER BY id DESC
            """,
            (pattern, pattern, pattern, pattern)
        ).fetchall()

    else:

        books = con.execute(
            "SELECT * FROM books ORDER BY id DESC"
        ).fetchall()

    con.close()

    rows = ""

    for b in books:

        rows += f"""

        <tr>

            <td>
                #{b["id"]}
            </td>

            <td>

                <img
                    class="qr-image"
                    src="/static/qr/{b["qr_code"]}"
                >

            </td>

            <td>

                <a
                    href="/book/{b["id"]}"
                    style="
                        color:#2563eb;
                        text-decoration:none;
                    ">

                    <b>
                        {b["title"]}
                    </b>

                </a>

            </td>

            <td>
                {b["author"]}
            </td>

            <td>
                {b["category"] or "-"}
            </td>

            <td>
                {b["quantity"]}
            </td>

            <td>
                <b style="color:#15803d">
                    {b["available"]}
                </b>
            </td>

            <td>

                <a
                    class="btn danger"
                    href="/books/delete/{b["id"]}"
                    onclick="
                        return confirm('Delete this book?')
                    ">

                    🗑 Delete

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
            Every book has a unique QR code.
        </p>

    </div>


    <a
        class="btn primary"
        href="/books/add">

        ➕ Add New Book

    </a>


    <br><br>


    <form
        method="GET"
        style="
            display:flex;
            gap:10px;
            margin-bottom:20px;
        ">

        <input
            name="search"
            value="{search}"
            placeholder="🔍 Search books..."
        >

        <button class="btn dark">
            Search
        </button>

    </form>


    <div class="table-box">

        <table>

            <thead>

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

            </thead>

            <tbody>
                {rows}
            </tbody>

        </table>

    </div>

    """

    return page(content)


# =========================================================
# ADD BOOK + GENERATE QR
# =========================================================

@app.route("/books/add", methods=["GET", "POST"])
@login_required
def add_book():

    if request.method == "POST":

        title = request.form["title"]
        author = request.form["author"]
        category = request.form.get("category", "")
        isbn = request.form.get("isbn", "")
        quantity = int(request.form["quantity"])

        con = get_db()
        cur = con.cursor()

        cur.execute(
            """
            INSERT INTO books
            (title,author,category,isbn,quantity,available)
            VALUES(?,?,?,?,?,?)
            """,
            (
                title,
                author,
                category,
                isbn,
                quantity,
                quantity
            )
        )

        book_id = cur.lastrowid

        # QR contains the local book URL
        qr_url = (
            f"http://127.0.0.1:5000/book/{book_id}"
        )

        qr = qrcode.QRCode(
            version=1,
            box_size=10,
            border=4
        )

        qr.add_data(qr_url)
        qr.make(fit=True)

        img = qr.make_image(
            fill_color="black",
            back_color="white"
        )

        filename = f"book_{book_id}.png"

        img.save(
            os.path.join(
                QR_FOLDER,
                filename
            )
        )

        cur.execute(
            """
            UPDATE books
            SET qr_code=?
            WHERE id=?
            """,
            (filename, book_id)
        )

        con.commit()
        con.close()

        flash(
            "Book added and QR code generated!"
        )

        return redirect("/books")

    content = """

    <div class="page-title">

        <h1>
            ➕ Add New Book
        </h1>

        <p>
            A unique QR code will be
            generated automatically.
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
                    required
                >

            </div>


            <div class="form-group">

                <label>
                    Author *
                </label>

                <input
                    name="author"
                    placeholder="Enter author"
                    required
                >

            </div>


            <div class="form-group">

                <label>
                    Category
                </label>

                <input
                    name="category"
                    placeholder="Programming / Science / etc."
                >

            </div>


            <div class="form-group">

                <label>
                    ISBN
                </label>

                <input
                    name="isbn"
                    placeholder="Enter ISBN"
                >

            </div>


            <div class="form-group">

                <label>
                    Quantity *
                </label>

                <input
                    type="number"
                    name="quantity"
                    min="1"
                    value="1"
                    required
                >

            </div>


            <button class="btn primary">

                📚 Add Book + Generate QR

            </button>


            <a
                href="/books"
                class="btn dark">

                Cancel

            </a>

        </form>

    </div>

    """

    return page(content)


# =========================================================
# DELETE BOOK
# =========================================================

@app.route("/books/delete/<int:id>")
@login_required
def delete_book(id):

    con = get_db()

    book = con.execute(
        "SELECT * FROM books WHERE id=?",
        (id,)
    ).fetchone()

    if book:

        if book["qr_code"]:

            path = os.path.join(
                QR_FOLDER,
                book["qr_code"]
            )

            if os.path.exists(path):
                os.remove(path)

        con.execute(
            "DELETE FROM books WHERE id=?",
            (id,)
        )

        con.commit()

    con.close()

    flash("Book deleted!")

    return redirect("/books")


# =========================================================
# STUDENTS
# =========================================================

@app.route("/students")
@login_required
def students():

    con = get_db()

    data = con.execute(
        "SELECT * FROM students ORDER BY id DESC"
    ).fetchall()

    con.close()

    rows = ""

    for s in data:

        rows += f"""

        <tr>

            <td>
                #{s["id"]}
            </td>

            <td>
                <b>{s["name"]}</b>
            </td>

            <td>
                {s["roll_no"]}
            </td>

            <td>
                {s["email"] or "-"}
            </td>

            <td>
                {s["phone"] or "-"}
            </td>

        </tr>

        """

    content = f"""

    <div class="page-title">

        <h1>
            👨‍🎓 Students
        </h1>

        <p>
            Registered library students.
        </p>

    </div>


    <a
        href="/students/add"
        class="btn primary">

        ➕ Add Student

    </a>


    <br><br>


    <div class="table-box">

        <table>

            <thead>

                <tr>
                    <th>ID</th>
                    <th>Name</th>
                    <th>Roll No</th>
                    <th>Email</th>
                    <th>Phone</th>
                </tr>

            </thead>

            <tbody>
                {rows}
            </tbody>

        </table>

    </div>

    """

    return page(content)


# =========================================================
# ADD STUDENT
# =========================================================

@app.route("/students/add", methods=["GET", "POST"])
@login_required
def add_student():

    if request.method == "POST":

        name = request.form["name"]
        roll = request.form["roll"]
        email = request.form.get("email", "")
        phone = request.form.get("phone", "")

        con = get_db()

        try:

            con.execute(
                """
                INSERT INTO students
                (name,roll_no,email,phone)
                VALUES(?,?,?,?)
                """,
                (
                    name,
                    roll,
                    email,
                    phone
                )
            )

            con.commit()

            flash(
                "Student registered successfully!"
            )

        except sqlite3.IntegrityError:

            flash(
                "Roll number already exists!"
            )

        con.close()

        return redirect("/students")

    content = """

    <div class="page-title">

        <h1>
            👨‍🎓 Add Student
        </h1>

    </div>


    <div class="form-box">

        <form method="POST">

            <div class="form-group">

                <label>
                    Student Name *
                </label>

                <input
                    name="name"
                    required
                    placeholder="Enter student name"
                >

            </div>


            <div class="form-group">

                <label>
                    Roll Number *
                </label>

                <input
                    name="roll"
                    required
                    placeholder="Enter roll number"
                >

            </div>


            <div class="form-group">

                <label>
                    Email
                </label>

                <input
                    name="email"
                    type="email"
                    placeholder="student@example.com"
                >

            </div>


            <div class="form-group">

                <label>
                    Phone
                </label>

                <input
                    name="phone"
                    placeholder="Enter phone number"
                >

            </div>


            <button class="btn primary">

                👨‍🎓 Register Student

            </button>

        </form>

    </div>

    """

    return page(content)


# =========================================================
# ISSUE BOOK
# =========================================================

@app.route("/issue", methods=["GET", "POST"])
@login_required
def issue_book():

    con = get_db()

    if request.method == "POST":

        book_id = request.form["book"]
        student_id = request.form["student"]

        book = con.execute(
            "SELECT * FROM books WHERE id=?",
            (book_id,)
        ).fetchone()

        if not book or book["available"] <= 0:

            con.close()

            flash(
                "Book is not available!"
            )

            return redirect("/issue")

        issue_date = datetime.now().strftime(
            "%Y-%m-%d"
        )

        due_date = (
            datetime.now() +
            timedelta(days=14)
        ).strftime("%Y-%m-%d")

        con.execute(
            """
            INSERT INTO transactions
            (book_id,student_id,issue_date,
             due_date,status)
            VALUES(?,?,?,?,?)
            """,
            (
                book_id,
                student_id,
                issue_date,
                due_date,
                "Issued"
            )
        )

        con.execute(
            """
            UPDATE books
            SET available=available-1
            WHERE id=?
            """,
            (book_id,)
        )

        con.commit()
        con.close()

        flash(
            "📖 Book issued successfully!"
        )

        return redirect("/dashboard")

    books = con.execute(
        """
        SELECT * FROM books
        WHERE available>0
        """
    ).fetchall()

    students = con.execute(
        "SELECT * FROM students"
    ).fetchall()

    con.close()

    book_options = ""

    for b in books:

        book_options += f"""

        <option value="{b["id"]}">

            {b["title"]}
            — Available: {b["available"]}

        </option>

        """

    student_options = ""

    for s in students:

        student_options += f"""

        <option value="{s["id"]}">

            {s["name"]}
            — {s["roll_no"]}

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
                        Choose book
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
                        Choose student
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
                    disabled
                >

            </div>


            <button class="btn primary">

                📖 Issue Book

            </button>

        </form>

    </div>

    """

    return page(content)


# =========================================================
# RETURN PAGE
# =========================================================

@app.route("/returns")
@login_required
def returns():

    con = get_db()

    data = con.execute(
        """
        SELECT
            t.id,
            b.title,
            s.name,
            s.roll_no,
            t.issue_date,
            t.due_date

        FROM transactions t

        JOIN books b
            ON t.book_id=b.id

        JOIN students s
            ON t.student_id=s.id

        WHERE t.status='Issued'

        ORDER BY t.id DESC
        """
    ).fetchall()

    con.close()

    rows = ""

    for x in data:

        rows += f"""

        <tr>

            <td>
                <b>{x["title"]}</b>
            </td>

            <td>
                {x["name"]}
            </td>

            <td>
                {x["roll_no"]}
            </td>

            <td>
                {x["issue_date"]}
            </td>

            <td>
                {x["due_date"]}
            </td>

            <td>

                <a
                    href="/return/{x["id"]}"
                    class="btn success">

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
            Books currently issued.
        </p>

    </div>


    <div class="table-box">

        <table>

            <thead>

                <tr>
                    <th>Book</th>
                    <th>Student</th>
                    <th>Roll</th>
                    <th>Issue</th>
                    <th>Due</th>
                    <th>Action</th>
                </tr>

            </thead>

            <tbody>
                {rows}
            </tbody>

        </table>

    </div>

    """

    return page(content)


# =========================================================
# RETURN BOOK
# =========================================================

@app.route("/return/<int:id>")
@login_required
def return_book(id):

    con = get_db()

    transaction = con.execute(
        """
        SELECT book_id
        FROM transactions
        WHERE id=?
        AND status='Issued'
        """,
        (id,)
    ).fetchone()

    if transaction:

        return_date = datetime.now().strftime(
            "%Y-%m-%d"
        )

        con.execute(
            """
            UPDATE transactions

            SET return_date=?,
                status='Returned'

            WHERE id=?
            """,
            (return_date, id)
        )

        con.execute(
            """
            UPDATE books
            SET available=available+1
            WHERE id=?
            """,
            (transaction["book_id"],)
        )

        con.commit()

        flash(
            "↩️ Book returned successfully!"
        )

    con.close()

    return redirect("/returns")


# =========================================================
# HISTORY
# =========================================================

@app.route("/history")
@login_required
def history():

    con = get_db()

    data = con.execute(
        """
        SELECT
            t.*,
            b.title,
            s.name,
            s.roll_no

        FROM transactions t

        JOIN books b
            ON t.book_id=b.id

        JOIN students s
            ON t.student_id=s.id

        ORDER BY t.id DESC
        """
    ).fetchall()

    con.close()

    rows = ""

    for x in data:

        if x["status"] == "Returned":

            status = """
            <span class="btn success">
                ✓ Returned
            </span>
            """

        else:

            status = """
            <span
                class="btn"
                style="
                    background:#dbeafe;
                    color:#1d4ed8;
                ">

                ● Issued

            </span>
            """

        rows += f"""

        <tr>

            <td>
                #{x["id"]}
            </td>

            <td>
                <b>{x["title"]}</b>
            </td>

            <td>
                {x["name"]}
            </td>

            <td>
                {x["roll_no"]}
            </td>

            <td>
                {x["issue_date"]}
            </td>

            <td>
                {x["due_date"]}
            </td>

            <td>
                {x["return_date"] or "-"}
            </td>

            <td>
                {status}
            </td>

        </tr>

        """

    content = f"""

    <div class="page-title">

        <h1>
            📋 History
        </h1>

        <p>
            Complete library transaction history.
        </p>

    </div>


    <div class="table-box">

        <table>

            <thead>

                <tr>
                    <th>ID</th>
                    <th>Book</th>
                    <th>Student</th>
                    <th>Roll</th>
                    <th>Issue</th>
                    <th>Due</th>
                    <th>Return</th>
                    <th>Status</th>
                </tr>

            </thead>

            <tbody>
                {rows}
            </tbody>

        </table>

    </div>

    """

    return page(content)


# =========================================================
# QR SCANNER
# =========================================================

@app.route("/scan")
@login_required
def scan():

    content = """

    <div class="page-title">

        <h1>
            📷 QR Book Scanner
        </h1>

        <p>
            Scan a book QR code using your
            laptop webcam.
        </p>

    </div>


    <div class="scanner-box">

        <h2>
            Scan QR Code
        </h2>

        <p style="
            color:#64748b;
            margin-top:7px;
        ">

            Place the QR code inside
            the scanning area.

        </p>

        <br>


        <div class="qr-frame">

            <div class="corner c1"></div>
            <div class="corner c2"></div>
            <div class="corner c3"></div>
            <div class="corner c4"></div>

            <div id="reader"></div>

        </div>


        <p style="
            margin-top:15px;
            color:#64748b;
        ">

            🟢 Scanner active...

        </p>

    </div>


    <script src="
        https://unpkg.com/html5-qrcode
    "></script>


    <script>

    function onScanSuccess(decodedText){

        if(
            decodedText.startsWith(
                "http://127.0.0.1:5000/book/"
            )
        ){

            window.location.href =
                decodedText;

        }else{

            alert(
                "This QR code is not a library book QR code."
            );

        }

    }


    function onScanFailure(error){
        // Scanner keeps searching
    }


    const scanner =
        new Html5QrcodeScanner(
            "reader",
            {
                fps:10,
                qrbox:250
            },
            false
        );


    scanner.render(
        onScanSuccess,
        onScanFailure
    );

    </script>

    """

    return page(content)


# =========================================================
# QR BOOK DETAILS
# =========================================================

@app.route("/book/<int:id>")
def book_details(id):

    con = get_db()

    book = con.execute(
        "SELECT * FROM books WHERE id=?",
        (id,)
    ).fetchone()

    con.close()

    if not book:

        return """
        <h1 style="
            text-align:center;
            margin-top:100px;
        ">
            ❌ Book Not Found
        </h1>
        """

    if book["available"] > 0:

        status = """
        <span class="btn success">
            🟢 Available
        </span>
        """

    else:

        status = """
        <span class="btn danger">
            🔴 Not Available
        </span>
        """

    content = f"""

    <div class="page-title">

        <h1>
            📚 QR Book Information
        </h1>

        <p>
            Book information retrieved
            from QR code.
        </p>

    </div>


    <div
        class="form-box"
        style="
            max-width:650px;
            text-align:center;
        "
    >

        <img
            class="qr-image"
            style="
                width:180px;
                height:180px;
                animation:qrAppear .8s ease;
            "
            src="/static/qr/{book["qr_code"]}"
        >


        <h2 style="margin:25px 0">

            {book["title"]}

        </h2>


        <p style="
            margin:13px 0;
            text-align:left;
        ">

            <b>Book ID:</b>
            #{book["id"]}

        </p>


        <p style="
            margin:13px 0;
            text-align:left;
        ">

            <b>Author:</b>
            {book["author"]}

        </p>


        <p style="
            margin:13px 0;
            text-align:left;
        ">

            <b>Category:</b>
            {book["category"] or "-"}

        </p>


        <p style="
            margin:13px 0;
            text-align:left;
        ">

            <b>ISBN:</b>
            {book["isbn"] or "-"}

        </p>


        <p style="
            margin:13px 0;
            text-align:left;
        ">

            <b>Total Copies:</b>
            {book["quantity"]}

        </p>


        <p style="
            margin:13px 0;
            text-align:left;
        ">

            <b>Available Copies:</b>
            {book["available"]}

        </p>


        <br>

        {status}

    </div>


    <style>

    @keyframes qrAppear{{

        from{{
            opacity:0;
            transform:
                scale(0.4)
                rotate(-10deg);
        }}

        to {{
            opacity:1;
            transform:
                scale(1)
                rotate(0);
        }}

    }}

    </style>

    """

    return page(content)


# =========================================================
# START APPLICATION
# =========================================================

if __name__ == "__main__":

    init_db()

    print()
    print("==========================================")
    print("      QR LIBRARY MANAGEMENT SYSTEM")
    print("==========================================")
    print("Username : admin")
    print("Password : admin123")
    print("Website  : http://127.0.0.1:5000")
    print("==========================================")
    print()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )