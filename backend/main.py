from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from models.user import User
from models.conversation import Conversation, Message
from routers import auth, chat, history

# Automatically create all SQLite database tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Chatbot Tư Vấn Pháp Luật Lao Động - API",
    description="Hệ thống Backend cung cấp các API xác thực người dùng và hỏi đáp tư vấn luật lao động.",
    version="1.0.0"
)

# CORS middleware configuration
# Allows requests from frontend applications (e.g. running on localhost ports, live-server, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Set to specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(history.router)

@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Chào mừng đến với API Chatbot Tư Vấn Pháp Luật Lao Động!",
        "docs_url": "/docs"
    }
