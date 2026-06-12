import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4.1-mini")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
CHILD_CHUNK_SIZE = 500   
TOP_K_RETRIEVE = 30       # số child chunk lấy từ Chroma
TOP_N_RERANK = 8          # số parent giữ lại sau LLM Reranker
MAX_HISTORY_TURNS = 5     # số lượt hội thoại dùng cho Query Rewriting
RERANKER_MODEL = "gpt-4.1-mini"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VECTOR_STORE_DIR = os.path.join(BASE_DIR, "vector_store")
DOCSTORE_PATH = os.path.join(BASE_DIR, "docstore", "parents.json")
CHUNKS_DIR = os.path.join(BASE_DIR, "..", "data", "chunks")
