from datetime import datetime
from app import db

class Cliente(db.Model):
    __tablename__ = 'clientes'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    obras = db.relationship('Obra', backref='cliente', lazy=True, cascade='all, delete-orphan')

class Obra(db.Model):
    __tablename__ = 'obras'
    
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    registros = db.relationship('RegistroFotografico', backref='obra', lazy=True, cascade='all, delete-orphan')

class RegistroFotografico(db.Model):
    __tablename__ = 'registros'
    
    id = db.Column(db.Integer, primary_key=True)
    obra_id = db.Column(db.Integer, db.ForeignKey('obras.id'), nullable=False)
    nome_quadro = db.Column(db.String(100), nullable=False)
    data_upload = db.Column(db.DateTime, default=datetime.utcnow)
    
    fotos = db.relationship('Foto', backref='registro', lazy=True, cascade='all, delete-orphan')

class Foto(db.Model):
    __tablename__ = 'fotos'
    
    id = db.Column(db.Integer, primary_key=True)
    registro_id = db.Column(db.Integer, db.ForeignKey('registros.id'), nullable=False)
    nome_arquivo = db.Column(db.String(255), nullable=False)
    caminho = db.Column(db.String(500), nullable=False)
    data_upload = db.Column(db.DateTime, default=datetime.utcnow)
