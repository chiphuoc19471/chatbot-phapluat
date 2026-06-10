import os
import sys
import unittest
from fastapi.testclient import TestClient

# Ensure the backend directory is in python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import app
from database import Base, engine, SessionLocal
from models.user import User
from models.conversation import Conversation, Message

class TestChatbotAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create test client
        cls.client = TestClient(app)
        # Clear database for testing (since it's sqlite, we can recreate tables or delete all rows)
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

        cls.test_email = "testuser@example.com"
        cls.test_password = "securepassword123"
        cls.test_name = "Test User Lộc"

    def test_01_register_user(self):
        # 1. Register new user
        response = self.client.post(
            "/auth/register",
            json={
                "email": self.test_email,
                "password": self.test_password,
                "name": self.test_name
            }
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["message"], "Đăng ký thành công")
        self.assertTrue("user_id" in data)

        # 2. Register with duplicate email
        response_dup = self.client.post(
            "/auth/register",
            json={
                "email": self.test_email,
                "password": "anotherpassword",
                "name": "Another Name"
            }
        )
        self.assertEqual(response_dup.status_code, 400)
        self.assertEqual(response_dup.json()["detail"], "Email đã được sử dụng")

    def test_02_login_user(self):
        # 1. Login with correct credentials
        response = self.client.post(
            "/auth/login",
            json={
                "email": self.test_email,
                "password": self.test_password
            }
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue("access_token" in data)
        self.assertEqual(data["token_type"], "bearer")
        self.assertEqual(data["user"]["email"], self.test_email)
        self.assertEqual(data["user"]["name"], self.test_name)
        
        # Save token for subsequent tests
        self.__class__.token = data["access_token"]

        # 2. Login with incorrect credentials
        response_wrong = self.client.post(
            "/auth/login",
            json={
                "email": self.test_email,
                "password": "wrongpassword"
            }
        )
        self.assertEqual(response_wrong.status_code, 401)
        self.assertEqual(response_wrong.json()["detail"], "Email hoặc mật khẩu không đúng")

    def test_03_chat_unauthorized(self):
        # Send question without Authorization header
        response = self.client.post(
            "/chat",
            json={"question": "Thử việc tối đa bao nhiêu ngày?"}
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Token không hợp lệ hoặc đã hết hạn")

    def test_04_chat_authorized(self):
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # 1. Start new conversation
        response = self.client.post(
            "/chat",
            json={"question": "Quy định về thời gian thử việc?"},
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue("answer" in data)
        self.assertTrue(len(data["sources"]) > 0)
        self.assertEqual(data["sources"][0]["law"], "Bộ luật Lao động 2019")
        self.assertEqual(data["sources"][0]["article"], "Điều 25")
        self.assertTrue("conversation_id" in data)
        self.assertTrue("message_id" in data)

        self.__class__.conversation_id = data["conversation_id"]

        # 2. Continue conversation
        response_cont = self.client.post(
            "/chat",
            json={
                "question": "Tính lương làm thêm giờ như thế nào?",
                "conversation_id": self.conversation_id
            },
            headers=headers
        )
        self.assertEqual(response_cont.status_code, 200)
        data_cont = response_cont.json()
        self.assertEqual(data_cont["conversation_id"], self.conversation_id)
        self.assertTrue("lương" in data_cont["answer"].lower() or "tiền lương" in data_cont["answer"].lower())

    def test_05_get_history(self):
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Get history list
        response = self.client.get("/history", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], self.conversation_id)
        self.assertEqual(data[0]["message_count"], 4)  # 2 questions + 2 answers = 4 messages

    def test_06_get_conversation_detail(self):
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Get details
        response = self.client.get(f"/history/{self.conversation_id}", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], self.conversation_id)
        self.assertEqual(len(data["messages"]), 4)
        
        # Verify first message is user question
        self.assertEqual(data["messages"][0]["role"], "user")
        self.assertEqual(data["messages"][0]["content"], "Quy định về thời gian thử việc?")
        
        # Verify second message is assistant answer and has sources parsed
        self.assertEqual(data["messages"][1]["role"], "assistant")
        self.assertEqual(data["messages"][1]["sources"][0]["law"], "Bộ luật Lao động 2019")

    def test_07_delete_conversation(self):
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Delete conversation
        response = self.client.delete(f"/history/{self.conversation_id}", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Đã xóa hội thoại thành công")

        # Verify deleted
        response_get = self.client.get(f"/history/{self.conversation_id}", headers=headers)
        self.assertEqual(response_get.status_code, 404)
        self.assertEqual(response_get.json()["detail"], "Không tìm thấy hội thoại")

if __name__ == "__main__":
    unittest.main()
