import os
import glob
import json
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from dotenv import load_dotenv

def main():
    load_dotenv() # Tự động load OPENAI_API_KEY từ file .env
    
    # Thư mục chứa chunks đã chia nhỏ
    base_dir = os.path.dirname(os.path.abspath(__file__))
    chunks_dir = os.path.join(base_dir, "chunks")
    
    if not os.path.exists(chunks_dir):
        print(f"Không tìm thấy thư mục {chunks_dir}. Hãy chạy chunking.py trước.")
        return

    json_files = glob.glob(os.path.join(chunks_dir, "*.json"))
    
    docs = []
    print(f"Tìm thấy {len(json_files)} file json. Đang đọc dữ liệu...")
    
    for file_path in json_files:
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                chunks_data = json.load(f)
                for chunk in chunks_data:
                    text = chunk.get("text", "")
                    metadata = chunk.get("metadata", {})
                    if text:
                        docs.append(Document(page_content=text, metadata=metadata))
            except json.JSONDecodeError:
                print(f"Lỗi đọc file JSON: {file_path}")
                    
    print(f"Tổng số chunks đã tải: {len(docs)}")
    
    if not docs:
        print("Không có dữ liệu để tạo index.")
        return

    # Khởi tạo mô hình Embedding
    print("Đang khởi tạo HuggingFace Embeddings (paraphrase-multilingual-MiniLM-L12-v2)...")
    hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")
    if not hf_token or hf_token == "Điền_Token_HuggingFace_Của_Bạn_Vào_Đây":
        print("Lỗi: Bạn chưa cấu hình HUGGINGFACEHUB_API_TOKEN trong file .env!")
        print("Vui lòng lấy token miễn phí tại https://huggingface.co/settings/tokens")
        return

    embeddings = HuggingFaceEndpointEmbeddings(
        model="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        huggingfacehub_api_token=hf_token
    )
    
    # Tạo vector store bằng Chroma
    output_dir = os.path.join(base_dir, "..", "rag", "vector_store")
    os.makedirs(output_dir, exist_ok=True)
    
    print("Đang khởi tạo Chroma DB. Quá trình này sẽ nhanh hơn nhiều và không bị giới hạn gắt gao...")
    vector_store = Chroma(embedding_function=embeddings, persist_directory=output_dir)
    
    import time
    batch_size = 50  # API của HuggingFace cho phép xử lý lô lớn hơn
    
    for i in range(0, len(docs), batch_size):
        batch = docs[i:i+batch_size]
        print(f"Đang nhúng chunks từ {i+1} đến {min(i+batch_size, len(docs))} trên tổng số {len(docs)}...")
        
        # Thêm document trực tiếp vào Chroma với cơ chế tự động thử lại (Retry)
        while True:
            try:
                vector_store.add_documents(batch)
                break  # Thành công thì thoát vòng lặp Retry
            except Exception as e:
                print(f"⚠️ Chi tiết lỗi HuggingFace: {str(e)}", flush=True)
                print(f"Tự động chờ 5 giây trước khi thử lại...", flush=True)
                time.sleep(5)
            
    print(f"\n[Thành công] Đã lưu Chroma index tại: {os.path.relpath(output_dir, base_dir)}")

if __name__ == "__main__":
    main()
