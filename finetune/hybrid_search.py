#!/usr/bin/env python3
"""
混合检索系统：BM25 + 向量召回 + 交叉重排

功能：
- BM25关键词检索（使用jieba中文分词）
- 向量语义检索（使用sentence-transformers + FAISS）
- 交叉重排（使用cross-encoder）

使用方法：
1. 构建索引：python hybrid_search.py --mode build --data processed_data.json
2. 单次检索：python hybrid_search.py --mode search --query "你的查询" --top-k 12
3. 交互式：python hybrid_search.py --mode interactive --top-k 12
"""

# ============================================================
# 本地测试配置（直接运行时使用，不需要命令行参数）
# ============================================================
# 使用说明：
# 1. 首次使用：将 mode 设为 'build' 来构建索引
# 2. 单次检索：将 mode 设为 'search' 并设置 query
# 3. 交互式：将 mode 设为 'interactive'
# ============================================================
LOCAL_CONFIG = {
    'mode': 'search',  # 可选: 'build', 'search', 'interactive'
    'data': 'processed_data.json',  # 数据文件路径
    'index_dir': './index',  # 索引目录
    'query': '这傻逼班 不想上了',  # 查询文本（search模式使用）
    'top_k': 12  # 返回结果数量
}
# ============================================================

import json
import pickle
import os
import time
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Set
import numpy as np
from tqdm import tqdm

# BM25和分词
import jieba
from rank_bm25 import BM25Okapi

# 向量化和检索
from sentence_transformers import SentenceTransformer, CrossEncoder
import faiss


class HybridSearchEngine:
    """混合检索引擎"""
    
    def __init__(self, index_dir: str = "./index"):
        """
        初始化检索引擎
        
        Args:
            index_dir: 索引文件保存目录
        """
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(exist_ok=True)
        
        # 模型
        self.embedding_model = None
        self.reranker_model = None
        
        # 索引
        self.documents = []
        self.bm25 = None
        self.tokenized_corpus = []
        self.faiss_index = None
        
        # 配置
        self.config = {
            "embedding_model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            "reranker_model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
            "embedding_dim": 384,
            "batch_size": 32
        }
    
    def _load_models(self):
        """加载模型（延迟加载）"""
        if self.embedding_model is None:
            print(f"加载向量化模型: {self.config['embedding_model']}")
            self.embedding_model = SentenceTransformer(self.config['embedding_model'])
            self.config['embedding_dim'] = self.embedding_model.get_sentence_embedding_dimension()
        
        if self.reranker_model is None:
            print(f"加载重排模型: {self.config['reranker_model']}")
            self.reranker_model = CrossEncoder(self.config['reranker_model'])
    
    def _tokenize_chinese(self, text: str) -> List[str]:
        """
        中文分词
        
        Args:
            text: 输入文本
            
        Returns:
            分词列表
        """
        return list(jieba.cut(text))
    
    def build_index(self, data_path: str):
        """
        构建索引
        
        Args:
            data_path: 数据文件路径（JSON格式）
        """
        print("=" * 60)
        print("开始构建索引")
        print("=" * 60)
        
        # 加载数据
        print(f"\n[1/4] 加载数据: {data_path}")
        with open(data_path, 'r', encoding='utf-8') as f:
            self.documents = json.load(f)
        print(f"  加载了 {len(self.documents)} 条文档")
        
        # 构建BM25索引
        print("\n[2/4] 构建BM25索引（中文分词中...）")
        self.tokenized_corpus = []
        for doc in tqdm(self.documents, desc="  分词进度"):
            tokens = self._tokenize_chinese(doc)
            self.tokenized_corpus.append(tokens)
        
        self.bm25 = BM25Okapi(self.tokenized_corpus)
        print("  BM25索引构建完成")
        
        # 构建向量索引
        print("\n[3/4] 构建FAISS向量索引")
        self._load_models()
        
        # 批量向量化
        print("  文本向量化中...")
        embeddings = []
        batch_size = self.config['batch_size']
        for i in tqdm(range(0, len(self.documents), batch_size), desc="  向量化进度"):
            batch = self.documents[i:i + batch_size]
            batch_embeddings = self.embedding_model.encode(
                batch, 
                show_progress_bar=False,
                normalize_embeddings=True  # L2归一化
            )
            embeddings.append(batch_embeddings)
        
        embeddings = np.vstack(embeddings).astype('float32')
        print(f"  向量化完成，形状: {embeddings.shape}")
        
        # 创建FAISS索引（使用内积，因为向量已归一化，等价于余弦相似度）
        print("  构建FAISS索引...")
        self.faiss_index = faiss.IndexFlatIP(self.config['embedding_dim'])
        self.faiss_index.add(embeddings)
        print(f"  FAISS索引构建完成，包含 {self.faiss_index.ntotal} 个向量")
        
        # 保存索引
        print("\n[4/4] 保存索引到磁盘")
        self._save_index()
        print("  索引保存完成")
        
        print("\n" + "=" * 60)
        print("索引构建完成！")
        print("=" * 60)
    
    def _save_index(self):
        """保存索引到磁盘"""
        # 保存BM25索引
        bm25_path = self.index_dir / "bm25_index.pkl"
        with open(bm25_path, 'wb') as f:
            pickle.dump({
                'bm25': self.bm25,
                'tokenized_corpus': self.tokenized_corpus
            }, f)
        print(f"  BM25索引: {bm25_path}")
        
        # 保存FAISS索引
        faiss_path = self.index_dir / "faiss_index.bin"
        faiss.write_index(self.faiss_index, str(faiss_path))
        print(f"  FAISS索引: {faiss_path}")
        
        # 保存文档
        docs_path = self.index_dir / "documents.pkl"
        with open(docs_path, 'wb') as f:
            pickle.dump(self.documents, f)
        print(f"  文档数据: {docs_path}")
        
        # 保存配置
        config_path = self.index_dir / "config.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
        print(f"  配置信息: {config_path}")
    
    def load_index(self):
        """从磁盘加载索引"""
        print("加载索引...")
        
        # 加载配置
        config_path = self.index_dir / "config.json"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        
        # 加载BM25索引
        bm25_path = self.index_dir / "bm25_index.pkl"
        with open(bm25_path, 'rb') as f:
            data = pickle.load(f)
            self.bm25 = data['bm25']
            self.tokenized_corpus = data['tokenized_corpus']
        print(f"  BM25索引加载完成")
        
        # 加载FAISS索引
        faiss_path = self.index_dir / "faiss_index.bin"
        self.faiss_index = faiss.read_index(str(faiss_path))
        print(f"  FAISS索引加载完成（{self.faiss_index.ntotal} 个向量）")
        
        # 加载文档
        docs_path = self.index_dir / "documents.pkl"
        with open(docs_path, 'rb') as f:
            self.documents = pickle.load(f)
        print(f"  文档数据加载完成（{len(self.documents)} 条）")
        
        # 加载模型
        self._load_models()
        
        print("索引加载完成！\n")
    
    def _bm25_search(self, query: str, top_k: int = 50) -> List[Tuple[int, float]]:
        """
        BM25检索
        
        Args:
            query: 查询文本
            top_k: 返回Top K结果
            
        Returns:
            [(doc_id, score), ...]
        """
        tokenized_query = self._tokenize_chinese(query)
        scores = self.bm25.get_scores(tokenized_query)
        
        # 获取Top K
        top_indices = np.argsort(scores)[::-1][:top_k]
        results = [(int(idx), float(scores[idx])) for idx in top_indices if scores[idx] > 0]
        
        return results
    
    def _vector_search(self, query: str, top_k: int = 50) -> List[Tuple[int, float]]:
        """
        向量检索
        
        Args:
            query: 查询文本
            top_k: 返回Top K结果
            
        Returns:
            [(doc_id, score), ...]
        """
        # 向量化查询
        query_vector = self.embedding_model.encode(
            [query], 
            normalize_embeddings=True
        ).astype('float32')
        
        # FAISS检索
        scores, indices = self.faiss_index.search(query_vector, top_k)
        
        results = [(int(idx), float(score)) for idx, score in zip(indices[0], scores[0])]
        return results
    
    def _merge_candidates(self, 
                         bm25_results: List[Tuple[int, float]], 
                         vector_results: List[Tuple[int, float]]) -> Set[int]:
        """
        合并候选结果（去重）
        
        Args:
            bm25_results: BM25结果
            vector_results: 向量检索结果
            
        Returns:
            去重后的文档ID集合
        """
        candidate_ids = set()
        
        for doc_id, score in bm25_results:
            candidate_ids.add(doc_id)
        
        for doc_id, score in vector_results:
            candidate_ids.add(doc_id)
        
        return candidate_ids
    
    def _rerank(self, query: str, candidate_ids: Set[int], top_k: int = 12) -> List[Dict]:
        """
        使用cross-encoder重排
        
        Args:
            query: 查询文本
            candidate_ids: 候选文档ID集合
            top_k: 返回Top K结果
            
        Returns:
            重排后的结果列表
        """
        if not candidate_ids:
            return []
        
        # 准备候选文档
        candidates = [(doc_id, self.documents[doc_id]) for doc_id in candidate_ids]
        
        # 构建query-document对
        pairs = [(query, doc) for doc_id, doc in candidates]
        
        # 批量打分
        scores = self.reranker_model.predict(pairs, show_progress_bar=False)
        
        # 合并结果并排序
        results = []
        for (doc_id, doc), score in zip(candidates, scores):
            results.append({
                'doc_id': doc_id,
                'text': doc,
                'score': float(score)
            })
        
        # 按分数降序排序
        results.sort(key=lambda x: x['score'], reverse=True)
        
        # 添加排名
        for rank, result in enumerate(results[:top_k], 1):
            result['rank'] = rank
        
        return results[:top_k]
    
    def search(self, query: str, top_k: int = 12, verbose: bool = True) -> Dict:
        """
        混合检索
        
        Args:
            query: 查询文本
            top_k: 返回Top K结果
            verbose: 是否打印详细信息
            
        Returns:
            检索结果
        """
        start_time = time.time()
        
        if verbose:
            print(f"\n查询: {query}")
            print("-" * 60)
        
        # 1. BM25召回
        if verbose:
            print("[1/3] BM25召回...")
        bm25_results = self._bm25_search(query, top_k=50)
        if verbose:
            print(f"  召回 {len(bm25_results)} 条候选")
        
        # 2. 向量召回
        if verbose:
            print("[2/3] 向量召回...")
        vector_results = self._vector_search(query, top_k=50)
        if verbose:
            print(f"  召回 {len(vector_results)} 条候选")
        
        # 3. 合并候选
        candidate_ids = self._merge_candidates(bm25_results, vector_results)
        if verbose:
            print(f"  合并去重后: {len(candidate_ids)} 条候选")
        
        # 4. 交叉重排
        if verbose:
            print("[3/3] 交叉重排...")
        final_results = self._rerank(query, candidate_ids, top_k=top_k)
        
        total_time = time.time() - start_time
        
        if verbose:
            print(f"  返回 Top {len(final_results)} 结果")
            print(f"\n总耗时: {total_time:.3f}秒")
            print("-" * 60)
        
        return {
            'query': query,
            'results': final_results,
            'total_time': f"{total_time:.3f}s",
            'stats': {
                'bm25_candidates': len(bm25_results),
                'vector_candidates': len(vector_results),
                'merged_candidates': len(candidate_ids),
                'final_results': len(final_results)
            }
        }
    
    def print_results(self, search_result: Dict):
        """打印检索结果"""
        print("\n" + "=" * 60)
        print("检索结果")
        print("=" * 60)
        
        for result in search_result['results']:
            print(f"\n[{result['rank']}] 得分: {result['score']:.4f}")
            print(f"内容: {result['text'][:200]}{'...' if len(result['text']) > 200 else ''}")
            print(f"文档ID: {result['doc_id']}")
        
        print("\n" + "=" * 60)
        print(f"查询: {search_result['query']}")
        print(f"耗时: {search_result['total_time']}")
        print("=" * 60)


def main():
    """主函数"""
    import sys
    
    # 检查是否有命令行参数，如果没有则使用本地配置
    use_local_config = len(sys.argv) == 1
    
    if use_local_config:
        print("=" * 60)
        print("使用本地配置运行（无命令行参数）")
        print("=" * 60)
        print(f"模式: {LOCAL_CONFIG['mode']}")
        print(f"数据文件: {LOCAL_CONFIG['data']}")
        print(f"索引目录: {LOCAL_CONFIG['index_dir']}")
        if LOCAL_CONFIG['mode'] == 'search':
            print(f"查询: {LOCAL_CONFIG['query']}")
        print(f"Top K: {LOCAL_CONFIG['top_k']}")
        print("=" * 60)
        print()
        
        # 使用本地配置创建一个简单对象
        class Config:
            pass
        args = Config()
        args.mode = LOCAL_CONFIG['mode']
        args.data = LOCAL_CONFIG['data']
        args.index_dir = LOCAL_CONFIG['index_dir']
        args.query = LOCAL_CONFIG['query']
        args.top_k = LOCAL_CONFIG['top_k']
    else:
        # 使用命令行参数
        parser = argparse.ArgumentParser(description="混合检索系统")
        parser.add_argument('--mode', type=str, required=True, 
                           choices=['build', 'search', 'interactive'],
                           help='运行模式：build=构建索引, search=单次检索, interactive=交互式检索')
        parser.add_argument('--data', type=str, default='processed_data.json',
                           help='数据文件路径（build模式）')
        parser.add_argument('--index-dir', type=str, default='./index',
                           help='索引目录路径')
        parser.add_argument('--query', type=str, default='',
                           help='查询文本（search模式）')
        parser.add_argument('--top-k', type=int, default=12,
                           help='返回结果数量')
        
        args = parser.parse_args()
    
    # 初始化引擎
    engine = HybridSearchEngine(index_dir=args.index_dir)
    
    if args.mode == 'build':
        # 构建索引模式
        if not os.path.exists(args.data):
            print(f"错误: 数据文件不存在: {args.data}")
            return
        
        engine.build_index(args.data)
        
    elif args.mode == 'search':
        # 单次检索模式
        if not args.query:
            print("错误: 请提供查询文本（--query）")
            return
        
        engine.load_index()
        result = engine.search(args.query, top_k=args.top_k)
        engine.print_results(result)
        
        # 保存结果到JSON
        output_file = f"search_result_{int(time.time())}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n结果已保存到: {output_file}")
        
    elif args.mode == 'interactive':
        # 交互式检索模式
        engine.load_index()
        
        print("\n" + "=" * 60)
        print("交互式检索模式")
        print("=" * 60)
        print("输入查询文本进行检索，输入 'quit' 或 'exit' 退出\n")
        
        while True:
            try:
                query = input("请输入查询: ").strip()
                
                if query.lower() in ['quit', 'exit', 'q']:
                    print("退出检索")
                    break
                
                if not query:
                    continue
                
                result = engine.search(query, top_k=args.top_k)
                engine.print_results(result)
                
            except KeyboardInterrupt:
                print("\n\n退出检索")
                break
            except Exception as e:
                print(f"错误: {e}")


if __name__ == "__main__":
    main()

