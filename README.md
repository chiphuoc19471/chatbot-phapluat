# 🤖 Chatbot Tư Vấn Pháp Luật Lao Động
> Ứng dụng kỹ thuật RAG (Retrieval-Augmented Generation) và Mô hình Ngôn ngữ Lớn (LLM)

---

## 📌 Giới thiệu

Hệ thống chatbot hỏi đáp pháp luật lao động, giúp người lao động và doanh nghiệp tra cứu nhanh các quy định về hợp đồng lao động, lương thưởng, nghỉ phép, BHXH, tranh chấp lao động,... dựa trên Bộ luật Lao động 2019 và các văn bản pháp luật liên quan.

---

## 👥 Nhóm phát triển

| Người | Vai trò | Phụ trách |
|---|---|---|
| Nguyễn Tiến Lộc (A)| Backend | FastAPI, Auth JWT, Database, API |
| Hoàng Chí Phước (B)| Team Lead + RAG Engineer | LangChain, FAISS, Embedding, RAG Pipeline |
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
┌───────▼──────────┐    ┌──────────▼──────────────────┐
│  RAG Pipeline    │    │     Database (SQLite)        │
│  LangChain       │    │  users, conversations,       │
│  FAISS + bge-m3  │    │  messages                    │
│  GPT-4o Mini     │    └─────────────────────────────-┘
└──────────────────┘
```

---

## 🛠️ Tech Stack

| Thành phần | Công nghệ |
|---|---|
| Frontend | React + Tailwind CSS |
| Backend | FastAPI (Python 3.10+) |
| LLM | GPT-4o Mini (OpenAI) |
| Embedding | `BAAI/bge-m3` |
| Vector DB | FAISS |
| RAG Framework | LangChain |
| Database | SQLite |

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
│   ├── auth.py
│   └── requirements.txt
│
├── rag/                      # Người B phụ trách
│   ├── pipeline.py
│   ├── embedder.py
│   ├── retriever.py
│   ├── generator.py
│   ├── rewriter.py
│   └── vector_store/
│
├── data/                     # Người D phụ trách
│   ├── raw/
│   ├── processed/
│   ├── chunks/
│   ├── parse_pdf.py
│   ├── chunking.py
│   ├── build_index.py
│   └── evaluation/
│       ├── test_questions.json
│       └── ragas_eval.py
│
├── frontend/                 # Người C phụ trách
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Login.jsx
│   │   │   ├── Register.jsx
│   │   │   └── Chat.jsx
│   │   ├── components/
│   │   │   ├── ChatBox.jsx
│   │   │   ├── Sidebar.jsx
│   │   │   └── Message.jsx
│   │   └── services/
│   │       └── api.js
│   └── package.json
│
├── docs/
│   ├── API.md
│   └── setup.md
│
├── .gitignore
└── README.md
```

---

## 🚀 Hướng dẫn cài đặt & chạy

### Yêu cầu
- Python 3.10+
- Node.js 18+
- OpenAI API Key

### 1. Clone repo
```bash
git clone https://github.com/your-org/chatbot-phapluat.git
cd chatbot-phapluat
```

### 2. Tạo file .env
```bash
# Tạo file .env trong thư mục gốc
cp .env.example .env
# Điền API key vào file .env
```

### 3. Chạy Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
uvicorn main:app --reload
# → Chạy tại: http://localhost:8000
# → Swagger docs: http://localhost:8000/docs
```

### 4. Build FAISS Index (chạy 1 lần)
```bash
cd data
python build_index.py
# → Tạo file index tại rag/vector_store/
```

### 5. Chạy Frontend
```bash
cd frontend
npm install
npm start
# → Chạy tại: http://localhost:3000
```

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
- **KHÔNG** push thẳng lên `master` 

---

## 📞 Liên hệ trưởng nhóm

> Hoàng Chí Phước - chiphuoc1947@gmail.com
