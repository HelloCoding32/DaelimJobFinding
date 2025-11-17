from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime


# ------------------------------------------------------
# 👤 사용자 관련 스키마
# ------------------------------------------------------

class UserCreate(BaseModel):
    """회원가입 요청 스키마"""
    user_id: str
    password: str
    name: str


class UserLogin(BaseModel):
    """로그인 요청 스키마"""
    user_id: str
    password: str


class UserResponse(BaseModel):
    """로그인/회원가입 성공 시 응답"""
    success: bool
    message: str
    user_id: Optional[str] = None
    user_name: Optional[str] = None


# ------------------------------------------------------
# 💬 챗봇 관련 스키마
# ------------------------------------------------------

class ChatRequest(BaseModel):
    """
    클라이언트 → 서버로 보내는 챗봇 요청
    - user_id: 로그인한 사용자 ID
    - user_input: 학생의 질문
    - conversation_id: 대화 세션 ID (uuid 등)
    - history: 이전 대화 (role, content 구조)
    """
    user_id: Optional[str] = "guest"
    user_input: str
    conversation_id: str
    history: List[Dict[str, Any]] = []


class ChatResponse(BaseModel):
    """
    서버 → 클라이언트로 보내는 챗봇 응답
    - conversation_id: 현재 대화 세션 ID (세션 유지용)
    - answer: 챗봇의 조언 텍스트
    - new_history: 업데이트된 대화 히스토리
    - recommendations: 추천 직업 목록 (3개 + 이유 + 부가정보)
    - keywords: 학생 분석 키워드 및 적합도(선택)
    """
    conversation_id: str
    answer: str
    new_history: List[Dict[str, Any]]
    recommendations: List[Dict[str, str]] = []  # ✅ 직업 추천 결과 포함
    keywords: Optional[List[Dict[str, Any]]] = []  # ✅ 분석용 키워드 (예: [{"label": "창의력", "value": "높음"}])


# ------------------------------------------------------
# 🧾 Firestore 데이터 구조 검증용 (선택적)
# ------------------------------------------------------

class ConversationLog(BaseModel):
    """Firestore에 저장되는 1개의 대화 로그 구조"""
    conversation_id: str
    user_id: str
    turn_number: int
    speaker: str
    text: str
    summary_version: Optional[int] = 0
    created_at: Optional[str] = datetime.now().isoformat()


class ChatLog(BaseModel):
    """Firestore의 chat_logs 문서 구조"""
    user_id: str
    sender: str
    message: str
    created_at: Optional[str] = datetime.now().isoformat()