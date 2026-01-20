<div align="center">
  <img width="522" height="216" alt="image" src="https://github.com/user-attachments/assets/bd298391-3c38-4464-8e71-6fd3a7209136" />
  
  <h1>🌱 BOJ Jandi (백준 잔디)</h1>
  <p>
    <strong>백준 온라인 저지(BOJ)</strong>의 문제 해결 활동을 GitHub 잔디처럼 시각화해주는 서비스입니다.<br>
    별도의 API가 없는 BOJ 환경에 맞춰 <strong>실시간 스크래핑</strong>을 통해 데이터를 수집하고 시각화합니다.
  </p>
</div>

<br>

## ✨ 주요 기능

- **🔍 실시간 잔디 조회**: BOJ 핸들(아이디)을 입력하면 즉시 데이터를 수집하여 잔디 그래프를 그려줍니다.
- **⚡ 비동기 백그라운드 처리**: 스크래핑 작업을 백그라운드 큐로 처리하고, 프론트엔드에서 폴링(Polling) 방식으로 상태를 확인하여 타임아웃을 방지합니다.

<br>

## 🛠️ 기술 스택 (Tech Stack)

- **Backend**: FastAPI, Python 3.12+
- **Scraper**: Playwright (Headless Chromium)
- **Database**: PostgreSQL (Persisted via NFS)
- **Infrastructure**: Kubernetes, Docker, Traefik Ingress
- **Frontend**: HTML5, Vanilla JavaScript

<br>

## 🚀 시작하기 (Getting Started)

### 로컬 개발 (Local Development)

Docker만 있으면 로컬에서 즉시 실행할 수 있습니다.

```bash
# 레포지토리 클론
git clone https://github.com/shinkeonkim/boj-jandi-site.git
cd boj-jandi-site

# Docker Compose 실행 (이미지 빌드 및 서비스 시작)
docker-compose up -d --build

# 로그 확인
docker-compose logs -f web
```

브라우저에서 `http://localhost:8080`으로 접속하여 테스트할 수 있습니다.

<br>

## ☁️ 배포 (Deployment)

이 프로젝트는 Kubernetes 환경에 최적화되어 있습니다.

### Kubernetes 배포
`infra/` 디렉토리 내의 매니페스트를 사용하여 배포합니다.

- **Namespace**: `boj-jandi`
- **Domain**: `백준잔디.코드.kr` (xn--2z1bx8k47jumb.xn--hy1by51c.kr)
- **Ingress**: Traefik IngressRoute (TLS 적용)

### CI/CD
GitHub Actions를 통해 `main` 브랜치 푸시 시 자동으로 Docker 이미지가 빌드되어 Docker Hub에 업로드됩니다.
