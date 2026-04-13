from flask import Flask, request, jsonify, render_template_string
import mysql.connector
import os
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# ─── DATABASE CONFIG ──────────────────────────────────────────────
DB_CONFIG = {
    "host":     os.environ.get("DB_HOST"),
    "port":     int(os.environ.get("DB_PORT")),
    "user":     os.environ.get("DB_USER"),
    "password": os.environ.get("DB_PASSWORD"),
    "database": os.environ.get("DB_NAME"),
}

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            title       VARCHAR(255) NOT NULL,
            description TEXT,
            status      ENUM('pending','in_progress','done') DEFAULT 'pending',
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()
    print("[DB] Table ready.")

# ─── HTML INTERFACE ───────────────────────────────────────────────
HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Task Manager</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Segoe UI', sans-serif; background: #0f172a; color: #e2e8f0; min-height: 100vh; padding: 2rem; }
  h1 { text-align: center; font-size: 2rem; margin-bottom: 2rem; color: #38bdf8; }
  .container { max-width: 800px; margin: 0 auto; }
  .card { background: #1e293b; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; border: 1px solid #334155; }
  input, textarea, select { width: 100%; padding: .6rem .8rem; margin: .4rem 0 .8rem; border-radius: 8px;
    background: #0f172a; border: 1px solid #475569; color: #e2e8f0; font-size: .95rem; }
  button { padding: .6rem 1.4rem; border-radius: 8px; border: none; cursor: pointer; font-weight: 600; font-size: .9rem; }
  .btn-primary { background: #38bdf8; color: #0f172a; }
  .btn-danger  { background: #f87171; color: #0f172a; }
  .btn-sm      { padding: .3rem .8rem; font-size: .8rem; }
  table { width: 100%; border-collapse: collapse; }
  th, td { padding: .75rem 1rem; text-align: left; border-bottom: 1px solid #334155; }
  th { color: #94a3b8; font-size: .8rem; text-transform: uppercase; }
  .badge { display: inline-block; padding: .2rem .6rem; border-radius: 99px; font-size: .75rem; font-weight: 700; }
  .badge-pending     { background: #fbbf24; color: #0f172a; }
  .badge-in_progress { background: #60a5fa; color: #0f172a; }
  .badge-done        { background: #34d399; color: #0f172a; }
  #status-msg { color: #34d399; margin-top: .5rem; font-size: .9rem; min-height: 1.2rem; }
</style>
</head>
<body>
<div class="container">
  <h1>📋 Task Manager</h1>

  <!-- Create task -->
  <div class="card">
    <h3 style="margin-bottom:1rem; color:#94a3b8;">Nueva Tarea</h3>
    <input id="title" placeholder="Título *" />
    <textarea id="desc" placeholder="Descripción" rows="2"></textarea>
    <select id="status">
      <option value="pending">Pendiente</option>
      <option value="in_progress">En Progreso</option>
      <option value="done">Completada</option>
    </select>
    <button class="btn-primary" onclick="createTask()">Agregar</button>
    <p id="status-msg"></p>
  </div>

  <!-- Task list -->
  <div class="card">
    <h3 style="margin-bottom:1rem; color:#94a3b8;">Tareas</h3>
    <table>
      <thead><tr><th>ID</th><th>Título</th><th>Estado</th><th>Fecha</th><th></th></tr></thead>
      <tbody id="task-list"></tbody>
    </table>
  </div>
</div>

<script>
  async function loadTasks() {
    const res = await fetch('/api/tasks');
    const tasks = await res.json();
    const tbody = document.getElementById('task-list');
    tbody.innerHTML = tasks.map(t => `
      <tr>
        <td>${t.id}</td>
        <td><b>${t.title}</b><br><small style="color:#94a3b8">${t.description||''}</small></td>
        <td><span class="badge badge-${t.status}">${t.status}</span></td>
        <td><small>${t.created_at}</small></td>
        <td><button class="btn-danger btn-sm" onclick="deleteTask(${t.id})">✕</button></td>
      </tr>`).join('');
  }

  async function createTask() {
    const title = document.getElementById('title').value.trim();
    if (!title) { showMsg('El título es requerido', '#f87171'); return; }
    await fetch('/api/tasks', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({
        title,
        description: document.getElementById('desc').value,
        status: document.getElementById('status').value
      })
    });
    document.getElementById('title').value = '';
    document.getElementById('desc').value  = '';
    showMsg('Tarea creada ✓');
    loadTasks();
  }

  async function deleteTask(id) {
    await fetch(`/api/tasks/${id}`, { method: 'DELETE' });
    loadTasks();
  }

  function showMsg(msg, color='#34d399') {
    const el = document.getElementById('status-msg');
    el.style.color = color;
    el.textContent = msg;
    setTimeout(() => el.textContent = '', 2500);
  }

  loadTasks();
</script>
</body>
</html>
"""

# ─── ROUTES / LOGIC ───────────────────────────────────────────────
@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/health")
def health():
    return jsonify({"status": "ok", "timestamp": datetime.utcnow().isoformat()})

@app.route("/api/tasks", methods=["GET"])
def get_tasks():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM tasks ORDER BY created_at DESC")
    rows = cursor.fetchall()
    for r in rows:
        r["created_at"] = str(r["created_at"])
    cursor.close()
    conn.close()
    return jsonify(rows)

@app.route("/api/tasks", methods=["POST"])
def create_task():
    data = request.get_json()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tasks (title, description, status) VALUES (%s, %s, %s)",
        (data["title"], data.get("description", ""), data.get("status", "pending"))
    )
    conn.commit()
    new_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return jsonify({"id": new_id, "message": "Task created"}), 201

@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Deleted"})

@app.route("/api/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    data = request.get_json()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE tasks SET title=%s, description=%s, status=%s WHERE id=%s",
        (data["title"], data.get("description",""), data["status"], task_id)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Updated"})

# ─── STRESS TEST ENDPOINT ─────────────────────────────────────────
@app.route("/api/stress", methods=["GET"])
def stress():
    """Heavy endpoint: reads all tasks + simulates a small delay."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) as total FROM tasks")
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    time.sleep(0.05)   # 50ms simulated load
    return jsonify({"total_tasks": result["total"], "ts": time.time()})

# ─── MAIN ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=False)
