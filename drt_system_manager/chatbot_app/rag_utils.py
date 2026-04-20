import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import os
from typing import List, Dict
import json

class RAGManager:
    def __init__(self, collection_name: str = "chatbot_knowledge"):
        # ChromaDB 클라이언트 초기화
        self.client = chromadb.Client(Settings(
            persist_directory="chatbot_app/data/chroma_db",
            anonymized_telemetry=False
        ))
        
        # 컬렉션 생성 또는 로드
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        # 임베딩 모델 초기화
        self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    
    def add_documents(self, documents: List[Dict[str, str]]):
        """문서를 벡터 DB에 추가"""
        ids = [str(i) for i in range(len(documents))]
        texts = [doc["content"] for doc in documents]
        metadatas = [{"source": doc.get("source", "unknown")} for doc in documents]
        
        # 임베딩 생성
        embeddings = self.embedding_model.encode(texts).tolist()
        
        # 벡터 DB에 추가
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )
    
    def search(self, query: str, n_results: int = 3) -> List[Dict]:
        """쿼리와 관련된 문서 검색"""
        # 쿼리 임베딩 생성
        query_embedding = self.embedding_model.encode(query).tolist()
        
        # 유사 문서 검색
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        # 결과 포맷팅
        formatted_results = []
        for i in range(len(results["documents"][0])):
            formatted_results.append({
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i]
            })
        
        return formatted_results
    
    def create_context(self, query: str, n_results: int = 3) -> str:
        """검색 결과를 기반으로 컨텍스트 생성"""
        results = self.search(query, n_results)
        
        if not results:
            return "관련 정보를 찾을 수 없습니다."
        
        context = "참고할 수 있는 정보:\n\n"
        for i, result in enumerate(results, 1):
            context += f"{i}. {result['content']}\n"
        
        return context 