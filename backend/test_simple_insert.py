# -*- coding: utf-8 -*-
"""
简单的数据库插入测试
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User, Conversation
from werkzeug.security import generate_password_hash
from services.embedding_service import get_text_embedding
from datetime import datetime
import numpy as np

def test_simple_insert():
    """简单的数据库插入测试"""
    print("开始简单插入测试...")
    
    with app.app_context():
        # 创建数据库表
        db.create_all()
        print("数据库表创建完成")
        
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
                email='test@example.com',
                password_hash=generate_password_hash('testpassword')
            )
            db.session.add(test_user)
            db.session.commit()
            print(f"创建测试用户成功: {test_user.email} (ID: {test_user.id})")
        except Exception as e:
            print(f"创建用户时出错: {e}")
            db.session.rollback()
            return
        
        # 测试单个对话插入
        try:
            print("\n测试单个对话插入...")
            
            # 生成向量
            test_message = "我喜欢编程"
            embedding = get_text_embedding(test_message)
            print(f"生成向量成功，维度: {len(embedding)}")
            
            # 创建对话记录
            conversation = Conversation(
                user_id=test_user.id,
                content=test_message,
                role='user',
                timestamp=datetime.utcnow()
            )
            
            # 设置向量
            conversation.embedding = embedding
            print("向量设置成功")
            
            # 保存到数据库
            db.session.add(conversation)
            db.session.commit()
            print("对话保存成功")
            
            # 验证保存
            saved_conv = Conversation.query.filter_by(user_id=test_user.id).first()
            if saved_conv:
                print(f"验证成功: {saved_conv.content}")
                print(f"向量是否存在: {saved_conv.embedding is not None}")
                if saved_conv.embedding is not None:
                    print(f"向量维度: {len(saved_conv.embedding)}")
            else:
                print("验证失败: 未找到保存的对话")
                
        except Exception as e:
            print(f"插入对话时出错: {e}")
            print(f"错误类型: {type(e)}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
        
        print("\n简单插入测试完成")

if __name__ == '__main__':
    test_simple_insert()