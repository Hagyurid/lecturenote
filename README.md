# LectureNote Local Action Server

Custom GPT가 긴 강의 정리 작업을 진행할 때 현재 진행 상태와 생성 결과를 저장하는 FastAPI 서버입니다.

## 핵심 구조

- 원본 강의자료, 전사본, 교재, 과거 시험 자료는 ChatGPT에 업로드합니다.
- 이 서버는 원본 파일을 저장하지 않습니다.
- 이 서버는 GPT가 생성한 정리본, 이미지 삽입 목록, 교재 보강 목록, 수식 검수 목록, 확인 필요 목록만 로컬 SQLite에 저장합니다.
- OpenAI API를 호출하지 않습니다.

## 저장 방식

기본 로컬 저장:

```bash
data/lecture_actions.sqlite3
```

Render Persistent Disk 사용 시:

```bash
/var/data/lecture_actions.sqlite3
```

## 로컬 실행

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

확인:

```bash
http://127.0.0.1:8000/health
```

## Render 배포

이 저장소를 Render Web Service로 연결하면 됩니다.

환경변수:

```env
DATABASE_PATH=/var/data/lecture_actions.sqlite3
ACTION_API_KEY=긴_랜덤_비밀키
```

`render.yaml`에는 persistent disk 설정이 포함되어 있습니다.

## GPT Actions

GPT Builder의 Actions에는 `docs/actions/openapi.yaml` 내용을 넣습니다.

Schema 안의 server URL은 Render 배포 주소로 바꿔야 합니다.

```yaml
servers:
  - url: https://YOUR-RENDER-SERVICE.onrender.com
```

## 주요 endpoint

- `POST /projects`
- `POST /projects/{project_id}/outline`
- `GET /projects/{project_id}/next`
- `POST /projects/{project_id}/sections`
- `POST /projects/{project_id}/image-items`
- `POST /projects/{project_id}/textbook-items`
- `POST /projects/{project_id}/exam-items`
- `POST /projects/{project_id}/check-items`
- `POST /projects/{project_id}/formula-items`
- `POST /projects/{project_id}/design-items`
- `GET /projects/{project_id}/final-bundle`
