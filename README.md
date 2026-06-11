# 🤖 Chatbot Tư Vấn Pháp Luật Lao Động
> Ứng dụng kỹ thuật RAG (Retrieval-Augmented Generation) và Mô hình Ngôn ngữ Lớn (LLM)
<img width="2493" height="1375" alt="image" src="https://github.com/user-attachments/assets/dc41c2b2-cd01-47ef-bab8-e4bffe78f95e" />

---

## 📌 Giới thiệu

Hệ thống chatbot hỏi đáp pháp luật lao động, giúp người lao động và doanh nghiệp tra cứu nhanh các quy định về hợp đồng lao động, lương thưởng, nghỉ phép, BHXH, tranh chấp lao động,... dựa trên Bộ luật Lao động 2019 và các văn bản pháp luật liên quan.

---

## 👥 Nhóm phát triển

| Người | Vai trò | Phụ trách |
|---|---|---|
| Nguyễn Tiến Lộc (A)| Backend | FastAPI, Auth JWT, Database, API |
| Hoàng Chí Phước (B)| Team Lead + RAG Engineer | LangChain, Chroma, Embedding, RAG Pipeline |
| Bùi Thái Học (C)| Frontend Developer | React, Tailwind, Giao diện Chat |
| Nguyễn Trường Sơn (D)| Data + Evaluation | Thu thập luật, Chunking, RAGAS |

---

## 🏗️ Kiến trúc hệ thống

```
┌─────────────────────────────────────────────────────┐
│                  FRONTEND (React)                    │
│         Login / Register / Chat / History            │
└──────────────────────┬──────────────────────────────┘
                       │ REST API (JSON)
┌──────────────────────▼──────────────────────────────┐
│                  BACKEND (FastAPI)                   │
│         Auth JWT │ Chat API │ History API            │
└───────┬──────────────────────────┬──────────────────┘
        │                          │
┌───────▼──────────────────────────┐    ┌──────────▼──────────────────┐
│  RAG Pipeline (LangChain)        │    │     Database (SQLite)        │
│  1. Query Rewriting              │    │  users, conversations,       │
│     (lịch sử hội thoại phiên)    │    │  messages                    │
│  2. Parent Document Retrieval    │    └─────────────────────────────┘
│     - Chunk con  → Chroma        │
│       (text-embedding-3-small)   │
│     - Chunk cha (toàn văn Điều)  │
│       → Docstore (file JSON)     │
│  3. LLM Reranker (post-retrieval)│
│  4. Generator: GPT-4.1-mini      │
│     (trả lời + trích dẫn Điều)   │
└──────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Thành phần | Công nghệ |
|---|---|
| Frontend | HTML + CSS + JavaScript (thuần) |
| Backend | FastAPI (Python 3.10+) |
| LLM | GPT-4.1-mini (OpenAI) |
| Embedding | `OpenAI text-embedding-3-small` |
| Vector DB (chunk con) | Chroma |
| Docstore (chunk cha) | File JSON (`rag/docstore/parents.json`) |
| RAG Framework | LangChain |
| Query Rewriting | LangChain (tích hợp lịch sử hội thoại phiên) |
| Retrieval | Parent Document Retrieval (cha-con theo điều khoản luật) |
| Reranker | LLM Reranker (post-retrieval, dùng GPT-4.1-mini) |
| Database | SQLite |
| Cấu hình tham số RAG | `rag/config.py` + biến môi trường `.env` |

---

## 📡 Interface RAG Pipeline

Backend (A) gọi pipeline của RAG (B) qua **một hàm duy nhất** `rag.pipeline.answer()`:

**Input:**
```json
{
  "query": "Nghỉ thai sản được bao nhiêu tháng?",
  "chat_history": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ]
}
```
- `chat_history`: tối đa **5 lượt gần nhất** của phiên hiện tại, Backend truy xuất từ SQLite và truyền vào. Pipeline dùng để Query Rewriting, **không** tự đọc database.

**Output:**
```json
{
  "answer": "Theo Điều 139 Bộ luật Lao động 2019, lao động nữ được nghỉ thai sản 6 tháng...",
  "sources": [
    {
      "dieu": "Điều 139",
      "ten_dieu": "Nghỉ thai sản",
      "van_ban": "Bộ luật Lao động 2019",
      "trich_doan": "Lao động nữ được nghỉ thai sản trước và sau khi sinh con là 06 tháng..."
    }
  ]
}
```
- `sources` để Frontend hiển thị trích dẫn điều luật và để RAGAS lấy `contexts` khi đánh giá.

---

## 📁 Cấu trúc thư mục

```
chatbot-phapluat/
├── backend/                  # Người A phụ trách
│   ├── main.py
│   ├── routers/
│   │   ├── auth.py
│   │   ├── chat.py
│   │   └── history.py
│   ├── models/
│   │   ├── user.py
│   │   └── conversation.py
│   ├── database.py
│   └── auth.py
│
├── rag/                      # Người B phụ trách
│   ├── config.py             # Tham số: chunk size, top_k, top_n, model name...
│   ├── pipeline.py           # Hàm answer() - entry point cho Backend gọi
│   ├── embedder.py           # Khởi tạo embedding model (dùng chung cho build & query)
│   ├── retriever.py          # Parent Document Retrieval
│   ├── reranker.py           # LLM Reranker
│   ├── generator.py          # Sinh câu trả lời + trích dẫn
│   ├── rewriter.py           # Query Rewriting từ lịch sử hội thoại
│   ├── build_index.py        # Build Chroma index + docstore từ data/chunks/
│   ├── vector_store/         # Chroma index (chunk con) - KHÔNG commit lên Git
│   └── docstore/             # parents.json (chunk cha)  - KHÔNG commit lên Git
│
├── data/                     # Người D phụ trách
│   ├── raw/                  # PDF văn bản luật gốc
│   ├── processed/            # Markdown đã làm sạch
│   ├── chunks/               # chunks.json chuẩn hóa theo Điều/Khoản/Điểm
│   ├── parse_pdf.py
│   ├── chunking.py
│   └── evaluation/
│       ├── test_questions.json
│       └── ragas_eval.py
│
├── frontend/                 # Người C phụ trách
│   ├── css/
│   ├── js/
│   ├── index.html            # Trang đăng nhập
│   ├── register.html         # Trang đăng ký
│   └── chat.html             # Giao diện chat chính
│
├── docs/
│   ├── API.md
│   └── setup.md
│
├── requirements.txt          # Dependencies Python dùng chung (backend + rag + data)
├── .env.example              # Mẫu biến môi trường (copy thành .env)
├── .gitignore
└── README.md
```

### 🔀 Quy ước phối hợp B ↔ D (khâu dữ liệu → index)

| Bước | Ai làm | Output |
|---|---|---|
| Parse PDF → Markdown | D (`data/parse_pdf.py`) | `data/processed/` |
| Chunking theo Điều/Khoản/Điểm | D (`data/chunking.py`) | `data/chunks/chunks.json` |
| Embedding + Build index | B (`rag/build_index.py`, dùng `rag/embedder.py`) | `rag/vector_store/` + `rag/docstore/` |

> Format `chunks.json` do B và D thống nhất, mô tả chi tiết trong `docs/setup.md`. Chỉ có **một** bộ code embedding duy nhất nằm trong `rag/embedder.py` — D không tự viết embedding riêng.

---

## ⚙️ Setup môi trường

### Yêu cầu
- Python 3.10+
- OpenAI API Key

### 1. Clone repo
```bash
git clone https://github.com/your-org/chatbot-phapluat.git
cd chatbot-phapluat
```

### 2. Tạo virtual environment & cài dependencies (1 venv duy nhất ở thư mục gốc)
```bash
python -m venv venv

# Windows (PowerShell)
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```


> Khi cài thêm thư viện mới: `pip install <tên>` xong phải cập nhật vào `requirements.txt` rồi mới commit.

### 3. Cấu hình biến môi trường
```bash
# Tạo file .env rồi điền giá trị thật vào
```

Nội dung `.env.example`:
```env
OPENAI_API_KEY= 

SECRET_KEY=your-jwt-secret-key-here
DATABASE_URL=sqlite:///./chatbot.db
EMBEDDING_MODEL=text-embedding-3-small
LLM_MODEL=gpt-4.1-mini

```

Các tham số kỹ thuật của pipeline đặt trong `rag/config.py`:
```python
CHILD_CHUNK_SIZE = 500        # tokens, chunk con theo Khoản/Điểm
TOP_K_RETRIEVE = 10           # số chunk lấy từ Chroma
TOP_N_RERANK = 4              # số chunk giữ lại sau LLM Reranker
MAX_HISTORY_TURNS = 5         # số lượt hội thoại dùng cho Query Rewriting
RERANKER_MODEL = "gpt-4.1-mini"
```

### 4. Build Chroma Index + Docstore (chạy 1 lần, hoặc khi dữ liệu thay đổi)
```bash
python -m rag.build_index
# → Tạo Chroma index tại rag/vector_store/
# → Tạo docstore chunk cha tại rag/docstore/parents.json
```

### 5. Chạy Backend
```bash
cd backend
uvicorn main:app --reload --port 8001
# → Chạy tại: http://localhost:8001
# → Swagger docs: http://localhost:8001/docs
```

### 6. Chạy Frontend

Dùng Live Server (VS Code extension) để tránh lỗi CORS khi gọi API.

---

## 🌿 Quy trình Git

### Nhánh
```
master          ← Production, chỉ merge khi hoàn thiện
└── dev       ← Nhánh phát triển chung
    ├── feature/backend-auth
    ├── feature/backend-api
    ├── feature/rag-pipeline
    ├── feature/frontend-auth
    ├── feature/frontend-chat
    └── feature/data-processing
```

### Quy tắc commit
```bash
feat: thêm tính năng mới
fix: sửa bug
docs: cập nhật tài liệu
refactor: tái cấu trúc code
test: thêm test
```

### Quy trình làm việc
```
1. git checkout dev
2. git pull origin dev
3. git checkout -b feature/ten-tinh-nang
4. ... làm việc ...
5. git add . && git commit -m "feat: mô tả"
6. git push origin feature/ten-tinh-nang
7. Tạo Pull Request vào dev
8. Chờ 1 người review → merge
```

---

## 📅 Timeline

| Tuần | Mục tiêu |
|---|---|
| 1 | Setup môi trường, Auth API, Mock API, Thu thập dữ liệu |
| 1 | RAG Pipeline cơ bản, API chat/lịch sử, Màn hình Login |
| 2 | Hoàn thiện Pipeline (reranking), Màn hình Chat, Chunking xong |
| 2 | Tích hợp toàn bộ, kết nối API thật |
| 3 | Kiểm thử RAGAS, Fix bug, Viết báo cáo |

---

## ⚠️ Lưu ý quan trọng

- **KHÔNG** commit file `.env` lên Git
- **KHÔNG** commit `rag/vector_store/` và `rag/docstore/` lên Git (đã thêm vào `.gitignore`, build lại bằng `python -m rag.build_index`)
- **KHÔNG** push thẳng lên `master`

---

## 📞 Liên hệ trưởng nhóm

> Hoàng Chí Phước - chiphuoc1947@gmail.com
