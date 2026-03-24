# Scene Spark Suite 배포 가이드

## 프론트엔드 (GitHub Pages)
- 자동 배포 완료: https://jehun-hue.github.io/scene-spark-suite/

## 백엔드 (Railway)
1. https://railway.app 접속 → GitHub 로그인
2. "New Project" → "Deploy from GitHub repo" 선택
3. jehun-hue/scene-spark-suite 레포 선택
4. Settings → Environment Variables에 추가:
   - GEMINI_API_KEY = (AI Studio에서 발급받은 키)
5. Settings → Networking → Generate Domain 클릭
6. 생성된 도메인 (예: scene-spark-xxx.up.railway.app) 복사

## 프론트엔드 API 주소 변경
- 백엔드 배포 후 src/services/api.ts의 API_BASE_URL을 Railway 도메인으로 변경
