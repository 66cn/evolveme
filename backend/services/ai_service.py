import requests
import json
from typing import List, Dict, Any
from .embedding_service import get_text_embedding, calculate_similarity

# 火山引擎方舟平台（豆包模型）的API Key
# 注意：在生产环境中，此密钥应该从环境变量中读取
# VOLC_ARK_API_KEY = os.getenv('VOLC_ARK_API_KEY')

# 开发阶段临时硬编码（生产环境必须替换为环境变量）
VOLC_ARK_API_KEY = "4f16bd13-8986-4177-9a70-354315a3eb30"  # 使用真实的API Key

# 豆包大模型API端点
API_ENDPOINT = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"

def search_relevant_conversations(user_content: str, user_id: int, limit: int = 5) -> List[Dict[str, Any]]:
    """
    搜索与用户输入相关的历史对话
    
    Args:
        user_content (str): 用户输入内容
        user_id (int): 用户ID
        limit (int): 返回的相关对话数量限制
        
    Returns:
        List[Dict]: 相关的历史对话列表
    """
    from models import Conversation
    
    # 生成用户输入的向量
    user_embedding = get_text_embedding(user_content)
    
    # 获取用户的所有历史对话（只获取用户消息，不包括AI回复）
    user_conversations = Conversation.query.filter_by(
        user_id=user_id, 
        role='user'
    ).filter(
        Conversation.embedding_json.isnot(None)
    ).all()
    
    # 计算相似度并排序
    conversation_similarities = []
    for conv in user_conversations:
        if conv.embedding is not None:
            similarity = calculate_similarity(user_embedding, conv.embedding)
            conversation_similarities.append({
                'conversation': conv,
                'similarity': similarity
            })
    
    # 按相似度降序排序
    conversation_similarities.sort(key=lambda x: x['similarity'], reverse=True)
    
    # 返回最相关的对话
    relevant_conversations = []
    for item in conversation_similarities[:limit]:
        conv = item['conversation']
        
        # 获取对应的AI回复
        ai_response = Conversation.query.filter_by(
            user_id=user_id,
            role='ai'
        ).filter(
            Conversation.timestamp > conv.timestamp
        ).order_by(Conversation.timestamp.asc()).first()
        
        relevant_conversations.append({
            'user_message': conv.content,
            'ai_response': ai_response.content if ai_response else None,
            'timestamp': conv.timestamp.isoformat(),
            'similarity': item['similarity']
        })
    
    return relevant_conversations

def build_context_with_memory(user_content: str, user_id: int) -> List[Dict[str, str]]:
    """
    构建包含长期记忆的对话上下文
    
    Args:
        user_content (str): 用户输入内容
        user_id (int): 用户ID
        
    Returns:
        List[Dict]: 构建好的消息列表
    """
    messages = [
        {
            "role": "system",
            "content": "你是EvolveMe的AI教练，专注于帮助用户实现个人成长和目标达成。请以友好、专业、鼓励的语气回复用户。你具有长期记忆能力，能够记住用户之前的对话内容，并在回复中体现出对用户情况的了解和关注。**重要：你的所有回复都必须使用Markdown格式进行排版，以便于阅读。例如，使用`**标题**`、`- 列表`和`1. 数字列表`等。**"
        }
    ]
    
    # 搜索相关的历史对话
    relevant_conversations = search_relevant_conversations(user_content, user_id, limit=3)
    
    # 如果有相关的历史对话，添加到上下文中
    if relevant_conversations:
        context_content = "\n\n基于我们之前的对话，我记得：\n"
        for i, conv in enumerate(relevant_conversations, 1):
            if conv['similarity'] > 0.3:  # 只包含相似度较高的对话
                context_content += f"{i}. 你曾经说过：\"{conv['user_message']}\"\n"
                if conv['ai_response']:
                    context_content += f"   我当时回复：\"{conv['ai_response'][:100]}...\"\n"
        
        context_content += "\n请结合这些历史信息来回复用户的新问题。"
        
        messages.append({
            "role": "system",
            "content": context_content
        })
    
    # 添加当前用户消息
    messages.append({
        "role": "user",
        "content": user_content
    })
    
    return messages

def get_llm_response(user_content: str, user_id: int = None) -> str:
    """
    调用火山引擎豆包大模型API获取AI回复
    
    Args:
        user_content (str): 用户输入的消息内容
        user_id (int): 用户ID，用于长期记忆功能
        
    Returns:
        str: AI生成的回复内容
    """
    try:
        # 构造请求头
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {VOLC_ARK_API_KEY}"
        }
        
        # 构建包含长期记忆的消息上下文
        if user_id:
            messages = build_context_with_memory(user_content, user_id)
        else:
            # 如果没有用户ID，使用基础上下文
            messages = [
                {
                    "role": "system",
                    "content": "你是EvolveMe的AI教练，专注于帮助用户实现个人成长和目标达成。请以友好、专业、鼓励的语气回复用户。**重要：你的所有回复都必须使用Markdown格式进行排版，以便于阅读。例如，使用`**标题**`、`- 列表`和`1. 数字列表`等。**"
                },
                {
                    "role": "user",
                    "content": user_content
                }
            ]
        
        # 构造请求体
        payload = {
            "model": "doubao-seed-1-6-thinking-250615",  # 豆包模型的endpoint ID
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        # [DEBUG] 打印完整的请求载荷
        print("--- [DEBUG] PAYLOAD SENT TO VOLCENGINE ---")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        
        # 发送POST请求到豆包API
        response = requests.post(
            API_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=55  # 新增：设置55秒的后端请求超时
        )
        
        # 检查响应状态
        if response.status_code == 200:
            response_data = response.json()
            
            # 提取AI回复内容
            if "choices" in response_data and len(response_data["choices"]) > 0:
                ai_reply = response_data["choices"][0]["message"]["content"]
                return ai_reply.strip()
            else:
                return "抱歉，我现在无法生成回复，请稍后再试。"
        else:
            print(f"API请求失败，状态码: {response.status_code}")
            print(f"错误信息: {response.text}")
            return "抱歉，AI服务暂时不可用，请稍后再试。"
            
    except requests.exceptions.Timeout:
        print("API请求超时")
        return "抱歉，响应超时，请稍后再试。"
    except requests.exceptions.RequestException as e:
        print(f"网络请求错误: {str(e)}")
        return "抱歉，网络连接出现问题，请检查网络后重试。"
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {str(e)}")
        return "抱歉，响应格式错误，请稍后再试。"
    except Exception as e:
        print(f"未知错误: {str(e)}")
        return "抱歉，发生了未知错误，请稍后再试。"