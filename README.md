# 의성군 관광지 추천 시스템 (us-check)

Django와 Gemini AI를 활용한 의성군 관광지 추천 시스템입니다. 사용자의 자연어 쿼리를 분석하여 적절한 관광지를 추천하고, 파친코 게임 형태로 클라이언트에 제공합니다.

## 🏗️ 프로젝트 구조

```
us_check/
├── us_check/           # Django 프로젝트 설정
├── api/               # 통합 API 엔드포인트
├── tourism/           # 관광지 데이터 관리
├── gemini_ai/         # Gemini AI 서비스
├── qr_service/        # QR 코드 생성 및 관리
└── requirements.txt   # 패키지 의존성
```

## 🚀 주요 기능

### 1. 자연어 쿼리 처리
- 사용자의 자연어 입력을 Gemini AI로 분석
- 키워드, 카테고리, 사용자 의도 추출
- 의성군 관광지 특성에 맞춘 맞춤형 추천

### 2. Firestore 연동
- 의성군 관광지 76개 데이터를 Firestore에 저장
- 실시간 데이터 동기화
- 확장 가능한 NoSQL 데이터베이스 구조

### 3. QR 코드 생성
- 사용자 선택 결과를 QR 코드로 생성
- GCP Cloud Storage 연동
- 공유 가능한 URL 제공

### 4. 파친코 게임 지원
- 클라이언트 파친코 게임을 위한 JSON 데이터 제공
- 최대 20개 관광지 추천
- 실시간 선택 결과 처리

## 📋 API 엔드포인트

### 1. 쿼리 처리
```http
POST /api/query/
Content-Type: application/json

{
    "query": "자연 경관이 좋은 곳 추천해줘",
    "session_id": "optional_session_id",
    "user_id": "optional_user_id"
}
```

### 2. 최종 선택 처리
```http
POST /api/finalize/
Content-Type: application/json

{
    "selection_id": 123,
    "selected_spot_ids": [1, 3, 7, 12],
    "user_id": "optional_user_id"
}
```

### 3. 사용자 기록 조회
```http
GET /api/history/?user_id=1&limit=10
```

### 4. 모든 관광지 조회
```http
GET /api/spots/
```

### 5. Firestore 동기화
```http
POST /api/sync/
```

## 🛠️ 설치 및 실행

### 1. 환경 설정
```bash
# 가상환경 생성 및 활성화
python -m venv venv
venv\Scripts\activate  # Windows

# 패키지 설치
pip install -r requirements.txt
```

### 2. 환경변수 설정 (.env)
```env
SERVER_ADDRESS=localhost
CLIENT_ADDRESS=http://localhost:3000
GEMINI_API_KEY=your_gemini_api_key
GOOGLE_APPLICATION_CREDENTIALS=./your-service-account.json
FIRESTORE_PROJECT_ID=your-project-id
DEBUG=True
```

### 3. 데이터베이스 마이그레이션
```bash
cd server/us_check
python manage.py makemigrations
python manage.py migrate
```

### 4. 관광지 데이터 로드
```bash
# JSON 파일에서 로드
python manage.py load_tourism_data --json-file=tourism_data.json --upload-to-firestore

# 또는 Firestore에서 동기화
python manage.py load_tourism_data --sync-from-firestore
```

### 5. 서버 실행
```bash
python manage.py runserver
```