from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='user')  # admin, user
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Projeto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    areas = db.relationship('Area', backref='projeto', lazy=True, cascade='all, delete-orphan')
    modulos = db.relationship('Modulo', backref='projeto', lazy=True, cascade='all, delete-orphan')  # Esta linha deve existir

class Area(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    projeto_id = db.Column(db.Integer, db.ForeignKey('projeto.id'), nullable=False)
    ambientes = db.relationship('Ambiente', backref='area', lazy=True, cascade='all, delete-orphan')

    __table_args__ = (db.UniqueConstraint('nome', 'projeto_id', name='unique_area_por_projeto'),)

class Ambiente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    area_id = db.Column(db.Integer, db.ForeignKey('area.id'), nullable=False)
    circuitos = db.relationship('Circuito', backref='ambiente', lazy=True, cascade='all, delete-orphan')
    
    __table_args__ = (db.UniqueConstraint('nome', 'area_id', name='unique_ambiente_por_area'),)

class Circuito(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    identificador = db.Column(db.String(50), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    ambiente_id = db.Column(db.Integer, db.ForeignKey('ambiente.id'), nullable=False)
    sak = db.Column(db.Integer, nullable=True)
    quantidade_saks = db.Column(db.Integer, default=1)  # Novo campo
    vinculacao = db.relationship('Vinculacao', backref='circuito', uselist=False, cascade='all, delete-orphan')

    __table_args__ = (db.UniqueConstraint('identificador', 'ambiente_id', name='unique_circuito_por_ambiente'),)

class Modulo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    quantidade_canais = db.Column(db.Integer, nullable=False)
    projeto_id = db.Column(db.Integer, db.ForeignKey('projeto.id'), nullable=False)
    vinculacoes = db.relationship('Vinculacao', backref='modulo', lazy=True, cascade='all, delete-orphan')

    __table_args__ = (db.UniqueConstraint('nome', 'projeto_id', name='unique_modulo_por_projeto'),)

class Vinculacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    circuito_id = db.Column(db.Integer, db.ForeignKey('circuito.id'), nullable=False, unique=True)
    modulo_id = db.Column(db.Integer, db.ForeignKey('modulo.id'), nullable=False)
    canal = db.Column(db.Integer, nullable=False)
    
    __table_args__ = (db.UniqueConstraint('modulo_id', 'canal', name='unique_canal_por_modulo'),)