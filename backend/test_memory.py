#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
长期记忆功能测试脚本
"""

import sys
import os
import numpy as np
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from app import app, db
from models import User, Conversation
from services.ai_service import search_relevant_conversations, build_context_with_memory
from services.embedding_service import get_text_embedding
from werkzeug.security import generate_password_hash

def test_long_term_memory():
    """测试长期记忆功能"""
    print("开始测试长期记忆功能...")
    
    # 在应用上下文中运行
    with app.app_context():
        # 创建数据库表
        db.create_all()
        print("=== 长期记忆功能测试 ===")
        
        # 清理现有数据
        Conversation.query.delete()
        User.query.delete()
        db.session.commit()
        
        # 创建测试用户
        test_user = User(
            email='test@example.com',
            password_hash=generate_password_hash('testpassword')
        )
        db.session.add(test_user)
        db.session.commit()
        
        print(f"创建测试用户: {test_user.email} (ID: {test_user.id})")
        
        # 模拟历史对话数据
        conversations = [
            {"user_message": "我喜欢编程", "ai_response": "编程是一项很有趣的技能！你最喜欢哪种编程语言？"},
            {"user_message": "我在学习Python", "ai_response": "Python是一门很棒的语言，适合初学者，也很强大。"},
            {"user_message": "我想做一个网站", "ai_response": "你可以使用Flask或Django来构建Python网站。"},
            {"user_message": "我喜欢看电影", "ai_response": "看电影是很好的娱乐方式！你喜欢什么类型的电影？"},
            {"user_message": "我在学习机器学习", "ai_response": "机器学习很有前景！建议从基础的算法开始学习。"}
        ]
        
        print("\n添加历史对话数据...")
        for i, conv in enumerate(conversations):
            # 为用户消息生成向量
            embedding_list = get_text_embedding(conv["user_message"])
            
            # 保存用户消息到数据库（包含向量）
            user_conversation = Conversation(
                user_id=test_user.id,
                content=conv["user_message"],
                role='user',
                embedding=np.array(embedding_list),
                timestamp=datetime.utcnow() - timedelta(days=i+1)
            )
            db.session.add(user_conversation)
            
            # 保存AI回复到数据库
            ai_conversation = Conversation(
                user_id=test_user.id,
                content=conv["ai_response"],
                role='ai',
                timestamp=datetime.utcnow() - timedelta(days=i+1, seconds=30)
            )
            db.session.add(ai_conversation)
            
            print(f"添加对话 {i+1}: {conv['user_message'][:30]}...")
        
        db.session.commit()
        print("\n历史对话数据添加完成！")
        
        # 查询所有对话记录
        all_conversations = Conversation.query.filter_by(user_id=test_user.id).all()
        print(f"\n数据库中共有 {len(all_conversations)} 条对话记录:")
        for conv in all_conversations:
            embedding_preview = str(conv.embedding)[:50] + "..." if conv.embedding is not None else "None"
            print(f"- {conv.role}: {conv.content} (embedding: {embedding_preview})")
        
        # 测试相关对话搜索
        print("\n=== 测试相关对话搜索 ===")
        query_message = "我想学习编程语言"
        print(f"查询消息: {query_message}")
        
        relevant_conversations = search_relevant_conversations(query_message, test_user.id, limit=3)
        print(f"\n找到 {len(relevant_conversations)} 条相关对话:")
        for conv in relevant_conversations:
            print(f"- {conv['user_message']} (相似度: {conv['similarity']:.4f})")
            if conv['ai_response']:
                print(f"  AI回复: {conv['ai_response']}")
        
        # 测试上下文构建
        print("\n=== 测试上下文构建 ===")
        context = build_context_with_memory(query_message, test_user.id)
        print(f"构建的上下文:\n{context}")
        
        print("=== 长期记忆功能测试完成 ===")

if __name__ == '__main__':
    test_long_term_memory()