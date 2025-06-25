# 测试简单向量化服务
from services.embedding_service import get_text_embedding, calculate_similarity

try:
    # 测试文本
    text1 = "我想学习编程"
    text2 = "如何学习Python编程"
    text3 = "今天天气很好"
    
    # 生成向量
    embedding1 = get_text_embedding(text1)
    embedding2 = get_text_embedding(text2)
    embedding3 = get_text_embedding(text3)
    
    print(f"文本1向量维度: {len(embedding1)}")
    print(f"文本2向量维度: {len(embedding2)}")
    print(f"文本3向量维度: {len(embedding3)}")
    
    # 计算相似度
    sim_1_2 = calculate_similarity(embedding1, embedding2)
    sim_1_3 = calculate_similarity(embedding1, embedding3)
    sim_2_3 = calculate_similarity(embedding2, embedding3)
    
    print(f"\n相似度测试:")
    print(f"'{text1}' vs '{text2}': {sim_1_2:.4f}")
    print(f"'{text1}' vs '{text3}': {sim_1_3:.4f}")
    print(f"'{text2}' vs '{text3}': {sim_2_3:.4f}")
    
    print("\n向量化服务测试成功！")
    
except Exception as e:
    print(f"测试失败: {e}")
    import traceback
    traceback.print_exc()