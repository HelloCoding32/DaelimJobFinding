# AI 진로 상담 챗봇 프로젝트 실행 가이드

이 문서는 FastAPI 기반 AI 진로 상담 챗봇 프로젝트를 새 로컬 환경에서 실행하는 방법을 안내합니다.

1. Python 및 라이브러리 설치

1-1. Python 설치
이 프로젝트는 **Python 3.10 이상** 버전이 필요합니다. 새 컴퓨터에 Python이 설치되어 있는지 확인하세요.

1-2. 필수 라이브러리 설치
터미널(CMD 또는 PowerShell)을 열고, 이 프로젝트 폴더(`D:\pro03`)로 이동한 뒤 다음 명령어를 실행하여 모든 필수 라이브러리를 설치합니다.

(설치한 드라이브 폴더로 이동)
cd /d D:\pro03
(필요한 라이브러리 설치)
pip install -r requirements.txt

---

## 2. 🗄️ 데이터베이스(DB) 설정 (MySQL)

이 프로젝트는 **MySQL (또는 MariaDB)** 서버를 사용합니다.

### 2-1. DB 서버 실행
새 컴퓨터에 MySQL/MariaDB 서버가 설치되어 있어야 하며, **현재 실행 중**인지 확인하세요.

### 2-2. DB 접속 정보 확인
`database.py` 파일을 열어, `DB_HOST`, `DB_USER`, `DB_PASSWD` 값이 로컬 DB 서버의 접속 정보와 일치하는지 확인합니다. (기본 설정은 `root` / `1234` 입니다.)

### 2-3. 데이터베이스 생성 (필수)
서버가 `User_Table`, `Conversation_Table`을 생성할 수 있도록, **`fastapi_db`**라는 이름의 데이터베이스가 미리 존재해야 합니다.

등 DB 관리 툴을 이용해 MySQL에 접속한 뒤, 다음 SQL 쿼리를 **한 번만** 실행하세요.


CREATE DATABASE fastapi_db;


---

## 3. 🧠 AI 모델 파일 준비

챗봇의 '뇌'와 '백과사전'에 해당하는 대용량 파일 3개가 필요합니다. 이 파일들은 용량이 커서 프로젝트 폴더에 포함되어 있지 않을 수 있습니다.

`main.py` 파일이 있는 `D:\pro03` 폴더 안에 **아래 3개 파일이 있는지 확인**하고, 없다면 별도로 복사해 넣어야 합니다.

1.  `EXAONE-3.0-7.8B-Instruct.Q4_K_M.gguf` (약 4.6GB)
2.  `careernet_index_v2.faiss`
3.  `careernet_meta_v2.npy`

(엑사원모델은 EXAONE-3.0-7.8B-Instruct.Q4_K_M.gguf 검색 후 허깅페이스에서 다운로드)
---

## 4. 🚀 FastAPI 서버 실행

위 3단계가 모두 완료되었으면, 터미널에서 다음 명령어를 입력하여 FastAPI 서버를 시작합니다.

```bash
cd D:\pro03
uvicorn main:app --reload
```
(폴더 위치에서 실행)

서버가 정상적으로 켜지면, AI 모델 로딩을 시작합니다. `n_gpu_layers: 0` (CPU 모드)이므로 로딩에 **1~2분 정도 소요**될 수 있습니다.

터미널에 다음과 같은 로그가 뜨면 성공입니다.

```log
...
✅ 챗봇 엔진 로딩 완료! 서버가 준비되었습니다.
...
INFO:     Application startup complete.
INFO:     Uvicorn running on [http://127.0.0.1:8000](http://127.0.0.1:8000) (Press CTRL+C to quit)
```

---

## 5. 🌐 접속 및 테스트

서버가 켜진 것을 확인한 후, 웹 브라우저를 열어 다음 주소로 접속합니다.

* **로그인 페이지 (시작 페이지):**
    `http://127.0.0.1:8000/`

* **회원가입 페이지:**
    `http://127.0.0.1:8000/register`