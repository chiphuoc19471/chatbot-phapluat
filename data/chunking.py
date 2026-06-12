import os
import glob
import json
import re

from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

def fix_markdown_hierarchy(md_text):
    """
    Tiền xử lý file Markdown: Chuẩn hóa lại các thẻ Heading bị sai cấp bậc do parser tạo ra.
    Ví dụ: pymupdf4llm thường để Chương, Mục, Điều đều là `##`. Ta sẽ sửa lại thành:
    # Phần/Chương
    ## Mục
    ### Điều
    """
    # Xử lý Chương
    md_text = re.sub(r'^(#+)\s*\**\s*(Chương\s+[IVXLCDM]+)\s*\**', r'# \2', md_text, flags=re.MULTILINE | re.IGNORECASE)
    # Xử lý Mục
    md_text = re.sub(r'^(#+)\s*\**\s*(Mục\s+\d+)\s*\**', r'## \2', md_text, flags=re.MULTILINE | re.IGNORECASE)
    # Xử lý Điều
    md_text = re.sub(r'^(#+)\s*\**\s*(Điều\s+\d+\.?)\s*\**', r'### \2', md_text, flags=re.MULTILINE | re.IGNORECASE)
    
    return md_text

def chunk_markdown_files(processed_dir='processed', chunk_dir='chunks'):
    if not os.path.exists(chunk_dir):
        os.makedirs(chunk_dir)
        
    md_files = glob.glob(os.path.join(processed_dir, '*.md'))
    if not md_files:
        print(f"Không tìm thấy file .md nào trong '{processed_dir}'.")
        return

    # 1. Khởi tạo cấu hình cho Giai đoạn 1: Structural Chunking
    headers_to_split_on = [
        ("#", "Chương"),
        ("##", "Mục"),
        ("###", "Điều"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on, strip_headers=False)

    # 2. Khởi tạo cấu hình cho Giai đoạn 2: Fallback Chunking (xử lý Điều quá dài)
    # Cố gắng không cắt giữa bảng (dấu |) hoặc giữa câu.
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,
        chunk_overlap=300,
        separators=["\n\n", "\n", ".", "?", "!", " ", ""],
        length_function=len,
    )

    for md_path in md_files:
        filename = os.path.basename(md_path)
        print(f"Đang băm nhỏ (chunking): {filename}...")
        
        with open(md_path, 'r', encoding='utf-8') as f:
            raw_md = f.read()
            
        # Tiền xử lý cấu trúc
        fixed_md = fix_markdown_hierarchy(raw_md)
        
        # Giai đoạn 1: Cắt theo thẻ Heading
        md_header_splits = markdown_splitter.split_text(fixed_md)
        
        # Giai đoạn 2: Cắt nhỏ tiếp các đoạn quá dài (Kế thừa metadata)
        final_splits = text_splitter.split_documents(md_header_splits)
        
        # 3. Đóng gói thành JSON
        chunks_data = []
        for i, doc in enumerate(final_splits):
            chunk_metadata = doc.metadata
            chunk_metadata["Source"] = filename  # Đánh dấu nguồn
            chunk_metadata["Chunk_ID"] = i + 1
            
            chunks_data.append({
                "chunk_id": chunk_metadata["Chunk_ID"],
                "text": doc.page_content,
                "metadata": chunk_metadata
            })
            
        # Lưu ra file JSON
        json_filename = filename.replace('.md', '.json')
        json_path = os.path.join(chunk_dir, json_filename)
        with open(json_path, 'w', encoding='utf-8') as json_file:
            json.dump(chunks_data, json_file, ensure_ascii=False, indent=4)
            
        print(f"  [Thành công] Đã tạo ra {len(chunks_data)} chunks. Lưu tại: {json_path}")

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    chunk_markdown_files()
