# -*- coding: utf-8 -*-
"""
📘 ChatGPT Career Counseling Server — JSON + CSV + GPT Fallback + Parallel (Final)

사용 파일:
  - data/career_jobs_full.json
  - data/jobpostings_export.csv

기능:
  1) JSON에서 career info 읽기
  2) 없으면 GPT 자동 생성 (3개 병렬)
  3) CSV에서 유사 직군 기반 회사 1개 매칭
"""

from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from openai import OpenAI
from dotenv import load_dotenv

import os, json, re, csv, hashlib
from datetime import datetime
from typing import Any, Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor

# Firestore
from database import create_document, get_document, get_firestore
import schemas


# ============================================
# 1️⃣ 환경 설정
# ============================================
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
db = get_firestore()

CAREER_JOBS_DATA: List[Dict[str, Any]] = []
JOB_POSTINGS_DATA: List[Dict[str, Any]] = []

CAREER_DETAIL_CACHE: Dict[str, Tuple[str, str]] = {}  # outlook, competition

executor = ThreadPoolExecutor(max_workers=3)
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


# ============================================
# 2️⃣ 유틸 함수
# ============================================
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def _norm(s: Any) -> str:
    return str(s).strip() if s else ""

def _norm_key(s: Any) -> str:
    return re.sub(r"\s+", "", _norm(s).lower())

def _extract_json_block(text: str) -> str:
    if not text:
        return text
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if m:
        return m.group(1).strip()
    m2 = re.search(r"(\{[\s\S]*\})", text)
    if m2:
        return m2.group(1).strip()
    return text.strip()


# ============================================
# 3️⃣ JSON 매칭
# ============================================
def _find_job_json(job_title: str):
    norm_title = _norm(job_title)
    for j in CAREER_JOBS_DATA:
        if _norm(j.get("job")) == norm_title:
            return j
    return None


# ============================================
# 4️⃣ GPT 자동 생성 (전망/경쟁률)
# ============================================
def _generate_detail(job_name: str, summary: str, similar: str):
    prompt = f"""
너는 대한민국 고용노동부 진로 전문가야.

아래 직업의 '직업 전망'과 '직업 경쟁률'을 각각 2~3문장으로 자세히 작성해줘.

출력 형식(JSON) ONLY:

{{
  "prospect_text": "...",
  "competition": "..."
}}

직업명: {job_name}
요약: {summary or "정보 없음"}
유사직업: {similar or "정보 없음"}
"""

    try:
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.7
        )
        raw = resp.choices[0].message.content
        data = json.loads(_extract_json_block(raw))
        return (
            _norm(data.get("prospect_text")),
            _norm(data.get("competition"))
        )
    except:
        return "정보 없음", "정보 없음"


# ============================================
# 5️⃣ JSON → 없으면 GPT로 Outlook/Competition 생성
# ============================================
def get_career_info(job_title: str) -> Tuple[str, str]:
    key = _norm(job_title).lower()

    # 캐시 먼저
    if key in CAREER_DETAIL_CACHE:
        return CAREER_DETAIL_CACHE[key]

    job_json = _find_job_json(job_title)

    if job_json:
        outlook = _norm(job_json.get("prospect_text"))
        comp = _norm(job_json.get("market_summary") or job_json.get("competition"))

        if outlook and comp:
            CAREER_DETAIL_CACHE[key] = (outlook, comp)
            return outlook, comp

        summary = _norm(job_json.get("summary"))
        similar = _norm(job_json.get("similarJob"))
    else:
        summary, similar = "", ""

    outlook, comp = _generate_detail(job_title, summary, similar)
    CAREER_DETAIL_CACHE[key] = (outlook, comp)
    return outlook, comp


# ============================================
# 6️⃣ CSV 회사 1개 찾기
# ============================================
def _build_keywords(job_title: str, job_json=None):
    kw = set([job_title])
    if job_json:
        similar = _norm(job_json.get("similarJob"))
        for t in re.split(r"[,/·\s]+", similar):
            if len(t) >= 2:
                kw.add(t)
    return kw

def get_company(job_title: str) -> str:
    job_json = _find_job_json(job_title)
    keywords = _build_keywords(job_title, job_json)

    # CSV 먼저 검색
    for row in JOB_POSTINGS_DATA:
        title_norm = _norm_key(row.get("title"))
        comp = _norm(row.get("company"))

        for kw in keywords:
            if _norm_key(kw) in title_norm:
                return comp

    # JSON에도 있으면 사용
    if job_json:
        c = _norm(job_json.get("company"))
        if c:
            return c

    return "정보 없음"


# ============================================
# 7️⃣ 추천 직업 통합 병렬 처리 (핵심 FIX)
# ============================================
def _normalize_recommendations(items):
    items = items or []
    res = []

    # 🔥 병렬 실행 준비
    futures = []
    for it in items:
        job_title = it.get("job") or it.get("title")
        if not job_title:
            continue

        futures.append(
            (it, executor.submit(get_career_info, job_title))
        )

    # 🔥 모든 future 완료 후 result 가져오기 (순서 보장)
    for it, future in futures:
        job_title = it.get("job") or it.get("title")
        reason = it.get("reason") or "학생에게 적합한 직업입니다."

        outlook, competition = future.result()
        company = get_company(job_title)

        res.append({
            "job": job_title,
            "reason": reason,
            "company": company,
            "outlook": outlook,
            "competition": competition,
        })

    # 3개 보장
    while len(res) < 3:
        res.append({
            "job": f"추천 직업 {len(res)+1}",
            "reason": "상담을 통해 더 알아볼 수 있어요.",
            "company": "-",
            "outlook": "-",
            "competition": "-"
        })

    return res[:3]


# ============================================
# 8️⃣ lifespan — JSON & CSV 로드
# ============================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    global CAREER_JOBS_DATA, JOB_POSTINGS_DATA
    print("🚀 서버 시작 중...")

    # JSON
    jp = "./data/career_jobs_full.json"
    if os.path.exists(jp):
        with open(jp, "r", encoding="utf-8") as f:
            CAREER_JOBS_DATA = json.load(f)
        print(f"📂 직업 JSON 로드: {len(CAREER_JOBS_DATA)}개")

    # CSV
    cp = "./data/jobpostings_export.csv"
    if os.path.exists(cp):
        with open(cp, "r", encoding="utf-8-sig") as f:
            JOB_POSTINGS_DATA = list(csv.DictReader(f))
        print(f"📂 CSV 로드: {len(JOB_POSTINGS_DATA)}개")

    yield
    print("🛑 서버 종료")


# ============================================
# 9️⃣ FastAPI 설정
# ============================================
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


# ============================================
# 🔟 HTML 라우팅
# ============================================
@app.get("/", response_class=FileResponse)
async def root():
    return FileResponse(os.path.join(static_dir, "login.html"))

@app.get("/login", response_class=FileResponse)
async def login():
    return FileResponse(os.path.join(static_dir, "login.html"))

@app.get("/register", response_class=FileResponse)
async def register():
    return FileResponse(os.path.join(static_dir, "register.html"))

@app.get("/chat", response_class=FileResponse)
async def chat():
    return FileResponse(os.path.join(static_dir, "chat.html"))


# ============================================
# 1️⃣1️⃣ 회원가입 / 로그인
# ============================================
@app.post("/api/register")
async def register_user(userid: str = Form(...), password: str = Form(...), name: str = Form(...)):
    if db.collection("users").document(userid).get().exists:
        return JSONResponse(status_code=400, content={"success": False, "message": "이미 존재하는 아이디입니다."})

    create_document("users", userid, {
        "User_ID": userid,
        "Password": hash_password(password),
        "Name": name,
        "Created_At": datetime.now().isoformat()
    })
    return {"success": True, "message": "회원가입 완료!"}


@app.post("/api/login")
async def login_user(userid: str = Form(...), password: str = Form(...)):
    user = get_document("users", userid)
    if not user or user["Password"] != hash_password(password):
        return JSONResponse(status_code=401, content={"success": False, "message": "아이디 또는 비밀번호가 일치하지 않습니다."})

    return {
        "success": True,
        "message": f"{user['Name']}님, 환영합니다!",
        "user_id": userid,
        "user_name": user["Name"],
    }


# ============================================
# 1️⃣2️⃣ ChatGPT 상담
# ============================================
@app.post("/api/chat", response_model=schemas.ChatResponse)
async def chat_api(request: schemas.ChatRequest):
    try:
        user_msg = request.user_input

        system_prompt = """
당신은 학생들의 진로 상담을 도와주는 전문가입니다.
반드시 아래 JSON 형식으로만 출력하세요:

{
  "advice": "...",
  "recommendations": [
    {"job": "직업명", "reason": "추천 이유"}
  ],
  "keywords": [{"label": "관심분야", "value": "키워드"}]
}
"""

        msgs = [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": "설명 없이 JSON만 출력하세요."}
        ]

        for h in request.history[-6:]:
            msgs.append({
                "role": "user" if h["role"] == "student" else "assistant",
                "content": h["content"]
            })

        msgs.append({"role": "user", "content": user_msg})

        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=msgs,
            max_tokens=500,
            temperature=0.7
        )

        raw = resp.choices[0].message.content
        parsed = json.loads(_extract_json_block(raw))

        advice = parsed.get("advice")
        recs = parsed.get("recommendations", [])
        keywords = parsed.get("keywords", [])

        final_recs = _normalize_recommendations(recs)

        # Firestore 저장
        db.collection("conversations").document().set({
            "conversation_id": request.conversation_id,
            "user_id": request.user_id,
            "user_input": user_msg,
            "bot_reply": advice,
            "recommendations": final_recs,
            "keywords": keywords,
            "timestamp": datetime.now().isoformat()
        })

        new_history = request.history + [
            {"role": "student", "content": user_msg},
            {"role": "assistant", "content": advice}
        ]

        return schemas.ChatResponse(
            conversation_id=request.conversation_id,
            answer=advice,
            new_history=new_history,
            recommendations=final_recs,
            keywords=keywords
        )

    except Exception as e:
        print("❌ 에러:", e)
        raise HTTPException(status_code=500, detail="서버 오류 발생")


# ============================================
# 1️⃣3️⃣ Health Check
# ============================================
@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "json_data_count": len(CAREER_JOBS_DATA),
        "csv_data_count": len(JOB_POSTINGS_DATA),
        "cache_size": len(CAREER_DETAIL_CACHE),
    }
