# -*- coding: utf-8 -*-
"""
独立的长期记忆功能测试脚本
"""

import sys
import os
import numpy as np
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event, text
from werkzeug.security import generate_password_hash

# 手动初始化Flask应用
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化数据库
db = SQLAlchemy(app)

# 注册pgvector扩展（如果使用PostgreSQL）
@event.listens_for(db.engine, "connect")
def register_vector(dbapi_connection, connection_record):
    try:
        with dbapi_connection.cursor() as cursor:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
            dbapi_connection.commit()
    except Exception as e:
        # SQLite不支持pgvector，忽略错误
        pass

# 导入模型（在数据库初始化之后）
from models import User, Conversation
from services.embedding_service import get_text_embedding, calculate_similarity

def test_standalone_memory():
    """独立的长期记忆功能测试"""
    print("开始独立的长期记忆功能测试...")
    
    # 在应用上下文中运行所有操作
    with app.app_context():
        # 创建数据库表
        db.create_all()
        print("=== 独立长期记忆功能测试 ===")
        
        # 清理现有数据
        try:
            Conversation.query.delete()
            User.query.delete()
            db.session.commit()
            print("清理现有数据完成")
        except Exception as e:
            print(f"清理数据时出错: {e}")
            db.session.rollback()
        
        # 创建测试用户
        try:
            test_user = User(
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
            # 尝试不同的向量格式
            embedding_array = np.array(embedding, dtype=np.float32)
            print(f"numpy数组类型: {type(embedding_array)}")
            print(f"numpy数组形状: {embedding_array.shape}")
            
            conversation = Conversation(
                user_id=test_user.id,
                content=test_text,
                role='user',
                embedding=embedding_array,
                timestamp=datetime.utcnow()
            )
            db.session.add(conversation)
            db.session.commit()
            print("成功保存带向量的对话")
        except Exception as e:
            print(f"向量存储时出错: {e}")
            print(f"错误类型: {type(e)}")
            db.session.rollback()
            
            # 尝试不保存向量
            try:
                conversation = Conversation(
                    user_id=test_user.id,
                    content=test_text,
                    role='user',
                    embedding=None,
                    timestamp=datetime.utcnow()
                )
                db.session.add(conversation)
                db.session.commit()
                print("成功保存不带向量的对话")
            except Exception as e2:
                print(f"保存不带向量的对话也失败: {e2}")
                db.session.rollback()
                return
        
        # 查询并验证
        print("\n=== 测试数据查询 ===")
        try:
            saved_conv = Conversation.query.filter_by(user_id=test_user.id).first()
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
        
        print("\n=== 独立长期记忆功能测试完成 ===")

if __name__ == '__main__':
    test_standalone_memory()