from fastapi import APIRouter, FastAPI, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
import os
import json
from datetime import datetime

from . import schemas, services, state
from .database import create_document, get_document

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
HTML_DIR = os.path.join(STATIC_DIR, "html")

router = APIRouter()


@router.get("/", response_class=FileResponse)
async def root():
    return FileResponse(os.path.join(HTML_DIR, "login.html"))


@router.get("/login", response_class=FileResponse)
async def login():
    return FileResponse(os.path.join(HTML_DIR, "login.html"))


@router.get("/register", response_class=FileResponse)
async def register():
    return FileResponse(os.path.join(HTML_DIR, "register.html"))


@router.get("/chat", response_class=FileResponse)
async def chat():
    return FileResponse(os.path.join(HTML_DIR, "chat.html"))


@router.post("/api/register")
async def register_user(userid: str = Form(...), password: str = Form(...), name: str = Form(...)):
    if state.db.collection("users").document(userid).get().exists:
        return JSONResponse(status_code=400, content={"success": False, "message": "이미 존재하는 아이디입니다."})

    create_document("users", userid, {
        "User_ID": userid,
        "Password": state.hash_password(password),
        "Name": name,
        "Created_At": datetime.now().isoformat()
    })
    return {"success": True, "message": "회원가입 완료!"}


@router.post("/api/login")
async def login_user(userid: str = Form(...), password: str = Form(...)):
    user = get_document("users", userid)
    if not user or user["Password"] != state.hash_password(password):
        return JSONResponse(status_code=401, content={"success": False, "message": "아이디 또는 비밀번호가 일치하지 않습니다."})

    return {
        "success": True,
        "message": f"{user['Name']}님, 환영합니다!",
        "user_id": userid,
        "user_name": user["Name"],
    }


@router.post("/api/chat", response_model=schemas.ChatResponse)
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

- keywords 작성 규칙:
  - 학생이 직접 말한 단어/표현만 사용하여 2~4개의 짧은 명사/형용사로 요약합니다.
  - 예시는 "경영, 경제, 분석, 연봉 높음"처럼 불필요한 접미사 없이 핵심 단어만 사용합니다.
  - 모델이 추정한 새 키워드를 추가하지 말고, 입력에 등장한 단어만 사용합니다.
  - "관련된/관심 분야" 같은 서술형 표현은 금지하고, 콤마로 구분한 단어 리스트만 작성합니다.
"""

        msgs = [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": "설명 없이 JSON만 출력하세요."}
        ]

        for h in request.history[-3:]:
            msgs.append({
                "role": "user" if h["role"] == "student" else "assistant",
                "content": h["content"]
            })

        msgs.append({"role": "user", "content": user_msg})

        resp = state.client.chat.completions.create(
            model=state.OPENAI_MODEL,
            messages=msgs,
            max_tokens=320,
            temperature=0.7,
            response_format={"type": "json_object"}
        )

        raw = resp.choices[0].message.content
        try:
            parsed = json.loads(services._extract_json_block(raw))
        except Exception:
            parsed = {}

        advice = parsed.get("advice") or raw or ""
        recs = parsed.get("recommendations", [])
        keywords = parsed.get("keywords", [])

        final_recs = services.normalize_recommendations(recs)

        state.db.collection("conversations").document().set({
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


@router.get("/api/health")
async def health():
    return {
        "status": "ok",
        "json_data_count": len(state.CAREER_JOBS_DATA),
        "csv_data_count": len(state.JOB_POSTINGS_DATA),
        "cache_size": len(state.CAREER_DETAIL_CACHE),
    }
