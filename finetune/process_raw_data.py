"""
处理原始数据文件，提取所有 content 字段

从 Posts.json 和 Comments.json 中提取 content 字段，
去重后合并保存到 processed_data.json
"""

import ijson
import json
import os
import re
from pathlib import Path
from datasketch import MinHash, MinHashLSH


def clean_content(text):
    """
    清洗文本内容
    
    处理规则：
    1. 删除 @username
    2. 删除 "回复" + ":"
    3. 删除特殊字符（保留emoji、中英文、数字、常用标点）
    4. 删除微博表情 [xxx]
    5. 删除 hashtag #xxx#
    6. 删除第一个双斜杠后的所有内容
    7. 删除 URL 链接 (http:// 或 https://)
    
    Args:
        text: 原始文本
    
    Returns:
        清洗后的文本
    """
    if not text:
        return ""
    
    # 1. 删除 URL 链接 (http:// 或 https://)
    # 注意：必须在删除双斜杠之前处理，否则 // 会被误删
    text = re.sub(r'https?://\S+', '', text)
    
    # 2. 删除第一个双斜杠后的所有内容（因为那是转发的评论）
    text = re.sub(r'//.*$', '', text)
    
    # 3. 删除 @username 及其后的空格
    # 匹配 @ 后跟字母、数字、中文、下划线、连字符，直到遇到空格或标点
    text = re.sub(r'@[\w\u4e00-\u9fa5_-]+\s*', '', text)
    
    # 4. 删除 "回复" + ":"  （如 "回复@xxx:"）
    text = re.sub(r'回复[^:]*:\s*', '', text)
    
    # 5. 删除微博表情 [xxx]
    text = re.sub(r'\[.*?\]', '', text)
    
    # 6. 删除 hashtag #xxx#
    text = re.sub(r'#[^#]+#', '', text)
    
    # 7. 删除特殊字符，但保留：
    #    - 中文字符 (\u4e00-\u9fa5)
    #    - 英文字母和数字 (a-zA-Z0-9)
    #    - 常用标点符号
    #    - emoji (保留 Unicode emoji 范围)
    # emoji 主要范围：
    #   - \U0001F300-\U0001F9FF (各种表情符号)
    #   - \U0001FA00-\U0001FAFF (扩展符号)
    #   - \u2600-\u26FF (杂项符号)
    #   - \u2700-\u27BF (装饰符号)
    #   - \U0001F600-\U0001F64F (表情符号)
    #   - \U0001F680-\U0001F6FF (交通和地图符号)
    
    # 保留的字符模式
    keep_pattern = re.compile(
        r'[\u4e00-\u9fa5'  # 中文
        r'a-zA-Z0-9'  # 英文和数字
        r'\s'  # 空白字符
        r'，。！？、；：""''（）《》…—'  # 中文标点
        r',.!?;:\'\"\(\)\-'  # 英文标点
        r'\U0001F300-\U0001F9FF'  # emoji
        r'\U0001FA00-\U0001FAFF'  # emoji扩展
        r'\u2600-\u26FF'  # 杂项符号
        r'\u2700-\u27BF'  # 装饰符号
        r']',
        re.UNICODE
    )
    
    # 只保留匹配的字符
    text = ''.join(keep_pattern.findall(text))
    
    # 8. 清理多余空格
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


class JSONFixerStream:
    """
    包装文件流，修复常见的 JSON 格式问题
    将 NaN 替换为 null
    """
    def __init__(self, file_obj):
        self.file_obj = file_obj
        self.buffer = b''
    
    def read(self, size=-1):
        chunk = self.file_obj.read(size)
        if not chunk:
            return chunk
        
        # 将 NaN 替换为 null
        chunk = re.sub(rb'\bNaN\b', b'null', chunk)
        return chunk
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        pass


def extract_content_from_file(file_path, content_set):
    """
    使用流式 JSON 解析提取 content 字段
    
    Args:
        file_path: JSON 文件路径
        content_set: 用于去重的 set
    
    Returns:
        提取的 content 数量
    """
    print(f"正在处理: {file_path}")
    
    count = 0
    error_count = 0
    try:
        with open(file_path, 'rb') as raw_file:
            # 使用修复流包装原始文件
            fixed_stream = JSONFixerStream(raw_file)
            
            try:
                # 使用 ijson 流式解析 JSON 数组
                parser = ijson.items(fixed_stream, 'item')
                
                for item in parser:
                    # 提取 content 字段
                    content = item.get('content')
                    
                    # 跳过空值和空字符串
                    if content and isinstance(content, str) and content.strip():
                        # 清洗文本内容
                        cleaned_content = clean_content(content)
                        
                        # 清洗后如果还有内容，则添加到集合
                        if cleaned_content:
                            content_set.add(cleaned_content)
                            count += 1
                            
                            # 每处理 1000 条打印进度
                            if count % 1000 == 0:
                                print(f"已处理 {count} 条记录，当前去重后数量: {len(content_set)}")
            
            except ijson.common.IncompleteJSONError as e:
                print(f"警告: JSON 格式错误，尝试继续处理: {str(e)[:100]}")
                error_count += 1
        
        print(f"完成处理 {file_path}，共提取 {count} 条记录")
        if error_count > 0:
            print(f"遇到 {error_count} 个格式错误，已跳过")
        return count
        
    except Exception as e:
        print(f"处理文件 {file_path} 时出错: {e}")
        print(f"已成功提取 {count} 条记录，将继续处理下一个文件")
        return count


def minhash_deduplicate(content_list, threshold=0.85, num_perm=128):
    """
    使用 MinHash 和 LSH 进行相似度去重
    
    Args:
        content_list: 文本列表
        threshold: Jaccard 相似度阈值，超过此值认为重复（默认 0.85）
        num_perm: MinHash 的 permutation 数量，越大越准确但越慢（默认 128）
    
    Returns:
        去重后的文本列表
    """
    print(f"\n开始 MinHash 去重，阈值: Jaccard >= {threshold}")
    print(f"去重前数量: {len(content_list)}")
    
    # 创建 LSH 索引
    lsh = MinHashLSH(threshold=threshold, num_perm=num_perm)
    
    # 存储每个文本的 MinHash
    minhashes = {}
    
    # 用于存储去重后的内容
    unique_contents = []
    duplicate_count = 0
    
    for idx, text in enumerate(content_list):
        # 创建 MinHash
        m = MinHash(num_perm=num_perm)
        
        # 将文本分词（使用字符级别的 n-gram，适合中文）
        # 使用 3-gram
        for i in range(len(text) - 2):
            m.update(text[i:i+3].encode('utf-8'))
        
        # 如果文本太短，至少添加整个文本
        if len(text) <= 2:
            m.update(text.encode('utf-8'))
        
        # 查询 LSH，看是否有相似的文本
        result = lsh.query(m)
        
        if result:
            # 找到相似的文本，跳过
            duplicate_count += 1
        else:
            # 没有找到相似的文本，添加到索引和结果列表
            key = f"text_{idx}"
            lsh.insert(key, m)
            minhashes[key] = m
            unique_contents.append(text)
        
        # 每处理 10000 条打印进度
        if (idx + 1) % 10000 == 0:
            print(f"已处理 {idx + 1}/{len(content_list)} 条，"
                  f"当前去重后: {len(unique_contents)} 条，"
                  f"已去除重复: {duplicate_count} 条")
    
    print(f"\nMinHash 去重完成:")
    print(f"  去重前: {len(content_list)} 条")
    print(f"  去重后: {len(unique_contents)} 条")
    print(f"  去除重复: {duplicate_count} 条")
    print(f"  去重率: {duplicate_count / len(content_list) * 100:.2f}%")
    
    return unique_contents


def main():
    # 设置文件路径
    base_dir = Path(__file__).parent
    raw_data_dir = base_dir / 'raw_data'
    posts_file = raw_data_dir / 'Posts.json'
    comments_file = raw_data_dir / 'Comments.json'
    output_file = base_dir / 'processed_data.json'
    
    # 检查输入文件是否存在
    if not posts_file.exists():
        print(f"错误: {posts_file} 不存在")
        return
    
    if not comments_file.exists():
        print(f"错误: {comments_file} 不存在")
        return
    
    print("=" * 60)
    print("开始处理原始数据")
    print("=" * 60)
    
    # 使用 set 进行去重
    content_set = set()
    
    # 提取 Posts.json 中的 content
    posts_count = extract_content_from_file(posts_file, content_set)
    
    # 提取 Comments.json 中的 content
    comments_count = extract_content_from_file(comments_file, content_set)
    
    # 转换为列表
    content_list = list(content_set)
    
    print("=" * 60)
    print(f"第一阶段：完全匹配去重统计:")
    print(f"  Posts 提取数量: {posts_count}")
    print(f"  Comments 提取数量: {comments_count}")
    print(f"  去重前总数: {posts_count + comments_count}")
    print(f"  完全匹配去重后: {len(content_list)}")
    print("=" * 60)
    
    # 第二阶段：使用 MinHash 进行相似度去重
    content_list = minhash_deduplicate(content_list, threshold=0.85)
    
    print("=" * 60)
    print(f"最终统计:")
    print(f"  原始数据总数: {posts_count + comments_count}")
    print(f"  完全匹配去重后: {len(content_set)}")
    print(f"  相似度去重后（最终）: {len(content_list)}")
    print("=" * 60)
    
    # 保存到文件
    print(f"正在保存到: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(content_list, f, ensure_ascii=False, indent=2)
    
    print(f"处理完成! 结果已保存到 {output_file}")
    print(f"文件大小: {output_file.stat().st_size / 1024 / 1024:.2f} MB")


def test_clean_content():
    """
    测试清洗函数
    """
    test_cases = [
        "@评论罗伯特 你怎么不回我",
        "回复@评论罗伯特:哈哈😂//@评论罗伯特:哇哦，乐虎减肥成功了，看来你的四个大罐罐也起作用了[赞]",
        "他怎么还看碟下菜[右哼哼]",
        "@评论罗伯特",
        "罗布特耍大牌啦[笑哈哈]",
        "#doubty# 这是一个话题",
        "她评论我两次了嘿嘿嘿[偷笑][偷笑][偷笑]",
        "查看链接 https://weibo.com/123456 了解详情",
        "这是一个测试 http://example.com 的内容",
    ]
    
    print("=" * 60)
    print("清洗函数测试")
    print("=" * 60)
    
    for i, text in enumerate(test_cases, 1):
        cleaned = clean_content(text)
        print(f"\n测试 {i}:")
        print(f"  原文: {text}")
        print(f"  清洗后: {cleaned}")
    
    print("\n" + "=" * 60)


def test_minhash():
    """
    测试 MinHash 去重
    """
    test_texts = [
        "今天天气真好，阳光明媚",
        "今天天气真好，阳光明媚啊",  # 非常相似
        "今天天气真好，阳光灿烂",  # 相似
        "明天会下雨吗",  # 完全不同
        "明天会下雨吗？",  # 几乎相同
        "我喜欢吃苹果",
        "我喜欢吃香蕉",  # 部分相似
        "完全不同的一句话",
        "这是另一个完全不同的句子",
    ]
    
    print("=" * 60)
    print("MinHash 去重测试")
    print("=" * 60)
    print(f"原始文本数量: {len(test_texts)}")
    print("\n原始文本:")
    for i, text in enumerate(test_texts, 1):
        print(f"  {i}. {text}")
    
    result = minhash_deduplicate(test_texts, threshold=0.85)
    
    print("\n去重后文本:")
    for i, text in enumerate(result, 1):
        print(f"  {i}. {text}")
    
    print("\n" + "=" * 60)


if __name__ == '__main__':
    import sys
    
    # 如果参数是 test，则运行测试
    if len(sys.argv) > 1:
        if sys.argv[1] == 'test':
            test_clean_content()
        elif sys.argv[1] == 'test_minhash':
            test_minhash()
        elif sys.argv[1] == 'test_all':
            test_clean_content()
            print("\n")
            test_minhash()
        else:
            print("未知参数，可用参数:")
            print("  test - 测试清洗函数")
            print("  test_minhash - 测试 MinHash 去重")
            print("  test_all - 运行所有测试")
            print("  (无参数) - 运行完整处理流程")
    else:
        main()

