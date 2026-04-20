from rag_utils import RAGManager
import json
import os

def load_documents_from_json(json_file_path: str):
    """JSON 파일에서 문서를 로드하여 벡터 DB에 추가"""
    with open(json_file_path, 'r', encoding='utf-8') as f:
        documents = json.load(f)
    
    rag_manager = RAGManager()
    rag_manager.add_documents(documents)
    print(f"Successfully loaded {len(documents)} documents from {json_file_path}")

def main():
    # JSON 디렉토리 경로
    json_dir = "JSON"
    
    # JSON 디렉토리의 모든 파일 처리
    for filename in os.listdir(json_dir):
        if filename.endswith('.json'):
            file_path = os.path.join(json_dir, filename)
            try:
                load_documents_from_json(file_path)
            except Exception as e:
                print(f"Error loading {filename}: {str(e)}")

if __name__ == "__main__":
    main() 