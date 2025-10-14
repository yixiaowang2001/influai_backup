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
                        content_set.add(content.strip())
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
    
    # 转换为列表并保存
    content_list = list(content_set)
    
    print("=" * 60)
    print(f"提取统计:")
    print(f"  Posts 提取数量: {posts_count}")
    print(f"  Comments 提取数量: {comments_count}")
    print(f"  去重前总数: {posts_count + comments_count}")
    print(f"  去重后总数: {len(content_list)}")
    print("=" * 60)
    
    # 保存到文件
    print(f"正在保存到: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(content_list, f, ensure_ascii=False, indent=2)
    
    print(f"处理完成! 结果已保存到 {output_file}")
    print(f"文件大小: {output_file.stat().st_size / 1024 / 1024:.2f} MB")


if __name__ == '__main__':
    main()

