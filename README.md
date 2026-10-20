[![🔗 대시보드 바로가기](site/assets/dashboard-badge.svg)](https://HSC-Class01.github.io/SI-alteogen/)

# ALTEOGEN · DART Financial Observatory

**대시보드:** https://HSC-Class01.github.io/SI-alteogen/  
GitHub Pages 자동 배포를 구성했습니다. 2026-10-20 최초 갱신에서 DART 보고서 원문 54건과 재무 데이터 86개 기간/기준을 수집했습니다. API 키는 GitHub Actions Secret에만 저장하며 저장소 코드에는 포함하지 않습니다.

## 시작하기: GitHub 웹 화면 기준

1. ZIP을 해제하고 **내용물**을 `HSC-Class01/SI-alteogen` 저장소 루트에 업로드합니다. `README.md`, `agent.py`, `build_site.py`, `config`, `automation`, `site`, `data`, `requirements.txt`가 루트에 있어야 합니다. `.github` 같은 숨김 경로는 ZIP에 포함하지 않습니다.
2. 저장소에는 `.github/workflows/monthly-update.yml`을 이미 추가했습니다. ZIP에도 같은 워크플로우 원본이 `automation/monthly-update.yml`로 포함됩니다. 기존 파일을 교체하거나 다른 저장소에 설치할 때 GitHub에서 **Add file → Create new file**로 `.github/workflows/monthly-update.yml`을 만든 뒤 원본 내용을 붙여넣으세요.
3. Open DART에서 회원가입 후 API 인증키를 신청합니다. 키는 40자리입니다. **소스 코드에 키를 붙여넣지 마세요.** 저장소 **Settings → Secrets and variables → Actions → New repository secret**에서 이름을 `DART_API_KEY`, 값에 인증키를 입력합니다. 이 키를 Issues/README/공개 대화에 올리지 마세요.
4. **Settings → Pages → Build and deployment → Source: GitHub Actions**를 선택합니다. Pages 메뉴가 없다면 계정 요금제/저장소 공개 범위/조직 정책을 확인하세요.
5. **Settings → Actions → General**에서 Actions 사용을 허용합니다. workflow job은 데이터 커밋을 위해 `contents: write`를 요청합니다. 조직 정책이나 기본 브랜치 보호규칙으로 봇 push가 금지되어 있으면 관리자에게 봇 쓰기 권한을 허용받아야 합니다. `main` 이름을 코드에 하드코딩하지 않고 기본 브랜치 checkout을 사용합니다.
6. **Actions → DART monthly update and Pages → Run workflow**에서 기본 브랜치를 선택하고 최초에는 `full_refresh=true`로 실행하세요. workflow 파일은 이번 변경에서 저장소에 추가했습니다. 초회 실행은 전체 원문·API 수집으로 오래 걸릴 수 있습니다. 성공하면 `data`와 `site/index.html`이 커밋되고 Pages가 배포됩니다. 실패하면 기존 배포 화면은 유지됩니다.
7. 저장소 오른쪽 **About** Website에 `https://HSC-Class01.github.io/SI-alteogen/`를 설정했습니다. README 최상단 배지는 이미 같은 주소를 가리킵니다. 사용자 첨부 배지 이미지를 받지 못해 기본 SVG 배지를 제공했습니다. 원하는 이미지로 `site/assets/dashboard-badge.svg`와 README 이미지 경로를 교체할 수 있습니다.

## 자동 갱신

- cron `15 0 1 * *`: **매월 1일 09:15 KST** (UTC 00:15). GitHub 예약 실행은 지연될 수 있어 정확한 실행 시각을 보장하지 않습니다.
- 기본 브랜치에 워크플로우가 있어야 예약 실행됩니다. 공개 저장소에 장기간 활동이 없으면 GitHub가 예약 실행을 비활성화할 수 있으므로 Actions 알림을 켜고 월별 성공 여부를 점검하세요.
- 2010-01-01 이후 전체 접수 이력을 매번 다시 조회하여 오래된 사업연도의 신규 정정도 감지합니다. 페이지네이션 포함, 원본·정정본을 모두 보존합니다.
- 기존 원문 ZIP은 재다운로드하지 않습니다. 신규 보고서/정정본이 가리키는 사업연도와 최근 3개 사업연도를 API로 재조회합니다. `full_refresh=true`는 2015년 이후 전체 API 자료를 재조회합니다.
- 013/014는 미제공으로 기록. 인증키/접근 IP/호출한도 오류는 성공으로 숨기지 않고 실행을 실패시킵니다. 네트워크·서버 점검은 제한된 재시도 후 실패합니다. API URL에는 키가 들어가므로 코드가 요청 URL/키를 로그에 출력하지 않습니다.
- 데이터 수집 단계가 실패하면 커밋/배포 단계는 실행하지 않습니다. 동시 실행은 순차 처리하여 push 경합을 줄입니다.

## 데이터 범위와 반드시 알아야 할 제한

**2010년부터 원문 수집을 시도하지만, 공시가 없는 연도의 보고서를 생성할 수 없습니다.** 상장 전 또는 미공시 기간에는 보고서가 없을 수 있습니다. 현금흐름·매출은 공시 숫자이고 기술이전 최대 계약액이나 미수령 마일스톤은 매출로 간주하지 않습니다.

Open DART 전체 재무제표 API는 **2015년부터** 제공합니다. 따라서 **2010~2014의 모든 재무수치를 자동 추출하는 완성본은 아닙니다.** 해당 기간은 원문 ZIP을 보존하고 `data/manual/verified.csv`를 통해 검증된 수치만 반영합니다. 불규칙한 옛 보고서 표에서 근거 없이 숫자를 자동 선택하지 않습니다. 과거 자동 추출을 확장하려면 실제 보고서 표본과 검증용 정답 수치가 필요합니다.

`verified.csv` 열: `year,code,basis,metric,amount_krw,rcept_no,verified,note`.
- code: 사업 11011 / 반기 11012 / Q1 11013 / Q3 11014.
- basis: CFS(연결) 또는 OFS(별도). metric은 `config/metrics.json`의 키.
- 금액은 원화 **원** 단위. 반기·분기 손익은 누적 값, 재무상태는 기말, CF는 누적.
- 원문을 확인한 후 접수번호(14자리), `verified=true`, 주석에 문서/표 위치를 적습니다.
- 검증되지 않은 행은 반영하지 않습니다. 2015년 이후는 API 기반으로 처리합니다.
- 과거 CSV는 자동 정정되지 않습니다. 과거 정정 원문이 발견되면 사람이 재검증해야 합니다.

현재 첨부 재무항목 파일을 받지 못하여 다음 표준항목을 채택했습니다. 사용자 지정 항목은 `config/metrics.json`의 계정 ID/정확한 계정명으로 확장할 수 있습니다. R&D, 로열티, 계약잔액 등 주석 항목은 이 전체재무제표 API로 항상 얻을 수 없으며 이번 버전에서는 추정하지 않습니다.

| 구분 | 항목 |
|---|---|
| 손익 | 매출액, 영업이익, 전체 당기순이익 |
| 재무상태 | 자산, 부채, 자본, 유동자산, 유동부채, 현금및현금성자산 |
| 현금흐름 | 영업·투자·재무활동 현금흐름 |
| 비율 | 영업이익률, 순이익률, 부채비율, 유동비율, 자기자본비율, 기간 ROE·ROA, 동일기간 매출 YoY |

## 비교 기간·계산 정의

- annual=12개월 누적, Half-year=6개월 누적, quarterly=Q1(3개월 누적)/Q3(9개월 누적). 반기 보고서의 3개월 손익은 별도 열로 제공합니다. Q2/Q4를 독립 공시로 생성하지 않습니다.
- `thstrm_add_amount`가 분/반기 손익의 누적값이고 `thstrm_amount`는 3개월 값입니다. Q1을 제외하고 누적값이 빠졌을 때 3개월 값을 누적값으로 대체하지 않습니다.
- 연결/별도는 모두 보존하며 대시보드에서 선택합니다. 비율 계산에 두 기준을 섞지 않습니다.
- ROE·ROA=전체 순이익/(전년 연말+현 기간 말 자본·자산 평균). 기간 기준이며 연율화하지 않음. 평균 계산에 필요한 전년 말이 없으면 결측.
- 분모가 0/음수이면 해당 비율은 결측. 전년 매출이 양수인 경우에만 YoY 산출. 결측을 0으로 채우지 않음.
- 표의 단위는 억원, CSV는 KRW 원. 계정별 원 응답/추출 근거는 `data/raw`, `data/financials.json`의 provenance에 저장됩니다. 모호한 매핑·비원화 통화는 경고와 결측으로 처리합니다.

## 폴더 구조

```
agent.py                     수집, 증분 갱신, 계정 정규화, 비율 계산
build_site.py                데이터 내장 HTML 생성
config/metrics.json         표준 계정 매핑
config/peers.json            비교기업과 선정 근거
automation/monthly-update.yml  업로드 가능한 워크플로우 원본
automation/install_workflow.py 로컬에서 필수 경로 생성(선택)
data/reports/               보고서 원문 ZIP·접수 목록
data/raw/                   API 응답 JSON
data/manual/verified.csv    검증된 2010~2014 수치 입력
data/financials.json         정규화 수치·계정 근거·비율
data/coverage.json          미제공 기간 목록
data/status.json            최종 성공 갱신 상태
site/index.html             단일 HTML 대시보드
site/assets/                README 배지
site/template.html          대시보드 소스 템플릿
tests/                      계산·단위·결측·모호한 매핑 테스트
```

Pages에는 `site`만 업로드하므로 API 원응답/보고서 원문은 Pages 산출물에 포함되지 않습니다. 공개 GitHub 저장소에 커밋된 공시 파일은 공개됩니다. ZIP 원문이 GitHub의 파일 크기 제한(개별 100MB 등)을 넘으면 push 실패할 수 있으며 그 경우 별도 저장소/LFS/외부 원문 저장 정책을 추가해야 합니다.

## 로컬 실행 (선택)

Python 3.11 이상. API 키를 환경변수에 넣되 명령 기록에 민감정보가 남지 않도록 주의하세요.

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python agent.py --full
python build_site.py
python automation/install_workflow.py
```

키는 `DART_API_KEY` 환경변수에서 읽습니다. 생성된 `.github/workflows/monthly-update.yml`을 커밋해야 GitHub가 실행합니다. 로컬 `site/index.html`은 더블클릭으로 열 수 있습니다. 데이터는 내장되어 있고 차트만 Chart.js CDN 연결을 사용합니다. CDN 실패 시에도 표와 결측 안내는 표시됩니다.

## 오류 점검

| 증상 | 확인/조치 |
|---|---|
| Actions에 워크플로우 없음 | `.github/workflows/monthly-update.yml` 경로·기본 브랜치·YAML 복사 여부 |
| DART_API_KEY 40자리 오류 | Actions secret 이름/값, 인증키 발급 상태 |
| DART 010/011/901 | 인증키 무효/중지/보유기간 만료 확인 |
| DART 012 | 인증키의 접근 IP 제한 확인. GitHub hosted runner IP는 변할 수 있음 |
| DART 020 | 호출한도 확인; 불필요한 전체 재조회 줄이고 다음 한도 갱신 후 재시도 |
| git push 403 / 보호 브랜치 | Actions 쓰기 권한·조직 정책·봇 push 허용 여부 |
| Pages 404 / configure-pages 오류 | Pages Source를 GitHub Actions로 선택하고 최초 workflow 성공 확인 |
| deploy 승인 대기 | github-pages 환경 보호규칙/승인자 확인 |
| 표가 비어 있음 | 수집 성공 여부, CFS/OFS 선택, 해당 연도 공시/API 지원 범위 확인 |
| 스케줄이 실행되지 않음 | 기본 브랜치, Actions 활성화, 장기 비활동 자동 중지, GitHub 지연 확인 |

단위 테스트/정적 YAML 검사는 수행하지만 API 인증키를 제공받지 않아 실제 DART 인증 호출·GitHub push·Pages 배포의 종단간 검증은 수행하지 못했습니다. 저장소 정책을 포함한 모든 환경에서 오류가 없다고 보장할 수 없습니다.

## 출처

- [Open DART 전체 재무제표 API 및 2015년 제공 범위](https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS003&apiId=2019020)
- [공시검색 API: 정기보고서, 정정본, 페이지네이션](https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS001&apiId=2019001)
- [Open DART 인증키 신청](https://opendart.fss.or.kr/mng/userApiKeyListView.do)
- [플랫폼 바이오 비교기업 선정 참고: 비즈워치](https://news.bizwatch.co.kr/article/healthcare/2026/08/19/0044)

## 국내 Peer Firms

선정 기준일 2026-10-12. 플랫폼 기술이전 사업모델 기준의 비교군이며 동일한 SC 제형변경 기술의 직접 경쟁사라는 뜻이 아닙니다. Peer 수치 수집은 이 버전 범위에 포함하지 않습니다.

| 기업 | 종목코드 | 사업모델 | 비교 근거 | 주의사항 |
|---|---|---|---|---|
| 에이비엘바이오 | 298380 | 이중항체·BBB 셔틀 플랫폼 | 플랫폼 라이선스, 계약금·마일스톤 수익구조 | 기술군·임상단계가 다름 |
| 리가켐바이오 | 141080 | ADC 플랫폼·후보물질 | 플랫폼 확장성, 기술이전, R&D 투자 | 기술군이 다름; 최대 계약액은 매출/현금수령액과 다름 |
