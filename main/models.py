from main.config import Config_db, Config_app
from sqlalchemy.orm import relationship
from main import db
import datetime

class AuthModel(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    password = db.Column(db.String(100))
    active = db.Column(db.BOOLEAN, default=False)
    created_at = db.Column(db.DATETIME, default=datetime.datetime.utcnow)

    the_book = relationship("BookModel", backref = "users")

class BookModel(db.Model):
    __tablename__ = "book"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    description = db.Column(db.String(100))
    content = db.Column(db.String(100))
    created_at = db.Column(db.DATETIME, default=datetime.datetime.utcnow)
    deleted = db.Column(db.String(100), default=None)

    create_by_id = db.Column(db.Text, db.ForeignKey("users.id"))

db.create_all()
