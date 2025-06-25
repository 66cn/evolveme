# -*- coding: utf-8 -*-
"""
基础的长期记忆功能测试脚本（不依赖pgvector）
"""

import sys
import os
import json
import numpy as np
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash

# 手动初始化Flask应用
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_memory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化数据库
db = SQLAlchemy(app)

# 定义简化的模型（不使用pgvector）
class TestUser(db.Model):
    __tablename__ = 'test_users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

class TestConversation(db.Model):
    __tablename__ = 'test_conversations'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('test_users.id'), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'user' 或 'ai'
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    # 将向量存储为JSON字符串
    embedding_json = db.Column(db.Text, nullable=True)
    
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

# 导入embedding服务
from services.embedding_service import get_text_embedding, calculate_similarity

def test_basic_memory():
    """基础的长期记忆功能测试"""
    print("开始基础的长期记忆功能测试...")
    
    # 在应用上下文中运行所有操作
    with app.app_context():
        # 创建数据库表
        db.create_all()
        print("=== 基础长期记忆功能测试 ===")
        
        # 清理现有数据
        try:
            TestConversation.query.delete()
            TestUser.query.delete()
            db.session.commit()
            print("清理现有数据完成")
        except Exception as e:
            print(f"清理数据时出错: {e}")
            db.session.rollback()
        
        # 创建测试用户
        try:
            test_user = TestUser(
                username='testuser',
                email='test@example.com',
                password_hash=generate_password_hash('testpassword')
            )
            db.session.add(test_user)
            db.session.commit()
            print(f"创建测试用户: {test_user.username} (ID: {test_user.id})")
        except Exception as e:
            print(f"创建用户时出错: {e}")
            db.session.rollback()
            return
        
        # 测试向量生成
        print("\n=== 测试向量生成 ===")
        try:
            test_text = "我喜欢编程"
            embedding = get_text_embedding(test_text)
            print(f"文本: {test_text}")
            print(f"向量维度: {len(embedding)}")
            print(f"向量前5个值: {embedding[:5]}")
            print(f"向量类型: {type(embedding)}")
        except Exception as e:
            print(f"向量生成时出错: {e}")
            return
        
        # 保存带向量的对话
        print("\n=== 测试向量存储 ===")
        try:
            conversation = TestConversation(
                user_id=test_user.id,
                content=test_text,
                role='user',
                timestamp=datetime.utcnow()
            )
            # 设置向量
            conversation.embedding = embedding
            
            db.session.add(conversation)
            db.session.commit()
            print("成功保存带向量的对话")
        except Exception as e:
            print(f"向量存储时出错: {e}")
            print(f"错误类型: {type(e)}")
            db.session.rollback()
            return
        
        # 查询并验证
        print("\n=== 测试数据查询 ===")
        try:
            saved_conv = TestConversation.query.filter_by(user_id=test_user.id).first()
            if saved_conv:
                print(f"查询到对话: {saved_conv.content}")
                print(f"对话角色: {saved_conv.role}")
                print(f"向量是否为空: {saved_conv.embedding is None}")
                if saved_conv.embedding is not None:
                    print(f"向量维度: {len(saved_conv.embedding)}")
                    print(f"向量前5个值: {saved_conv.embedding[:5]}")
                    
                    # 测试相似度计算
                    print("\n=== 测试相似度计算 ===")
                    query_text = "我想学习编程"
                    query_embedding = get_text_embedding(query_text)
                    similarity = calculate_similarity(query_embedding, saved_conv.embedding)
                    print(f"查询文本: {query_text}")
                    print(f"与存储对话的相似度: {similarity:.4f}")
                else:
                    print("向量为空，跳过相似度测试")
            else:
                print("未找到保存的对话")
        except Exception as e:
            print(f"查询数据时出错: {e}")
        
        # 添加更多测试数据
        print("\n=== 添加更多测试数据 ===")
        test_messages = [
            "我在学习Python",
            "我想做一个网站", 
            "我喜欢看电影",
            "今天天气很好"
        ]
        
        try:
            for i, msg in enumerate(test_messages):
                msg_embedding = get_text_embedding(msg)
                conv = TestConversation(
                    user_id=test_user.id,
                    content=msg,
                    role='user',
                    timestamp=datetime.utcnow() - timedelta(minutes=i*10)
                )
                conv.embedding = msg_embedding
                db.session.add(conv)
                print(f"添加对话: {msg}")
            
            db.session.commit()
            print("所有测试数据添加完成")
        except Exception as e:
            print(f"添加测试数据时出错: {e}")
            db.session.rollback()
        
        # 测试相似度搜索
        print("\n=== 测试相似度搜索 ===")
        try:
            query_text = "编程学习"
            query_embedding = get_text_embedding(query_text)
            
            # 获取所有用户对话
            all_conversations = TestConversation.query.filter_by(
                user_id=test_user.id, 
                role='user'
            ).filter(
                TestConversation.embedding_json.isnot(None)
            ).all()
            
            print(f"找到 {len(all_conversations)} 条带向量的对话")
            
            # 计算相似度并排序
            similarities = []
            for conv in all_conversations:
                if conv.embedding is not None:
                    similarity = calculate_similarity(query_embedding, conv.embedding)
                    similarities.append({
                        'content': conv.content,
                        'similarity': similarity,
                        'timestamp': conv.timestamp
                    })
            
            # 按相似度排序
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            
            print(f"查询: {query_text}")
            print("相关对话 (按相似度排序):")
            for i, item in enumerate(similarities[:3], 1):
                print(f"{i}. {item['content']} (相似度: {item['similarity']:.4f})")
                
        except Exception as e:
            print(f"相似度搜索时出错: {e}")
        
        print("\n=== 基础长期记忆功能测试完成 ===")

if __name__ == '__main__':
    test_basic_memory()