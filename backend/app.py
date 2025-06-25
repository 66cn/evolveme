from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
from models import db, User, Conversation
from services.ai_service import get_llm_response
import os

# 生产环境API密钥配置示例（开发阶段可暂时不用）
# VOLCENGINE_API_KEY = os.getenv('VOLCENGINE_API_KEY')
# VOLCENGINE_SECRET_KEY = os.getenv('VOLCENGINE_SECRET_KEY')

app = Flask(__name__)

# 配置CORS，允许来自前端http://localhost:3000的请求
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})

# 数据库配置
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# JWT配置
app.config['JWT_SECRET_KEY'] = 'your-secret-string-here'  # 在生产环境中应使用环境变量

# 初始化扩展
db.init_app(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)

# SQLite数据库配置（不需要pgvector扩展）

@app.route('/api/health')
def health_check():
    return jsonify({"status": "ok"})

@app.route('/api/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'error': '邮箱和密码都是必需的'}), 400
        
        email = data['email']
        password = data['password']
        
        # 检查邮箱是否已存在
        if User.query.filter_by(email=email).first():
            return jsonify({'error': '邮箱已存在'}), 400
        
        # 创建新用户
        user = User(email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({'message': '用户注册成功'}), 201
        
    except Exception as e:
        return jsonify({'error': '注册失败'}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'error': '邮箱和密码都是必需的'}), 400
        
        email = data['email']
        password = data['password']
        
        # 查找用户
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            # 创建访问令牌
            access_token = create_access_token(identity=str(user.id))
            return jsonify({
                'access_token': access_token,
                'message': '登录成功'
            }), 200
        else:
            return jsonify({'error': '邮箱或密码错误'}), 401
            
    except Exception as e:
        return jsonify({'error': '登录失败'}), 500

@app.route('/api/conversations', methods=['GET'])
@jwt_required()
def get_conversations():
    try:
        # 获取当前用户ID（字符串类型，需要转换为整数）
        current_user_id = int(get_jwt_identity())
        
        # 查询该用户的所有对话记录，按时间升序排列
        conversations = Conversation.query.filter_by(user_id=current_user_id).order_by(Conversation.timestamp.asc()).all()
        
        # 转换为JSON格式
        conversations_data = []
        for conv in conversations:
            conversations_data.append({
                'id': conv.id,
                'role': conv.role,
                'content': conv.content,
                'timestamp': conv.timestamp.isoformat()
            })
        
        return jsonify({'conversations': conversations_data}), 200
        
    except Exception as e:
        print(f"An error occurred in {request.endpoint}: {e}")
        app.logger.error(f"Error in get_conversations: {str(e)}")
        return jsonify({'error': '获取对话历史失败'}), 500

@app.route('/api/conversations', methods=['POST'])
@jwt_required()
def handle_conversation():
    try:
        # 获取当前用户ID
        current_user_id = get_jwt_identity()
        
        # 获取请求数据
        data = request.get_json()
        
        # 强化输入验证 - 支持message和content两种字段名
        message_content = data.get('message') or data.get('content')
        if not data or not message_content or not str(message_content).strip():
            return jsonify({'error': '消息内容不能为空'}), 400
        
        user_message = str(message_content).strip()
        
        # 生成用户消息的向量
        from services.embedding_service import get_text_embedding
        import numpy as np
        user_embedding = np.array(get_text_embedding(user_message))
        
        # 调用AI服务获取回复（传入用户ID以启用长期记忆）
        ai_response = get_llm_response(user_message, current_user_id)
        
        # 保存用户消息到数据库（包含向量）
        user_conversation = Conversation(
            user_id=current_user_id,
            content=user_message,
            role='user',
            embedding=user_embedding
        )
        db.session.add(user_conversation)
        
        # 保存AI回复到数据库
        ai_conversation = Conversation(
            user_id=current_user_id,
            content=ai_response,
            role='ai'
        )
        db.session.add(ai_conversation)
        
        # 提交数据库事务
        db.session.commit()
        
        # 返回AI回复
        return jsonify({
            'id': ai_conversation.id,
            'role': 'ai',
            'content': ai_response,
            'timestamp': ai_conversation.timestamp.isoformat()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"对话处理错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

if __name__ == '__main__':
    app.run(debug=True)