from flask import Flask, request, render_template, redirect, url_for, session
from werkzeug.security import check_password_hash
import os
import sqlite3

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY")
DB_PATH = "agenda.db"


def get_db():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agendamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT,
            pet TEXT,
            servico TEXT,
            dia TEXT,
            telefone TEXT,
            status TEXT DEFAULT 'pendente'
        )
    """)
    conn.commit()
    conn.close()


init_db()

# =======================================================
#  LOGIN DO ADMIN
# =======================================================
@app.route("/")
def home():
    return render_template("index.html")
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form["usuario"]
        senha = request.form["senha"]

        admin_user = os.environ.get("ADMIN_USER")
        admin_hash = os.environ.get("ADMIN_PASS_HASH")

        if user == admin_user and check_password_hash(admin_hash, senha):
            session["logado"] = True
            return redirect("/admin")
        else:
            return "Login inválido", 403

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


def require_login(func):
    def wrapper(*args, **kwargs):
        if not session.get("logado"):
            return redirect("/login")
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

# =======================================================
#  ROTA: RECEBER AGENDAMENTO
# =======================================================

@app.route("/agendar", methods=["POST"])
def agendar():
    cliente = request.form["cliente"]
    pet = request.form["pet"]
    servico = request.form["servico"]
    dia = request.form["dia"]
    telefone = request.form["telefone"]

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO agendamentos (cliente, pet, servico, dia, telefone)
        VALUES (?, ?, ?, ?, ?)
    """, (cliente, pet, servico, dia, telefone))
    conn.commit()
    conn.close()

    return render_template("confirmacao.html", cliente=cliente)

# =======================================================
#  ROTA: PAINEL ADMIN
# =======================================================

@app.route("/admin")
@require_login
def admin():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM agendamentos ORDER BY dia ASC")
    agendamentos = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM agendamentos")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM agendamentos WHERE status = 'pendente'")
    pendentes = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM agendamentos WHERE status = 'concluido'")
    concluidos = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "admin.html",
        agendamentos=agendamentos,
        total=total,
        pendentes=pendentes,
        concluidos=concluidos
    )

# =======================================================
#  ROTA: MARCAR COMO CONCLUÍDO
# =======================================================

@app.route("/concluir/<int:id>")
@require_login
def concluir(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE agendamentos SET status = 'concluido' WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin"))

# =======================================================
# INICIAR SERVIDOR
# =======================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
