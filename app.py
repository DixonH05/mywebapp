from flask import Flask, render_template, request, redirect, url_for, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import os

app = Flask(__name__)

# 改用新的資料庫檔名，避免和原本 blog 混在一起
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(BASE_DIR, "todo.db")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_path
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ---- 資料模型：Task（任務） ----
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)       # 任務名稱
    notes = db.Column(db.Text, nullable=True)               # 備註
    due_date = db.Column(db.Date, nullable=True)            # 到期日
    done = db.Column(db.Boolean, default=False, nullable=False)  # 是否完成
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "notes": self.notes or "",
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "done": self.done,
            "created_at": self.created_at.isoformat(),
        }

# 第一次啟動自動建表
with app.app_context():
    db.create_all()

# ------------- HTML Pages -------------
@app.route("/")
def index():
    # 預設顯示未完成在前、再按到期日排序
    tasks = Task.query.order_by(Task.done.asc(), Task.due_date.is_(None), Task.due_date.asc()).all()
    return render_template("index.html", tasks=tasks)

@app.route("/tasks/new")
def new_task():
    return render_template("new.html")

@app.route("/tasks", methods=["POST"])
def create_task():
    title = request.form.get("title", "").strip()
    notes = request.form.get("notes", "").strip()
    due = request.form.get("due_date", "").strip()
    if not title:
        return render_template("new.html", error="請輸入任務名稱", title=title, notes=notes, due_date=due), 400

    due_date = None
    if due:
        try:
            due_date = date.fromisoformat(due)
        except ValueError:
            return render_template("new.html", error="到期日格式錯誤（yyyy-mm-dd）", title=title, notes=notes, due_date=due), 400

    task = Task(title=title, notes=notes or None, due_date=due_date, done=False)
    db.session.add(task)
    db.session.commit()
    return redirect(url_for("show_task", task_id=task.id))

@app.route("/tasks/<int:task_id>")
def show_task(task_id):
    task = Task.query.get_or_404(task_id)
    return render_template("post.html", task=task)   # 檔名仍用 post.html，但內容是任務

@app.route("/tasks/<int:task_id>/edit")
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    return render_template("edit.html", task=task)

@app.route("/tasks/<int:task_id>", methods=["POST"])
def update_task(task_id):
    task = Task.query.get_or_404(task_id)
    title = request.form.get("title", "").strip()
    notes = request.form.get("notes", "").strip()
    due = request.form.get("due_date", "").strip()
    done = request.form.get("done") == "on"

    if not title:
        return render_template("edit.html", task=task, error="請輸入任務名稱"), 400

    task.title = title
    task.notes = notes or None
    if due:
        try:
            task.due_date = date.fromisoformat(due)
        except ValueError:
            return render_template("edit.html", task=task, error="到期日格式錯誤（yyyy-mm-dd）"), 400
    else:
        task.due_date = None
    task.done = done

    db.session.commit()
    return redirect(url_for("show_task", task_id=task.id))

@app.route("/tasks/<int:task_id>/delete", methods=["POST"])
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for("index"))

# ------------- 簡單 REST API（可留作加分） -------------
@app.route("/api/tasks")
def api_list_tasks():
    tasks = Task.query.order_by(Task.created_at.desc()).all()
    return jsonify([t.to_dict() for t in tasks])

@app.route("/api/tasks/<int:task_id>")
def api_get_task(task_id):
    task = Task.query.get_or_404(task_id)
    return jsonify(task.to_dict())

if __name__ == "__main__":
    app.run(debug=True)
