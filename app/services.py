import json
import re
from datetime import datetime
from typing import Any, Dict, List, Tuple

from . import state


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


def _find_job_json(job_title: str):
    norm_title = state._norm_key(job_title)
    return state.CAREER_JOB_MAP.get(norm_title)


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
        resp = state.client.chat.completions.create(
            model=state.OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.7
        )
        raw = resp.choices[0].message.content
        data = json.loads(_extract_json_block(raw))
        return (
            state._norm(data.get("prospect_text")),
            state._norm(data.get("competition"))
        )
    except:
        return "정보 없음", "정보 없음"


def get_career_info(job_title: str) -> Tuple[str, str]:
    key = state._norm(job_title).lower()

    if key in state.CAREER_DETAIL_CACHE:
        return state.CAREER_DETAIL_CACHE[key]

    job_json = _find_job_json(job_title)

    if job_json:
        outlook = state._norm(job_json.get("prospect_text"))
        comp = state._norm(job_json.get("market_summary") or job_json.get("competition"))

        if outlook and comp:
            state.CAREER_DETAIL_CACHE[key] = (outlook, comp)
            return outlook, comp

        summary = state._norm(job_json.get("summary"))
        similar = state._norm(job_json.get("similarJob"))
    else:
        summary, similar = "", ""

    outlook, comp = _generate_detail(job_title, summary, similar)
    state.CAREER_DETAIL_CACHE[key] = (outlook, comp)
    return outlook, comp


def _build_keywords(job_title: str, job_json=None):
    kw = set([job_title])
    if job_json:
        similar = state._norm(job_json.get("similarJob"))
        for t in re.split(r"[,/·\s]+", similar):
            if len(t) >= 2:
                kw.add(t)
    return kw


def get_company(job_title: str) -> Tuple[str, str]:
    norm_title = state._norm_key(job_title)
    if norm_title in state.COMPANY_CACHE:
        return state.COMPANY_CACHE[norm_title]

    job_json = _find_job_json(job_title)
    keywords = _build_keywords(job_title, job_json)
    kw_norms = {state._norm_key(kw) for kw in keywords}

    for title_norm, comp, link in state.JOB_POSTINGS_CACHE:
        for kw in kw_norms:
            if kw in title_norm:
                state.COMPANY_CACHE[norm_title] = (comp, link)
                return comp, link

    if job_json:
        c = state._norm(job_json.get("company"))
        l = state._norm(job_json.get("link"))
        if c:
            state.COMPANY_CACHE[norm_title] = (c, l)
            return c, l

    state.COMPANY_CACHE[norm_title] = ("정보 없음", "")
    return "정보 없음", ""


def normalize_recommendations(items):
    items = items or []
    res = []

    futures = []
    for it in items:
        job_title = it.get("job") or it.get("title")
        if not job_title:
            continue

        futures.append(
            (it, state.executor.submit(get_career_info, job_title))
        )

    for it, future in futures:
        job_title = it.get("job") or it.get("title")
        reason = it.get("reason") or "학생에게 적합한 직업입니다."

        outlook, competition = future.result()
        company, link = get_company(job_title)

        res.append({
            "job": job_title,
            "reason": reason,
            "company": company,
            "link": link,
            "outlook": outlook,
            "competition": competition,
        })

    while len(res) < 3:
        res.append({
            "job": f"추천 직업 {len(res)+1}",
            "reason": "상담을 통해 더 알아볼 수 있어요.",
            "company": "-",
            "outlook": "-",
            "competition": "-"
        })

    return res[:3]
