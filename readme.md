📘 AI 진로 상담 서버

AIHub 상담 데이터, CareerNet Open API, Redis 캐싱, FAISS RAG, LLaMA_CPP 모델, ChatGPT API를 통합한
실시간 AI 진로 상담 시스템 서버(FastAPI) 입니다.

Render 서버에서 자동 배포되며, Firestore를 통해 사용자 데이터 및 대화 이력을 저장합니다.

📂 주요 기능

🔹 1. 실시간 AI 진로 상담
	•	ChatGPT API 기반 자연스러운 대화
	•	사용자의 선호도(연봉, 직군, 관심사 등) 자동 추출
	•	EXAONE 또는 LLaMA-CPP 로컬 모델 사용 가능

🔹 2. 직업 추천 엔진
	•	Firestore에 사용자 프로필 저장
	•	CareerNet Open API 기반 직업/직군/자격증 정보 조회
	•	FAISS + SentenceTransformer 로 RAG 검색 기능
	•	Redis 캐싱하여 API 호출 최소화

🔹 3. 회사 정보 연동 (FAISS 기반)
	•	search_company() 로 기업 데이터 벡터 검색
	•	(직업 → 관련 기업 리스트) 자동 연결

🔹 4. Firebase Firestore 연동
	•	create_document(), get_document()
	•	로그인/회원가입/대화 히스토리 저장

🔹 5. Render 서버 배포 최적화
	•	Uvicorn + Gunicorn 조합
	•	CPU-only 환경에 맞춘 torch/llama-cpp-python 버전 조정
	•	.env 기반 API 키 관리

⚙️ 설치 & 실행
1. 가상환경 생성
python3 -m venv venv
source venv/bin/activate
2. 라이브러리 설치
pip install -r requirements.txt
3. 환경변수(.env) 설정
OPENAI_API_KEY=your_openai_key
CAREERNET_API_KEY=your_careernet_key
FIREBASE_CREDENTIALS=firebase-admin-key.json
REDIS_URL=redis://localhost:6379
