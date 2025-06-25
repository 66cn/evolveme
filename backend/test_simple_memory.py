# -*- coding: utf-8 -*-
"""
简化的长期记忆功能测试脚本
"""

import sys
import os
import numpy as np
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from app import app, db
from models import User, Conversation
from services.embedding_service import get_text_embedding, calculate_similarity
from werkzeug.security import generate_password_hash

def test_simple_memory():
    """简化的长期记忆功能测试"""
    print("开始简化的长期记忆功能测试...")
    
    # 在应用上下文中运行所有操作
    with app.app_context():
        # 创建数据库表
        db.create_all()
        print("=== 简化长期记忆功能测试 ===")
        
        # 清理现有数据
        Conversation.query.delete()
        User.query.delete()
        db.session.commit()
        
        # 创建测试用户
        test_user = User(
            username='testuser',
            email='test@example.com',
            password_hash=generate_password_hash('testpassword')
        )
        db.session.add(test_user)
        db.session.commit()
        
        print(f"创建测试用户: {test_user.username} (ID: {test_user.id})")
        
        # 测试向量生成
        print("\n=== 测试向量生成 ===")
        test_text = "我喜欢编程"
        embedding = get_text_embedding(test_text)
        print(f"文本: {test_text}")
        print(f"向量维度: {len(embedding)}")
        print(f"向量前5个值: {embedding[:5]}")
        
        # 保存带向量的对话
        print("\n=== 测试向量存储 ===")
        conversation = Conversation(
            user_id=test_user.id,
            content=test_text,
            role='user',
            embedding=np.array(embedding),
            timestamp=datetime.utcnow()
        )
        db.session.add(conversation)
        db.session.commit()
        print("成功保存带向量的对话")
        
        # 查询并验证向量
        print("\n=== 测试向量查询 ===")
        saved_conv = Conversation.query.filter_by(user_id=test_user.id).first()
        if saved_conv and saved_conv.embedding is not None:
            print(f"查询到对话: {saved_conv.content}")
            print(f"向量维度: {len(saved_conv.embedding)}")
            print(f"向量前5个值: {saved_conv.embedding[:5]}")
            
            # 测试相似度计算
            print("\n=== 测试相似度计算 ===")
            query_text = "我想学习编程"
            query_embedding = get_text_embedding(query_text)
            similarity = calculate_similarity(query_embedding, saved_conv.embedding)
            print(f"查询文本: {query_text}")
            print(f"与存储对话的相似度: {similarity:.4f}")
            
            # 添加更多测试数据
            print("\n=== 添加更多测试数据 ===")
            test_messages = [
                "我在学习Python",
                "我想做一个网站",
                "我喜欢看电影",
                "今天天气很好"
            ]
            
            for i, msg in enumerate(test_messages):
                msg_embedding = get_text_embedding(msg)
                conv = Conversation(
                    user_id=test_user.id,
                    content=msg,
                    role='user',
                    embedding=np.array(msg_embedding),
                    timestamp=datetime.utcnow() - timedelta(minutes=i*10)
                )
                db.session.add(conv)
                print(f"添加对话: {msg}")
            
            db.session.commit()
            
            # 测试相似度搜索
            print("\n=== 测试相似度搜索 ===")
            query_text = "编程学习"
            query_embedding = get_text_embedding(query_text)
            
            # 获取所有用户对话
            all_conversations = Conversation.query.filter_by(
                user_id=test_user.id, 
                role='user'
            ).filter(
                Conversation.embedding.isnot(None)
            ).all()
            
            # 计算相似度并排序
            similarities = []
            for conv in all_conversations:
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
        
        else:
            print("未找到保存的对话或向量为空")
        
        print("\n=== 简化长期记忆功能测试完成 ===")

if __name__ == '__main__':
    test_simple_memory()