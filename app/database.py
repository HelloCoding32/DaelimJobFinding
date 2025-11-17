import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
import os, json

# -----------------------------------------------------------
# 1️⃣ .env 환경 변수 로드
# -----------------------------------------------------------
load_dotenv()

FIREBASE_CREDENTIAL_PATH = os.getenv("FIREBASE_CREDENTIAL_PATH")
FIREBASE_KEY_JSON = os.getenv("FIREBASE_KEY_JSON")

if not FIREBASE_CREDENTIAL_PATH and not FIREBASE_KEY_JSON:
    raise ValueError("❌ Firebase 인증정보가 없습니다. .env에 FIREBASE_CREDENTIAL_PATH 또는 FIREBASE_KEY_JSON을 설정하세요.")

# -----------------------------------------------------------
# 2️⃣ Firebase 초기화 (이미 초기화된 경우 재사용)
# -----------------------------------------------------------
try:
    if not firebase_admin._apps:
        # ✅ JSON 문자열로 전달된 경우 (Render 환경)
        if FIREBASE_KEY_JSON:
            cred_dict = json.loads(FIREBASE_KEY_JSON)
            cred = credentials.Certificate(cred_dict)
        else:
            # ✅ 로컬 개발용 키 경로 기반
            cred = credentials.Certificate(FIREBASE_CREDENTIAL_PATH)

        firebase_admin.initialize_app(cred)
        print("✅ Firebase 초기화 완료.")
    else:
        print("ℹ️ Firebase 이미 초기화됨. 기존 인스턴스 재사용 중.")
except Exception as e:
    print(f"⚠️ Firebase 초기화 중 오류 발생: {e}")

# -----------------------------------------------------------
# 3️⃣ Firestore 클라이언트
# -----------------------------------------------------------
db = firestore.client()

# -----------------------------------------------------------
# 4️⃣ Firestore CRUD 함수
# -----------------------------------------------------------
def get_firestore():
    """Firestore 클라이언트 반환"""
    return db


def create_document(collection, doc_id, data):
    """문서 생성/덮어쓰기"""
    db.collection(collection).document(doc_id).set(data)
    print(f"📝 Firestore 문서 생성: {collection}/{doc_id}")


def get_document(collection, doc_id):
    """문서 조회"""
    doc = db.collection(collection).document(doc_id).get()
    return doc.to_dict() if doc.exists else None


def update_document(collection_name: str, doc_id: str, data: dict):
    """문서 업데이트"""
    db.collection(collection_name).document(doc_id).update(data)
    print(f"🔄 {collection_name}/{doc_id} 문서가 업데이트되었습니다.")


def delete_document(collection_name: str, doc_id: str):
    """문서 삭제"""
    db.collection(collection_name).document(doc_id).delete()
    print(f"🗑️ {collection_name}/{doc_id} 문서가 삭제되었습니다.")