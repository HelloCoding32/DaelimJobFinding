# /Users/seongjegeun/Downloads/pro03/models.py
# Firebase Firestore 기반 모델 구조 정의

from datetime import datetime

# ------------------------------------------------------
# 사용자 데이터 모델 (회원가입 / 로그인용)
# ------------------------------------------------------
class UserModel:
    def __init__(self, user_id: str, password: str, name: str, created_at=None):
        self.User_ID = user_id
        self.Password = password
        self.Name = name
        self.Created_At = created_at or datetime.now().isoformat()

    def to_dict(self):
        return {
            "User_ID": self.User_ID,
            "Password": self.Password,
            "Name": self.Name,
            "Created_At": self.Created_At
        }


# ------------------------------------------------------
# 대화 기록 모델 (턴 단위 저장)
# ------------------------------------------------------
class ConversationModel:
    def __init__(self, conversation_id: str, user_id: str, turn_number: int,
                 speaker: str, text: str, summary_version: int = 0, context_summary: str = None):
        self.Conversation_ID = conversation_id
        self.User_ID = user_id
        self.Turn_Number = turn_number
        self.Speaker = speaker
        self.Text = text
        self.Context_Summary = context_summary
        self.Summary_Version = summary_version
        self.Created_At = datetime.now().isoformat()

    def to_dict(self):
        return {
            "Conversation_ID": self.Conversation_ID,
            "User_ID": self.User_ID,
            "Turn_Number": self.Turn_Number,
            "Speaker": self.Speaker,
            "Text": self.Text,
            "Context_Summary": self.Context_Summary,
            "Summary_Version": self.Summary_Version,
            "Created_At": self.Created_At
        }


# ------------------------------------------------------
# 💬 채팅 로그 모델 (전체 채팅 저장)
# ------------------------------------------------------
class ChatLogModel:
    def __init__(self, user_id: str, sender: str, message: str, created_at=None):
        self.User_ID = user_id
        self.Sender = sender
        self.Message = message
        self.Created_At = created_at or datetime.now().isoformat()

    def to_dict(self):
        return {
            "User_ID": self.User_ID,
            "Sender": self.Sender,
            "Message": self.Message,
            "Created_At": self.Created_At
        }