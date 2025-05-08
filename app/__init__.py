from datetime import UTC, datetime
import random
from flask import Flask, abort, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
from markupsafe import escape

db = SQLAlchemy()

NOTE_COLORS = ['#FFFB7D', '#C2F0FF', '#C7FFB5', '#FFC2E2', '#FFD59E']

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    x = db.Column(db.Integer, nullable=False)
    y = db.Column(db.Integer, nullable=False)
    color = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now(UTC))

    def to_dict(self):
        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "color": self.color,
            "content": self.content,
        }


def create_app(database: str, testing: bool = False, **kwargs):
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        {
            **{
                "SQLALCHEMY_DATABASE_URI": f"sqlite:///{database}",
                "SQLALCHEMY_TRACK_MODIFICATIONS": False,
                "TESTING": testing,
            },
            **kwargs,
        }
    )

    db.init_app(app)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/api/notes", methods=["GET"])
    def get_notes():
        notes = Note.query.all()
        return jsonify([note.to_dict() for note in notes])

    @app.route("/api/notes", methods=["POST"])
    def create_note():
        data = request.get_json()
        x = data.get("x", 40)
        y = data.get("y", 40)
        if not isinstance(x, int) or not isinstance(y, int):
            return jsonify({'message': "x and y must be integers"}), 400

        note = Note(
            x=x,
            y=y,
            color=random.choice(NOTE_COLORS),
            content=escape(data.get("content", "")),
        )
        db.session.add(note)
        db.session.commit()
        return jsonify(note.to_dict())

    @app.route("/api/notes/<int:note_id>", methods=["GET"])
    def get_note(note_id):
        note = db.session.get(Note, note_id)
        if note is None:
            abort(404)
        return jsonify(note.to_dict())

    @app.route("/api/notes/<int:note_id>", methods=["PUT"])
    def update_note(note_id):
        note = db.session.get(Note, note_id)

        if note is None:
            abort(404)

        data = request.get_json()
        x = data.get("x", 40)
        y = data.get("y", 40)
        if not isinstance(x, int) or not isinstance(y, int):
            return jsonify({'message': "x and y must be integers"}), 400

        note.x = x
        note.y = y
        new_content = data.get("content", None)
        if new_content is not None:
            note.content = escape(new_content)
        db.session.commit()
        return jsonify(note.to_dict())

    @app.route("/api/notes/<int:note_id>", methods=["DELETE"])
    def delete_note(note_id):
        note = db.session.get(Note, note_id)

        if note is None:
            abort(404)

        db.session.delete(note)
        db.session.commit()
        return jsonify({"message": "Note deleted"})

    with app.app_context():
        db.create_all()

    return app
