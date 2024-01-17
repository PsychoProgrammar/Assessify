from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.String(255), nullable=False)
    option_a = db.Column(db.String(50), nullable=False)
    option_b = db.Column(db.String(50), nullable=False)
    option_c = db.Column(db.String(50), nullable=False)
    option_d = db.Column(db.String(50), nullable=False)
    correct_option = db.Column(db.String(1), nullable=False)

def init_app(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()