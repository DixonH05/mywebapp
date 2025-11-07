from flask import Flask, render_template, request, redirect, url_for, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)

# SQLite DB file path
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(BASE_DIR, "blog.db")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_path
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    author = db.Column(db.String(80), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "author": self.author,
            "content": self.content,
            "created_at": self.created_at.isoformat()
        }

# Initialize database if not exists
with app.app_context():
    db.create_all()

# ---------- HTML PAGES ----------

@app.route("/")
def index():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template("index.html", posts=posts)

@app.route("/posts/new")
def new_post():
    return render_template("new.html")

@app.route("/posts", methods=["POST"])
def create_post():
    title = request.form.get("title", "").strip()
    author = request.form.get("author", "").strip()
    content = request.form.get("content", "").strip()
    if not title or not author or not content:
        return render_template("new.html", error="All fields are required.", title=title, author=author, content=content), 400
    post = Post(title=title, author=author, content=content)
    db.session.add(post)
    db.session.commit()
    return redirect(url_for("show_post", post_id=post.id))

@app.route("/posts/<int:post_id>")
def show_post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template("post.html", post=post)

@app.route("/posts/<int:post_id>/edit")
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template("edit.html", post=post)

@app.route("/posts/<int:post_id>", methods=["POST"])
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    title = request.form.get("title", "").strip()
    author = request.form.get("author", "").strip()
    content = request.form.get("content", "").strip()
    if not title or not author or not content:
        return render_template("edit.html", post=post, error="All fields are required.")
    post.title = title
    post.author = author
    post.content = content
    db.session.commit()
    return redirect(url_for("show_post", post_id=post.id))

@app.route("/posts/<int:post_id>/delete", methods=["POST"])
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for("index"))

# ---------- RESTful API ----------

@app.route("/api/posts", methods=["GET"])
def api_list_posts():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return jsonify([p.to_dict() for p in posts])

@app.route("/api/posts/<int:post_id>", methods=["GET"])
def api_get_post(post_id):
    post = Post.query.get_or_404(post_id)
    return jsonify(post.to_dict())

@app.route("/api/posts", methods=["POST"])
def api_create_post():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    author = (data.get("author") or "").strip()
    content = (data.get("content") or "").strip()
    if not title or not author or not content:
        return jsonify({"error": "title, author, content are required"}), 400
    post = Post(title=title, author=author, content=content)
    db.session.add(post)
    db.session.commit()
    return jsonify(post.to_dict()), 201

@app.route("/api/posts/<int:post_id>", methods=["PUT"])
def api_update_post(post_id):
    post = Post.query.get_or_404(post_id)
    data = request.get_json(silent=True) or {}
    if "title" in data: post.title = data["title"]
    if "author" in data: post.author = data["author"]
    if "content" in data: post.content = data["content"]
    db.session.commit()
    return jsonify(post.to_dict())

@app.route("/api/posts/<int:post_id>", methods=["DELETE"])
def api_delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    return "", 204

if __name__ == "__main__":
    # For local run
    app.run(debug=True)
