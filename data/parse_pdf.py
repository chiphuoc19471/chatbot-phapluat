import os
import glob
import re
try:
    import pymupdf4llm
except ImportError:
    print("Vui lòng cài đặt pymupdf4llm bằng lệnh: pip install pymupdf4llm")
    exit(1)

def clean_markdown(md_text):
    """
    Hàm làm sạch file markdown.
    Có thể thêm các regex để xóa bỏ header/footer không mong muốn.
    """
    # Xóa các dòng chỉ chứa số trang (ví dụ: "Trang 1", "- 1 -", v.v.)
    md_text = re.sub(r'^(Trang \d+|-\s*\d+\s*-)$', '', md_text, flags=re.MULTILINE)
    
    # Loại bỏ các khoảng trắng hoặc dòng trống dư thừa
    md_text = re.sub(r'\n{3,}', '\n\n', md_text)
    
    return md_text

def parse_all_pdfs(raw_dir='raw', processed_dir='processed'):
    if not os.path.exists(raw_dir):
        os.makedirs(raw_dir)
        print(f"Đã tạo thư mục '{raw_dir}'. Vui lòng copy các file PDF pháp luật vào đây.")
        return
        
    if not os.path.exists(processed_dir):
        os.makedirs(processed_dir)

    pdf_files = glob.glob(os.path.join(raw_dir, '*.pdf'))
    if not pdf_files:
        print(f"Không tìm thấy file PDF nào trong thư mục '{raw_dir}'.")
        return

    print(f"Tìm thấy {len(pdf_files)} file PDF. Bắt đầu chuyển đổi...")

    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        md_filename = filename.replace('.pdf', '.md')
        processed_path = os.path.join(processed_dir, md_filename)
        
        print(f"Đang xử lý: {filename} -> {md_filename}...")
        try:
            # Dùng pymupdf4llm chuyển thẳng PDF sang Markdown
            md_text = pymupdf4llm.to_markdown(pdf_path)
            
            # Làm sạch sơ bộ
            clean_md = clean_markdown(md_text)
            
            # Lưu file
            with open(processed_path, 'w', encoding='utf-8') as f:
                f.write(clean_md)
            print(f"  [Thành công] Đã lưu tại: {processed_path}")
            
        except Exception as e:
            print(f"  [Lỗi] khi xử lý {filename}: {e}")

if __name__ == "__main__":
    # Thay đổi thư mục làm việc hiện tại về thư mục chứa script để đường dẫn tương đối hoạt động đúng
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    parse_all_pdfs()
