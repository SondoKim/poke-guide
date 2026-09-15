"""데이터 수집 스크립트 — data/ 폴더에 원본 데이터를 저장한다.

  python fetch_data.py          # 전부 새로 받기
  python fetch_data.py --skip-dittobase   # 레이드 순위(느림)는 건너뛰기

출처
  - PvPoke gamemaster / 랭킹 : github.com/pvpoke/pvpoke (pvpoke.com이 사내망에서 막혀 있어 GitHub 미러 사용)
  - 한국어 이름               : github.com/PokeAPI/pokeapi CSV (local_language_id=3)
  - 타입별 레이드 딜러 순위   : dittobase.com/pokemon-go/best-attackers/<type> (서버 렌더링된 상위 50위)
"""
import json
import os
import re
import sys
import time
import urllib.request

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
UA = {"User-Agent": "Mozilla/5.0 (poke-guide build script)"}

PVPOKE_RAW = "https://raw.githubusercontent.com/pvpoke/pvpoke/master/src/data/"
POKEAPI_RAW = "https://raw.githubusercontent.com/PokeAPI/pokeapi/master/data/v2/csv/"
DITTO = "https://www.dittobase.com/pokemon-go/best-attackers/"
TYPES = ["bug", "dark", "dragon", "electric", "fairy", "fighting", "fire", "flying", "ghost",
         "grass", "ground", "ice", "normal", "poison", "psychic", "rock", "steel", "water"]


def get(url, retries=3):
    for i in range(retries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            if i == retries - 1:
                raise
            print(f"  retry {i + 1}: {e}")
            time.sleep(2)


def save(name, data: bytes):
    os.makedirs(DATA, exist_ok=True)
    path = os.path.join(DATA, name)
    with open(path, "wb") as f:
        f.write(data)
    print(f"  saved {name} ({len(data):,} bytes)")


def fetch_pvpoke():
    print("[PvPoke]")
    save("gamemaster.json", get(PVPOKE_RAW + "gamemaster.json"))
    for cp in (1500, 2500, 10000):
        save(f"rankings-{cp}.json", get(f"{PVPOKE_RAW}rankings/all/overall/rankings-{cp}.json"))


def fetch_pokeapi():
    print("[PokeAPI 한국어 이름]")
    for name in ("pokemon_species_names.csv", "moves.csv", "move_names.csv"):
        save(name, get(POKEAPI_RAW + name))


def parse_dittobase(html: str):
    """Next.js RSC 페이로드에 박혀 있는 initialResults(상위 50) 배열을 꺼낸다."""
    chunks = re.findall(r'self\.__next_f\.push\(\[1,"((?:[^"\\]|\\.)*)"\]\)', html)
    payload = "".join(json.loads('"' + c + '"') for c in chunks)
    i = payload.find('"initialResults":[')
    if i < 0:
        raise RuntimeError("initialResults not found")
    arr, _ = json.JSONDecoder().raw_decode(payload[i + len('"initialResults":'):])
    m = re.search(r'"updatedAt":"([^"]+)"', payload)
    return {"updatedAt": m.group(1) if m else None, "results": arr}


def fetch_dittobase():
    print("[Dittobase 타입별 레이드 순위]")
    out = {}
    for t in TYPES:
        html = get(DITTO + t).decode("utf-8")
        out[t] = parse_dittobase(html)
        print(f"  {t:9s} {len(out[t]['results'])}개  (updated {out[t]['updatedAt']})")
        time.sleep(0.5)
    save("dittobase.json", json.dumps(out, ensure_ascii=False).encode("utf-8"))


if __name__ == "__main__":
    fetch_pvpoke()
    fetch_pokeapi()
    if "--skip-dittobase" not in sys.argv:
        fetch_dittobase()
    with open(os.path.join(DATA, "fetched_at.txt"), "w") as f:
        f.write(time.strftime("%Y-%m-%d %H:%M"))
    print("done")
