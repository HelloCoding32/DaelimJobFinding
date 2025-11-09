import os
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

# -----------------------------------------------------------
# 1️⃣ .env 환경 변수 로드
# -----------------------------------------------------------
load_dotenv()

FIREBASE_CREDENTIAL_PATH = os.getenv("FIREBASE_CREDENTIAL_PATH")

if not FIREBASE_CREDENTIAL_PATH:
    raise ValueError("❌ 환경변수 'FIREBASE_CREDENTIAL_PATH'가 설정되지 않았습니다. .env 파일을 확인하세요.")

# -----------------------------------------------------------
# 2️⃣ Firebase 초기화 (앱이 이미 초기화되어 있다면 재사용)
# -----------------------------------------------------------
# ✅ 수정 포인트: firebase_admin._apps 사용
if not firebase_admin._apps:  
    cred = credentials.Certificate(FIREBASE_CREDENTIAL_PATH)
    firebase_admin.initialize_app(cred)
    print("✅ Firebase 초기화 완료.")
else:
    print("ℹ️ Firebase 이미 초기화됨. 기존 인스턴스 재사용 중.")

# Firestore 클라이언트 가져오기
db = firestore.client()

# -----------------------------------------------------------
# 3️⃣ Firestore 공통 CRUD 함수
# -----------------------------------------------------------
def get_firestore():
    """Firestore 인스턴스 반환"""
    return db


def create_document(collection_name: str, doc_id: str, data: dict):
    """문서 생성 또는 덮어쓰기"""
    db.collection(collection_name).document(doc_id).set(data)
    print(f"✅ {collection_name}/{doc_id} 문서가 생성되었습니다.")


def get_document(collection_name: str, doc_id: str):
    """문서 읽기"""
    doc_ref = db.collection(collection_name).document(doc_id)
    doc = doc_ref.get()
    if doc.exists:
        print(f"📄 {collection_name}/{doc_id} 문서가 조회되었습니다.")
        return doc.to_dict()
    else:
        print(f"⚠️ {collection_name}/{doc_id} 문서를 찾을 수 없습니다.")
        return None


def update_document(collection_name: str, doc_id: str, data: dict):
    """문서 업데이트"""
    db.collection(collection_name).document(doc_id).update(data)
    print(f"🔄 {collection_name}/{doc_id} 문서가 업데이트되었습니다.")


def delete_document(collection_name: str, doc_id: str):
    """문서 삭제"""
    db.collection(collection_name).document(doc_id).delete()
    print(f"🗑️ {collection_name}/{doc_id} 문서가 삭제되었습니다.")