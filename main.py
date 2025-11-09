# /Users/seongjegeun/Downloads/pro03/main.py
# [버그 수정] AI가 'advice'에만 직업 언급하고 'recommendations'를 비워두는 치명적 버그 재수정
# [수정] AI의 작업 순서를 (1. 추천 리스트 생성 -> 2. 채팅 답변 생성)으로 강제함

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from openai import OpenAI
from dotenv import load_dotenv
import os, time, hashlib, json, re
from datetime import datetime

from database import create_document, get_document, get_firestore
import schemas

# ------------------------------------------------------
# 1️⃣ 환경 설정
# ------------------------------------------------------
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
db = get_firestore()

# ------------------------------------------------------
# 2️⃣ 유틸 함수
# ------------------------------------------------------
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def _extract_json_block(text: str) -> str:
    if not text:
        return text
    # 코드펜스 우선 제거
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if m:
        return m.group(1).strip()
    # 배열 형태 ([ ... ]) 지원
    m2 = re.search(r"($begin:math:display$[\\s\\S]*$end:math:display$)", text)
    if m2:
        return m2.group(1).strip()
    # 객체 형태 ({ ... }) 지원
    m3 = re.search(r"(\{[\s\S]*\})", text)
    if m3:
        return m3.group(1).strip()
    return text.strip()

def _strip_counselor_prefix(s: str) -> str:
    if not s:
        return s
    for token in ["counselor:", "Counselor:", "상담사:", "상담 교사:", "상담사 AI:", "상담교사:"]:
        s = s.replace(token, "")
    return s.strip()

def _normalize_recommendations(items):
    """
    프론트가 기대하는 key들(reason/company/outlook/competition)을 항상 제공.
    ✅ 3개 초과 시 자동 자르기 + 3개 미만 시 자동 채우기
    """
    norm = []
    for it in (items or []):
        job = it.get("job") or it.get("title") or it.get("직업")
        if not job or "추천 직업" in job:
            continue

        reason = it.get("reason") or it.get("사유") or it.get("이유") or ""
        company = it.get("company") or it.get("회사") or ""
        outlook = it.get("outlook") or it.get("전망") or ""
        competition = it.get("competition") or it.get("경쟁률") or ""

        norm.append({
            "job": job,
            "reason": reason,
            "company": company,
            "outlook": outlook,
            "competition": competition,
        })

    # ✅ 3개 이상이면 초과 항목 제거
    if len(norm) > 3:
        norm = norm[:3]

    # ✅ 3개 미만이면 빈 슬롯 채움
    while len(norm) < 3:
        norm.append({
            "job": f"추천 직업 {len(norm)+1}",
            "reason": "추천 사유가 없습니다.",
            "company": "",
            "outlook": "",
            "competition": "",
        })
    return norm

# ------------------------------------------------------
# 3️⃣ FastAPI 초기화
# ------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("✅ ChatGPT 진로상담 서버 시작됨.")
    yield

app = FastAPI(lifespan=lifespan)

# ✅ CORS 허용 (올바른 호출 형태)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ 정적 파일 설정
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# ✅ favicon 처리
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    icon_path = os.path.join(static_dir, "favicon.ico")
    return FileResponse(icon_path) if os.path.exists(icon_path) else FileResponse(os.path.join(static_dir, "bot-profile.png"))

# ------------------------------------------------------
# 4️⃣ HTML 라우트
# ------------------------------------------------------
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
    chat_html_path = os.path.join(static_dir, "chat.html")
    if os.path.exists(chat_html_path):
        return FileResponse(chat_html_path)
    index_html_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_html_path):
        return FileResponse(index_html_path)
    raise HTTPException(status_code=404, detail="Chat HTML file not found.")


# ------------------------------------------------------
# 5️⃣ 회원가입 / 로그인
# ------------------------------------------------------
@app.post("/api/register")
async def register_user(userid: str = Form(...), password: str = Form(...), name: str = Form(...)):
    if db.collection("users").document(userid).get().exists:
        return JSONResponse(status_code=400, content={"success": False, "message": "이미 존재하는 아이디입니다."})

    hashed_pw = hash_password(password)
    create_document("users", userid, {
        "User_ID": userid,
        "Password": hashed_pw,
        "Name": name,
        "Created_At": datetime.now().isoformat()
    })
    return JSONResponse(status_code=200, content={"success": True, "message": "회원가입이 완료되었습니다!"})

@app.post("/api/login")
async def login_user(userid: str = Form(...), password: str = Form(...)):
    user = get_document("users", userid)
    if not user or user["Password"] != hash_password(password):
        return JSONResponse(status_code=401, content={"success": False, "message": "아이디 또는 비밀번호가 일치하지 않습니다."})
    return JSONResponse(status_code=200, content={
        "success": True,
        "message": f"{user['Name']}님, 환영합니다!",
        "user_id": userid,
        "user_name": user["Name"]
    })

# ------------------------------------------------------
# 6️⃣ 회원정보 수정 API
# ------------------------------------------------------
@app.post("/api/update_profile")
async def update_profile(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    new_name = data.get("new_name")
    new_password = data.get("new_password", "")

    user_ref = db.collection("users").document(user_id)
    if not user_ref.get().exists:
        return JSONResponse(status_code=404, content={"success": False, "message": "사용자를 찾을 수 없습니다."})

    update_data = {}
    if new_name:
        update_data["Name"] = new_name
    if new_password:
        update_data["Password"] = hash_password(new_password)

    user_ref.update(update_data)
    print(f"🔄 회원정보 수정: {user_id}")
    return JSONResponse(status_code=200, content={"success": True, "message": "회원정보가 수정되었습니다."})

# ------------------------------------------------------
# 7️⃣ ChatGPT 챗봇 API (직업 추천 포함, counselor 제거)
#     ✅ response_model=schemas.ChatResponse : 프론트 일관성
# ------------------------------------------------------
@app.post("/api/chat", response_model=schemas.ChatResponse)
async def handle_chat(request: schemas.ChatRequest):
    try:
        start = time.time()
        user_input = request.user_input
        conversation_id = request.conversation_id

        # 1. 시스템 프롬프트 정의
        # 💡 [버그 수정] AI 작업 순서 변경 및 프롬프트 단순화
        system_prompt = f"""
당신은 학생의 대화를 분석하여 JSON 객체만 반환하는 AI입니다.
---
## [작업 순서]
1. (분석) 학생의 대화(history)와 현재 질문(user_input)에서 '게임', '유튜브', '연봉 높음' 등 핵심 관심사와 조건을 파악합니다.
2. (키워드) 1번에서 파악한 관심사를 'keywords' 리스트에 채웁니다. (예: [{{"label": "관심분야", "value": "게임"}}])
3. (추천) 1번의 관심사에 맞는 직업 3개를 'recommendations' 리스트에 채웁니다. 
   - 학생이 "유튜브", "게임"을 좋아한다면 -> '게임 유튜버', '게임 기획자'를 추천합니다.
   - 학생이 '연봉'을 물으면, 'competition' 필드에 "연봉: 4000~7000만원" 형식으로 관련 정보를 포함합니다.
   - 학생이 "또 다른 직업은 없어?"라고 물으면, *이전 대화(history)에서 추천한 직업은 제외*하고 *새로운* 직업을 추천합니다.
4. (답변) 'advice' 필드에는 3번에서 추천한 직업을 자연스럽게 소개하고, 학생의 다음 반응을 유도하는 **질문**을 포함합니다. (예: "게임을 좋아하신다면 '게임 기획자'는 어떠신가요? 이 직업에 대해 더 알려드릴까요?")

## [치명적인 JSON 규칙]
1. **무조건 JSON(큰따옴표 " 사용)만** 반환하세요. 코드 블록이나 다른 텍스트는 절대 금지입니다.
2. **[매우 중요] 'recommendations' 리스트가 *비어있지 않다면* (즉, 1개라도 직업을 추천했다면), 'advice' 텍스트에도 해당 직업명이 *반드시* 포함되어야 합니다.**
3. 추천할 직업이 *정말로* 없는 경우(예: '안녕하세요')에만 'recommendations'와 'keywords'를 `[]`로 반환합니다.
4. 'advice' 안에 직업명이 등장하면 반드시 'recommendations' 리스트에도 그 직업 정보를 포함하세요.
5. 'recommendations'가 비어 있다면, 기본 직업 하나를 자동으로 추가하세요.
6. 'recommendations'에는 최소 1개 이상의 직업이 반드시 있어야 합니다.
---
## [JSON 출력 예시 1: '유튜브'/'게임' 키워드 응답]
{{
  "advice": "게임을 좋아하고 유튜브를 즐겨 보시는군요. 그렇다면 '게임 기획자'나 '게임 유튜버'는 어떠신가요? '게임 기획자'는 게임의 규칙을 만드는 일이고, '게임 유튜버'는 게임 방송을 콘텐츠로 만듭니다. 두 직업 다 흥미로울 것 같은데, 더 궁금한 점이 있나요?",
  "recommendations": [
    {{"job": "게임 기획자", "reason": "게임을 좋아하고(e.g., 유튜브) 창의적인 일을 원해 추천합니다.", "company": "주요 게임사", "outlook": "밝음", "competition": "높음"}},
    {{"job": "게임 유튜버 (스트리머)", "reason": "게임과 유튜브 시청을 좋아하며, 방송 콘텐츠 제작에 흥미가 있을 수 있습니다.", "company": "유튜브, 치지직 등", "outlook": "경쟁이 치열하나 성공 시 높음", "competition": "매우 높음"}}
  ],
  "keywords": [{{"label": "관심분야", "value": "게임"}}, {{"label": "관심분야", "value": "유튜브"}}]
}}
---
## [JSON 출력 예시 2: 직업 추천이 *없는* 경우 (단순 인사)]
{{
  "advice": "안녕하세요. 저는 진로 상담사 AI예요. 궁금한 걸 편하게 물어봐요!",
  "recommendations": [],
  "keywords": []
}}
"""

        # 2. OpenAI에 보낼 메시지 리스트 구성
        messages_to_send = [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": "무조건 JSON 형식으로만 출력하세요. 다른 설명 문장 금지."}
        ]

        # 3. 이전 대화 기록(history)을 'user' / 'assistant' 역할로 매핑
        for msg in request.history[-6:]:
            role = msg.get("role")
            content = msg.get("content")
            
            if role == "student":
                messages_to_send.append({"role": "user", "content": content})
            elif role == "assistant" or role == "counselor":
                messages_to_send.append({"role": "assistant", "content": content})

        # 4. 현재 사용자 입력을 'user' 역할로 추가
        messages_to_send.append({"role": "user", "content": user_input})
        
        # OpenAI 호출
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages_to_send,
            temperature=0.7,
            max_tokens=800,
        )

        raw_answer = (response.choices[0].message.content or "").strip()
        print(f"💬 [AI 원본 응답] {raw_answer}")

        # JSON 파싱 예외 처리
        parsed = None
        advice = "죄송해요, 답변을 처리하지 못했습니다." # 기본 에러 메시지
        recs = []
        keywords = []

        try:
            json_block = _extract_json_block(raw_answer)
            parsed = json.loads(json_block)
            
            advice = _strip_counselor_prefix((parsed.get("advice") or "답변을 생성하지 못했습니다.").strip())
            recs = _normalize_recommendations(parsed.get("recommendations", []))
            keywords = parsed.get("keywords", []) 
            print("📊 반환 직전 keywords:", keywords)
            # ✅ [추가] 이전 추천 직업과 병합 (중복 방지)
            try:
                existing_doc = db.collection("conversations").where("conversation_id", "==", conversation_id).stream()
                old_recs = []
                for d in existing_doc:
                    data = d.to_dict()
                    recs = _normalize_recommendations(parsed.get("recommendations", []))
            except Exception as e:
                print(f"⚠️ 기존 추천 병합 실패: {e}")
            if not recs:
                recs = _normalize_recommendations([]) 
            if not recs or all(not r.get("job") or "추천 직업" in r.get("job") for r in recs):
                print("⚠️ recommendations 비어있음 → GPT에게 보조 요청 실행")
                
                extract_prompt = f"""
                문장 "{advice}" 에서 직업명을 모두 찾아 JSON 배열로만 출력하세요.
                출력 형식:
                [
                {{"job": "직업명", "reason": "대화 중 언급됨"}}
                ]
                JSON만 출력, 다른 말 금지.
                """

                sub_response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "system", "content": "당신은 문장에서 직업명을 추출하는 JSON 전문가입니다."},{"role": "user", "content": extract_prompt}],
                    temperature=0.3,
                    max_tokens=200
                )

                sub_text = _extract_json_block(sub_response.choices[0].message.content or "")
                try:
                    extracted = json.loads(sub_text)
                    if isinstance(extracted, list) and extracted:
                        recs = _normalize_recommendations(extracted)
                        print("🧩 sub_response:", sub_response.choices[0].message.content)
                        print("🧩 sub_text:", sub_text)
                except Exception as e:
                    print(f"⚠️ 보조 GPT 파싱 실패: {e}")

        except json.JSONDecodeError:
            print(f"❌ JSON 파싱 실패! (AI가 작은따옴표를 사용했거나 형식이 깨짐): {raw_answer}")
            advice = _strip_counselor_prefix(raw_answer)

            # 🔧 보조 GPT 강제 실행
            extract_prompt = f"""
            문장 "{advice}"에서 등장한 직업명을 모두 찾아 JSON 배열로만 출력하세요.
            출력 예시:
            [
            {{"job": "직업명", "reason": "대화 중 언급됨"}}
            ]
            JSON만 출력.
            """

            sub_response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "당신은 문장에서 직업명을 JSON 형식으로 추출하는 전문가입니다."},
                    {"role": "user", "content": extract_prompt}
                ],
                temperature=0,
                max_tokens=200
            )
            sub_text = _extract_json_block(sub_response.choices[0].message.content or "")
            try:
                extracted = json.loads(sub_text)
                if isinstance(extracted, list) and extracted:
                    recs = _normalize_recommendations(extracted)
            except Exception as e:
                print(f"⚠️ 보조 GPT 파싱 실패: {e}")


        # Firestore 저장 (세션별 독립 기록)
        db.collection("conversations").document().set({
            "conversation_id": conversation_id,
            "user_id": request.user_id,
            "user_input": user_input,
            "bot_reply": advice,
            "recommendations": recs,
            "keywords": keywords,
            "timestamp": datetime.now().isoformat()
        })

        # 히스토리 갱신
        new_history = request.history + [
            {"role": "student", "content": user_input},
            {"role": "assistant", "content": advice},
        ]

        print(f"✅ [AI 응답] {advice}")
        print(f"⏱️ 처리시간: {time.time() - start:.2f}초")

        # ✅ 항상 마지막에 normalize (3개 초과 시 잘라냄)
        recs = _normalize_recommendations(recs)

        print("📤 전송 직전 recommendations:", json.dumps(recs, ensure_ascii=False, indent=2))
        return schemas.ChatResponse(
            conversation_id=conversation_id,
            answer=advice,
            new_history=new_history,
            recommendations=recs,
            keywords=keywords
        )

    except Exception as e:
        print(f"❌ ChatGPT 오류: {e}")
        raise HTTPException(status_code=500, detail="응답 생성 중 오류 발생")
    


# ------------------------------------------------------
# 8️⃣ 서버 상태 확인
# ------------------------------------------------------
@app.get("/api/health")
async def health_check():
    return {"status": "ok", "chatgpt_connected": True}