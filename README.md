# Clean FastAPI

Clean Architecture 기반의 FastAPI 애플리케이션

## 아키텍처

### 레이어드 아키텍처 (Controller → Service → Repository → DB)

```
1. Controller Layer
   ↓  HTTP 요청/응답 처리 (Request/Response DTO)
2. Service Layer
   ↓  비즈니스 로직 실행 (Command/Query 처리)
3. Repository Layer
   ↓  데이터 접근 (ORM, SQL, 외부 API 호출)
   ↓  Domain Model(Entity) ↔ DB 변환
4. Database (Persistence)
```

**계층별 역할**

* **Controller Layer**: HTTP 요청/응답 처리, 유효성 검증
* **Service Layer**: 비즈니스 로직, 트랜잭션 관리
* **Repository Layer**: 데이터 접근, SQL/ORM 쿼리 실행
* **Database**: 실제 데이터 저장소

---

## 프로젝트 구조

```
app/
├── interfaces/          # 프레젠테이션 계층
│   ├── controllers/     # API 엔드포인트
│   └── schemas/         # Request/Response 모델
├── application/         # 애플리케이션 계층
│   ├── services/        # 비즈니스 로직
│   ├── commands/        # CQRS Commands
│   ├── queries/         # CQRS Queries
│   └── unit_of_work.py  # UoW 인터페이스
├── domain/              # 도메인 계층
│   ├── entities/        # 도메인 엔티티
│   └── repositories/    # 레포지토리 프로토콜
├── infra/               # 인프라 계층
│   ├── repositories/    # 레포지토리 구현체
│   ├── models/          # DB 모델
│   └── unit_of_work.py  # UoW 구현체
└── container/           # DI 컨테이너
```

---

## 주요 구현

### Auth

* 클래스 기반 컨트롤러 (`AuthController`)
* JWT 기반 인증

### Note

* 클래스 기반 컨트롤러 (`NoteController`)
* CQRS 패턴 적용 (Commands/Queries 분리)
* 태그 시스템 (Many-to-Many)
* 커서 기반 페이지네이션 지원

### User

* 함수형 라우터 방식
* dict 기반 업데이트 (`changes` 딕셔너리)
* 역할 기반 접근 제어 (USER/ADMIN)

---

## 아키텍처 패턴

### Repository Pattern

```python
# 도메인 계층 - 인터페이스 정의
class NoteRepository(Protocol):
    async def get_notes(self, user_id: str, limit: int) -> list[Note]: ...
    async def save(self, user_id: str, note: Note) -> Note: ...
```

### Unit of Work (UoW)

* 트랜잭션 관리
* 컨텍스트 매니저 기반 자동 커밋/롤백
* Repository 패턴으로 데이터 접근 추상화

### 의존성 주입 (DI)

* `dependency-injector` 기반 DI 컨테이너
* Factory 패턴으로 객체 생성
* 애플리케이션 시작/종료 시 리소스 초기화 및 정리

---

## 기술 스택

* FastAPI + SQLAlchemy (Async)
* PostgreSQL
* Alembic (마이그레이션)
* JWT 인증
* dependency-injector (DI 컨테이너)