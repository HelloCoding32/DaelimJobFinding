import os
import json
import csv
import re
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor

from dotenv import load_dotenv
from openai import OpenAI

from .database import get_firestore

load_dotenv()

# 환경
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
db = get_firestore()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
FAST_SKIP_DETAIL = os.getenv("FAST_SKIP_DETAIL", "false").lower() in ("1", "true", "yes")

# 실행기 및 데이터
executor = ThreadPoolExecutor(max_workers=8)

CAREER_JOBS_DATA: List[Dict[str, Any]] = []
JOB_POSTINGS_DATA: List[Dict[str, Any]] = []

CAREER_DETAIL_CACHE: Dict[str, Tuple[str, str]] = {}  # outlook, competition
CAREER_JOB_MAP: Dict[str, Dict[str, Any]] = {}        # normalized title -> job json row
JOB_POSTINGS_CACHE: List[Tuple[str, str, str]] = []   # (normalized title, company, link)
COMPANY_CACHE: Dict[str, Tuple[str, str]] = {}        # normalized title -> (company, link)


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _norm(s: Any) -> str:
    return str(s).strip() if s else ""


def _norm_key(s: Any) -> str:
    return re.sub(r"\s+", "", _norm(s).lower())


def reset_company_cache():
    global COMPANY_CACHE
    COMPANY_CACHE = {}


def load_datasets():
    global CAREER_JOBS_DATA, JOB_POSTINGS_DATA, CAREER_JOB_MAP, JOB_POSTINGS_CACHE

    # JSON
    jp = "./data/json/career_jobs_full.json"
    if os.path.exists(jp):
        with open(jp, "r", encoding="utf-8") as f:
            CAREER_JOBS_DATA = json.load(f)
        print(f"📂 직업 JSON 로드: {len(CAREER_JOBS_DATA)}개")
        CAREER_JOB_MAP = {
            _norm_key(item.get("job")): item
            for item in CAREER_JOBS_DATA
            if item.get("job")
        }

    # CSV
    cp = "./data/jobpostings_export.csv"
    if os.path.exists(cp):
        with open(cp, "r", encoding="utf-8-sig") as f:
            JOB_POSTINGS_DATA = list(csv.DictReader(f))
        print(f"📂 CSV 로드: {len(JOB_POSTINGS_DATA)}개")
        JOB_POSTINGS_CACHE = [
            (_norm_key(row.get("title")), _norm(row.get("company")), _norm(row.get("link")))
            for row in JOB_POSTINGS_DATA
            if row.get("title")
        ]


def warm_cache(all_jobs: bool = False):
    """워밍업을 사용하지 않습니다(즉시 응답 우선)."""
    return


def warm_cache_background():
    """워밍업을 사용하지 않습니다(즉시 응답 우선)."""
    return
