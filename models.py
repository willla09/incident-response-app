from flask_login import UserMixin
from database import db
from datetime import datetime
import bcrypt

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))

class Incident(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    severity = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    handler = db.Column(db.String(100), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='in-progress')
    actions = db.relationship('Action', back_populates='incident', cascade='all, delete-orphan')

class Playbook(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    created_by = db.Column(db.String(100), nullable=False)
    actions = db.relationship('Action', back_populates='playbook', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Playbook {self.name}>'

    @property
    def playbook_name(self):
        return self.name

class Action(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey('incident.id'), nullable=True)
    playbook_id = db.Column(db.Integer, db.ForeignKey('playbook.id'), nullable=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    phase = db.Column(db.String(50), nullable=False)
    assigned_to = db.Column(db.String(100), default='Not assigned')
    incident = db.relationship('Incident', back_populates='actions')
    playbook = db.relationship('Playbook', back_populates='actions')
    is_playbook = db.Column(db.Boolean, default=False)
    playbook_name = db.Column(db.String(100), nullable=True)

class TaskNotification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action_id = db.Column(db.Integer, db.ForeignKey('action.id'), nullable=False)
    incident_id = db.Column(db.Integer, db.ForeignKey('incident.id'), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('task_notifications', lazy=True))
    action = db.relationship('Action', backref=db.backref('task_notifications', lazy=True))
    incident = db.relationship('Incident', backref=db.backref('task_notifications', lazy=True))
