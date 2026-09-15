# 포켓몬 GO 실전 개체 분류 가이드 (PKGO IVGD)

블룸버그 터미널 스타일의 포켓몬 GO 개체 분류 가이드. **전 종(계보 단위) 자동 생성** + 수작업 메모.

- **라이브 페이지**: https://sondokim.github.io/poke-guide/
- 분류: 1) 레이드+배틀리그 겸용 / 2) 레이드 전용 / 3) 배틀리그 전용 / 4) 도감작 후 박사행
- 결과물은 `index.html` 하나 (외부 의존성 없음, `poke_guide.html`은 동일 복사본)

## 구조
| 파일 | 역할 |
|---|---|
| `fetch_data.py` | 데이터 수집 → `data/` (PvPoke gamemaster·랭킹, PokeAPI 한국어 이름, Dittobase 타입별 레이드 상위 50) |
| `build.py` | `data/` + `notes.json` + `template.html` → `index.html` 생성. 분류 기준은 상단 `THRESH` 상수 |
| `notes.json` | 수작업 메모. 키 = 계보 안 아무 포켓몬의 한국어 이름, `memo`(HTML 허용) / `tm`(기술머신 메모) |
| `template.html` | 페이지 뼈대(스타일·스크립트). `{{...}}` 자리에 빌드 결과가 들어감 |

## 갱신 방법
```bash
python fetch_data.py   # 최신 데이터 받기 (1~2분)
python build.py        # index.html 재생성
git add -A && git commit -m "update" && git push
```

## 분류 기준 (기본값)
- **BOTH**: 타입별 레이드 딜러 50위 이내 **그리고** GL/UL/ML 중 하나 100위 이내
- **RAID**: 레이드 50위 이내 (그림자·메가 포함)
- **PVP**: GL 200위 / UL 150위 / ML 100위 이내
- **XFER**: 나머지

## 출처
- 배틀리그 순위·기술: [PvPoke](https://pvpoke.com/rankings/) (GitHub 원본 JSON)
- 레이드 딜러 순위: [Dittobase Best Attackers](https://www.dittobase.com/pokemon-go/best-attackers/fire) 18타입 × 상위 50 (eDPS)
- 특별한 기술머신(★): PvPoke gamemaster `eliteMoves` + Dittobase `isElite`
- 한국어 이름: [PokeAPI](https://github.com/PokeAPI/pokeapi) CSV
