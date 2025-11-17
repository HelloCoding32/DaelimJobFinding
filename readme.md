# FindJobAI — AI 진로 상담/추천 웹앱

FastAPI 기반의 진로 상담 챗봇/추천 서비스입니다. 학생 입력을 받아 OpenAI로 상담 메시지를 생성하고, 사전 로드한 직업/채용 데이터에서 전망·경쟁률·회사 정보를 조합해 대시보드로 보여줍니다. 로그인/회원가입과 대화 로그는 Firebase Firestore에 저장합니다.

## 주요 기능
- 챗봇 상담: OpenAI Chat Completions로 JSON 응답(`advice`, `recommendations`, `keywords`) 생성
- 직업 추천 보강: 로컬 JSON(`data/json/career_jobs_full.json`)과 CSV(`data/jobpostings_export.csv`)를 조회해 회사/전망/경쟁률을 매칭, 부족하면 OpenAI로 보완
- 사용자/세션 관리: 로그인·회원가입, 대화 로그 Firestore 저장
- 웹 프론트: `static`의 HTML/CSS/JS로 채팅 UI와 추천 대시보드 렌더링

## 코드 구조
- `main.py` : 앱 엔트리, FastAPI 앱 생성
- `app/`
  - `__init__.py` : 미들웨어, 정적 자원 마운트, lifespan(데이터 로드)
  - `routes.py` : 로그인/회원가입/채팅/헬스체크 API 및 HTML 라우팅
  - `services.py` : 직업/회사 조회, 전망/경쟁률 생성, 추천 정규화
  - `state.py` : OpenAI 클라이언트, 캐시/데이터 로드, 실행기 등 전역 상태
- `schemas.py` : Pydantic 스키마
- `static/` : `chat.html`, `css/chat.css`, `js/chat.js`
- `data/` : `json/career_jobs_full.json`, `jobpostings_export.csv`

## 준비물
- Firestore 서비스 키: `data/json/firebase-key.json`
- 데이터 파일: `data/json/career_jobs_full.json`, `data/jobpostings_export.csv`

## 설치
```bash
python -m venv venv
source venv/bin/activate   # Windows는 venv\Scripts\activate
pip install -r requirements.txt
```

## 실행
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
브라우저에서 `http://localhost:8000/chat` 접속.

## API 요약
- `POST /api/register` : userid, password, name (Form)
- `POST /api/login` : userid, password (Form)
- `POST /api/chat` : `ChatRequest`(JSON) → `ChatResponse`(JSON)
- `GET /api/health` : 데이터/캐시 카운트

## 참고
- 캐시 워밍업은 비활성화(즉시 응답 우선). 필요 시 `app/state.py`에서 활성화 로직 추가.
- 추천 카드의 회사 버튼은 CSV `link` 필드를 사용해 JobKorea 공고로 이동합니다.***
