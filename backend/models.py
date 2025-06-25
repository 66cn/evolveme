from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json
import numpy as np

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        """设置密码，使用加盐哈希存储"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email}>'


class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'user' 或 'ai'
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    embedding_json = db.Column(db.Text, nullable=True)  # 向量嵌入字段（JSON格式）
    
    @property
    def embedding(self):
        """获取向量数据"""
        if self.embedding_json:
            return np.array(json.loads(self.embedding_json))
        return None
    
    @embedding.setter
    def embedding(self, value):
        """设置向量数据"""
        if value is not None:
            if isinstance(value, np.ndarray):
                self.embedding_json = json.dumps(value.tolist())
            elif isinstance(value, list):
                self.embedding_json = json.dumps(value)
            else:
                self.embedding_json = json.dumps(list(value))
        else:
            self.embedding_json = None
    
    # 建立与User模型的关系
    user = db.relationship('User', backref=db.backref('conversations', lazy=True))
    
    def __repr__(self):
        return f'<Conversation {self.id}: {self.role} - {self.content[:50]}...>'