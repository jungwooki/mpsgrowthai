# AWS 운영 배포 — 2026-09-26

- URL: https://z3mvzwqkz5y6thouemc6p6vgd40ocomx.lambda-url.ap-southeast-2.on.aws/
- 프로젝트: 616714047727, 리전: ap-southeast-2.
- Lambda: growthai, Python 3.12 / x86_64, 2048MB, 300초.
- 역할: growthai-lambda-runtime. exams/* 및 budget/* 읽기·쓰기,
  references/*와 runtime/growthai-config.json 읽기만 허용. 로그는 앱 로그 그룹에 한정.
- 로그 그룹: /aws/lambda/growthai, 보존 14일.
- 버킷: growthai-media-616714047727-aps2. 퍼블릭 접근 차단 유지.
- 배포 ZIP: deployments/growthai-20260926.zip. 최신 2열 화면과 근거 원본 11개 포함.
- 비밀 설정: runtime/growthai-config.json, SSE-S3 AES256 암호화 확인.
  Lambda 시작 시 실행 역할로 읽으며 허용한 5개 설정만 로드. 값은 문서·ZIP·로그에 포함하지 않음.
  변경 후 실행 환경을 재생성해야 적용됨. 예: Lambda 구성 갱신.
- 환경 설정: 비공개 직접 업로드 및 S3 월간 비용 원장 활성화,
  기본 예산 50,000원, 서버·저장소 월 예비비 10,000원.
- Function URL은 사용자 명시 승인으로 공개. 로그인·자료·센터/MPS Basecamp 권한은 앱에서 검증.
  공개 첫 화면 외 인증 없는 /api/status는 401 확인.
- /healthz 200, 첫 화면 200 확인.
- 로컬 Python 기존 92개와 런타임 설정 장애/허용키 검증 2개, JS 5개 통과.

## 남은 확인

- references/ 원본 연결은 아래 후속 작업에서 완료. 세 계정 실제 로그인·업로드 검증은 미실시.
- 실제 AI 요청 성공은 아래 가상자료 시험에서 확인. 운영 과금 집계와 임상 정확도는 별도 검증 필요.
- 기존 Vercel 사이트와 HAEON EMR 입구는 이 배포로 변경하지 않음.
- AWS 요금제 및 고급 기능 변경 없음. 월 5만 원은 추정 예산이지 청구 상한이 아님.

## 비용 저장소 최초 연결 오류 수정

- 신규 월 원장이 아직 없을 때, 실행 역할에 ListBucket이 없어 GetObject가
  NoSuchKey(404) 대신 AccessDenied(403)를 반환했다.
- growthai-runtime-scoped 역할 정책에 해당 버킷 한정 s3:ListBucket 추가.
  객체 내용 읽기/쓰기 범위는 기존대로 유지.
- 같은 실행 역할의 임시 비공개 Lambda로 실제 검증:
  없는 원장 NoSuchKey 응답, 조건부 PutObject, GetObject 읽기 모두 성공.
- 시험용 객체와 임시 Lambda는 검증 후 제거. 실제 월 원장 및 사용 기록은 변경하지 않음.
- IAM SimulatePrincipalPolicy는 조직 정책 판정 explicitDeny를 반환했으나,
  실제 동일 실행 역할의 S3 호출은 성공했다. 운영 검증 결과를 기준으로 기록함.
- 앱 로그인 후 화면 검증은 별도 승인 대기 상태로 유지.

## GPT-4.1 30,000 TPM 대응 배포

- 배포 객체: deployments/growthai-20260926-staged.zip.
- 배포 SHA256(base64): 9uv6AEGVQyap8UBIRR24R605VmhqWJHcFCaJxidsFuk=.
- 현재 검사 사진 관찰과 참고영상 기반 종합 비교를 분리. 모든 현재 사진은
  첫 호출에서 high detail로 관찰하며 성별에 맞는 전체 연령 참고영상은
  두 번째 호출에 유지한다. 단계 사이 61초 대기.
- 종합 호출은 현재 사진 대신 파일별 관찰 기록을 받는다. 이 제한을 보고서에 표시.
  관찰 ID/부위 누락·중복·불일치는 종합 전에 차단한다.
- 검색 텍스트는 발췌 여부를 표시해 제한하고 필수 단계 정의 원문과 모든 참고영상 유지.
- 요청량 초과 한 건을 같은 크기로 재시도하지 않는다. 일시적 429만 61초 후 한 번 재시도.
  명시적 429/크레딧 거절은 원장에 rejected로 기록하고 해당 예비금을 해제한다.
  시간초과·알 수 없는 실패는 예비금을 유지한다. 과거 미확정 기록은 변경하지 않았다.
- Python 98개, JavaScript 5개 통과. 추가 제한시간 변경 후 관련 테스트 2개 재통과.
- 실제 OpenAI API 가상 시험: 환자자료 없는 가상 이미지 12장 + 참고영상 18장,
  2회 호출, 약 88.82초, 입력 토큰 합계 32,668 / 출력 4,134. 두 요청 모두 성공.
  가상 이미지 12개를 unusable로 분류하고 골연령 추정은 보류함.
  이 로컬 시험 비용은 운영 원장 집계 밖이며 임상 정확도를 검증한 것은 아님.
- Lambda Active / LastUpdateStatus Successful 및 로컬/운영 ZIP 해시 일치 확인.

## MPS 단계·융합 평가·자료실 연결

- 배포 객체: deployments/growthai-20260926-mps-stage.zip.
- SHA256(base64): lRuYs9QmLLHkrwUQ82a8Cdiosce2Mrxjiumg5QDwcfM=.
- Lambda Active / Successful, 배포 해시 일치 확인.
- 사용자 정의 Stage 0–4를 프롬프트·검증·화면에 연결. 세부 근거 부족은 판단 보류.
- 9번은 3개월 추적·단계별 운동과 회복·체성분 및 영양의 세 문단 MPS 관리 제안.
  정상 체지방이나 근육 증가 등 확인되지 않은 판단을 생성하지 않는다.
- references/ 원본 11개 업로드 완료. 서명 다운로드 11개 모두 로컬 SHA256와 일치,
  익명 접근 403 확인. 앱 경로는 권한 확인 후 5분 서명 URL을 발급한다.
- Python 116개 통과. 브라우저 데스크톱·모바일 가로 넘침 없음,
  단계 5개 및 관리 제안 3문단 렌더링 확인, 페이지 오류 없음.
- 변경된 프롬프트 실제 API 가상 시험: 12장+참고영상18장, 2회 호출,
  89.38초, 입력32,934 / 출력3,911. 가상 영상은 판독 불가, 골연령 판단 보류.
  실제 환자·로그인 운영 흐름 또는 임상 정확도를 검증한 시험은 아님.

## Vercel 원본 누락 재발 — 2026-09-26 로컬 수정, 미배포

- 신고 주소: https://growthai-two.vercel.app/workspace. AWS Function URL과 별도 배포다.
- Git에서 제외된 data/sources 원본은 GitHub 배포에 포함되지 않는다. 기존 status/library/AI 렌더러는 로컬 파일만 확인해 S3 원본을 이용하지 못했다.
- 로컬 수정: status/library는 로컬 파일이 없을 때 인증된 S3 HEAD와 크기로 연결을 확인한다. AI는 필요한 원본만 요청별 인증으로 내려받고 매니페스트 SHA256 검증 후 임시 캐시에 원자적으로 저장한다. 자료실은 로컬 파일 없이도 인증 확인 후 5분 서명 URL을 발급한다.
- 실제 S3 자격 증명/권한이 없는 배포는 계속 unavailable로 표시한다. 이 변경만으로 Vercel의 미완료 OIDC 연결이 해결되는 것은 아니다.
- 비공개 ZIP artifacts/mps-growth-web.zip에 원본 11개와 수정 코드를 포함했다. 원본 해시 검증, 비밀값 제외, ZIP 내부 .gitignore의 원본 제외 설정을 적용했다. S3 연결이 없는 Vercel은 이 로컬 비공개 원본을 포함하여 재배포해야 한다. 원본을 Git에 추가하지 않는다.
- 검증: 기존+신규 테스트 전체 120개 통과 후, 추가한 인증 실패 및 AI 경로 시험을 포함해 관련 12개 통과. 실제 유료 AI 요청은 하지 않았다.
- 운영 미반영: Vercel 앱이 haeons-projects 팀 접근을 403으로 거부하며 재인증을 요구한다. AWS 앱도 재인증 필요, 로컬 growthai 프로필 없음. 운영 환경변수/배포를 변경하지 않았다.

## Vercel 운영 반영 — 2026-09-27

- 재인증 후 growthai 프로젝트/배포 조회 성공. 플러그인 deploy_to_vercel은 Tool not found여서 별도로 승인받은 Vercel CLI 60.1.3 로그인으로 배포했다.
- 배포 ID: dpl_7RepUr9vn5zMqdwKAi8Gvrf3WXGL, 상태 READY / production.
- 운영 주소: https://growthai-two.vercel.app, 배포 주소: https://growthai-5rudld8td-haeons-projects.vercel.app.
- 로컬 비공개 data/sources 11개와 수정된 reference_storage 모듈을 배포 API 파일 목록에서 확인했다. /healthz HTTP 200 확인.
- Vercel 운영 환경변수에는 S3 설정이 없다. 현재 배포는 포함된 원본을 사용한다. S3 연결 완료 전에는 GitHub 소스만 재배포하면 원본이 다시 누락될 수 있으므로, 원본 11개를 갖춘 로컬에서 `npx vercel deploy --prod --yes`로 배포해야 한다.
- CLI로 가져온 환경변수로 검증용 앱 로그인은 401이었다. 실제 사용자 비밀번호를 변경하지 않았으며, 로그인 후 status/AI 요청은 확인하지 못했다. 유료 AI 요청 없음. 사용자 로그인 세션에서 새로고침 확인 필요.

## Git 자동 배포에 의한 재발 차단 — 2026-09-27

- 첫 복구 배포 dpl_7RepUr9vn5zMqdwKAi8Gvrf3WXGL 직후 GitHub main eac69af 자동 배포 dpl_2zzDaupphbCFzwKs5nZBxAmcgPki가 운영 별칭을 교체했다. 오류 요청 로그는 이 원본 없는 배포를 가리킨다.
- 원본을 포함해 재배포한 dpl_BefJ61BBtt9JZe99ejg6sa1RRXwY의 실제 운영 self-check 로그에서 남아 18장/여아 15장 참고영상 렌더링 성공을 확인했다. 유료 AI 요청·환자 자료 재전송 없이 검증했다.
- scripts/check_references.cjs는 원본 11개의 길이와 SHA256을 확인하고, 누락/불일치이면 Vercel ignore step의 종료 코드 0으로 새 배포를 건너뛴다. 모두 일치하면 종료 코드 1로 빌드를 진행한다.
- vercel.json ignoreCommand와 Vercel 프로젝트 commandForIgnoringBuildStep에 같은 검사를 적용했다. 검사 스크립트가 없는 과거 Git 커밋도 배포를 건너뛰므로 정상 운영본을 덮어쓰지 않는다. 서버 설정 저장 응답 일치 확인.
- 최종 배포: dpl_N7hyuNChCmaGaUS8FMJBokUUsS6P (https://growthai-94fvo0xca-haeons-projects.vercel.app).
- REFERENCE_SELF_CHECK=1은 서버 시작 시 공개 참고자료만 변환하고 성별/이미지 수 또는 오류 형식을 기록한다. 환자·API 데이터는 기록하지 않는다.
- 123개 테스트 통과. 원본 누락/변조/검사 스크립트 누락 때 배포 건너뛰기, 정상 원본일 때 빌드 진행 검증 포함.
- Vercel 비용 저장소는 여전히 미연결이다. AWS 앱 재인증이 필요하며 현재 AWS 접근을 확인하지 못했다. 비용 경고를 숨기거나 사용량을 0원으로 처리하지 않았다.

## AI HTTP 404: 빈 모델 설정 수정 — 2026-09-27

- 운영 모델 진단에서 configured 조회 URL이 /v1/models/였고 307 응답, 같은 키의 /v1/models/gpt-4.1은 200이었다. OPENAI_MODEL은 존재하지만 빈 문자열이었다. os.getenv(key, default)는 빈 문자열에 기본값을 적용하지 않아 Responses 요청에 빈 모델을 보냈다.
- Vercel OPENAI_MODEL을 gpt-4.1로 갱신했다. CLI는 공유 변수의 대상인 Production/Preview 양쪽 갱신을 보고했다. API 키·로그인 비밀번호는 변경하지 않았다.
- backend/ai_config.py의 model_name()으로 status, 결과지 전사, 관찰, 종합, 보고서 모델명을 통일했다. 미설정/빈 문자열/공백은 gpt-4.1, 명시 모델은 앞뒤 공백만 제거해 유지한다.
- 404 model_not_found는 모델 설정/프로젝트 접근 권한 안내로 구분한다. 공급자 원문·비밀값은 사용자 오류 메시지에 포함하지 않는다.
- 전체 129개 테스트 통과. 비공개 원본 포함 배포 ZIP 갱신.
- 수정 배포: dpl_CnsTr9N4fE3FUwodd7Z1SimLncJM / https://growthai-4hqa0qen5-haeons-projects.vercel.app.
- AI_MODEL_SELF_CHECK=1은 모델 메타데이터 GET만 수행한다. 환자 자료 전송이나 유료 생성 요청은 수행하지 않았다.
