import hashlib
import numpy as np
from typing import List

class SimpleEmbeddingService:
    """
    简单的文本向量化服务
    使用文本哈希和简单的特征提取来生成固定维度的向量
    """
    
    def __init__(self, vector_dim: int = 384):
        self.vector_dim = vector_dim
    
    def encode(self, text: str) -> List[float]:
        """
        将文本编码为向量
        
        Args:
            text (str): 输入文本
            
        Returns:
            List[float]: 固定维度的向量
        """
        # 清理文本
        text = text.lower().strip()
        
        # 使用多个哈希函数生成不同的特征
        features = []
        
        # 1. MD5哈希特征
        md5_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        for i in range(0, len(md5_hash), 2):
            features.append(int(md5_hash[i:i+2], 16) / 255.0)
        
        # 2. SHA1哈希特征
        sha1_hash = hashlib.sha1(text.encode('utf-8')).hexdigest()
        for i in range(0, min(len(sha1_hash), 40), 2):
            features.append(int(sha1_hash[i:i+2], 16) / 255.0)
        
        # 3. 文本长度特征
        features.append(min(len(text) / 1000.0, 1.0))
        
        # 4. 字符频率特征
        char_counts = {}
        for char in text:
            char_counts[char] = char_counts.get(char, 0) + 1
        
        # 添加常见字符的频率
        common_chars = 'abcdefghijklmnopqrstuvwxyz0123456789 .,!?'
        for char in common_chars:
            freq = char_counts.get(char, 0) / max(len(text), 1)
            features.append(min(freq, 1.0))
        
        # 5. 单词数量特征
        word_count = len(text.split())
        features.append(min(word_count / 100.0, 1.0))
        
        # 6. 使用文本内容生成更多特征
        text_bytes = text.encode('utf-8')
        for i in range(min(len(text_bytes), 50)):
            features.append(text_bytes[i] / 255.0)
        
        # 确保向量长度为指定维度
        while len(features) < self.vector_dim:
            # 使用现有特征的组合生成更多特征
            if len(features) > 0:
                features.append((features[len(features) % len(features)] + 0.1) % 1.0)
            else:
                features.append(0.5)
        
        # 截断到指定维度
        features = features[:self.vector_dim]
        
        # 归一化向量
        features = np.array(features)
        norm = np.linalg.norm(features)
        if norm > 0:
            features = features / norm
        
        return features.tolist()
    
    def similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        计算两个向量的余弦相似度
        
        Args:
            vec1 (List[float]): 向量1
            vec2 (List[float]): 向量2
            
        Returns:
            float: 相似度分数 (0-1)
        """
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        return max(0.0, similarity)  # 确保非负

# 全局实例
embedding_service = SimpleEmbeddingService()

def get_text_embedding(text: str) -> List[float]:
    """
    获取文本的向量表示
    
    Args:
        text (str): 输入文本
        
    Returns:
        List[float]: 文本向量
    """
    return embedding_service.encode(text)

def calculate_similarity(embedding1: List[float], embedding2: List[float]) -> float:
    """
    计算两个向量的相似度
    
    Args:
        embedding1 (List[float]): 向量1
        embedding2 (List[float]): 向量2
        
    Returns:
        float: 相似度分数
    """
    return embedding_service.similarity(embedding1, embedding2)