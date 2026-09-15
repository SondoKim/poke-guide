"""포켓몬 GO 실전 개체 분류 가이드 — 전 종 자동 생성기

  python fetch_data.py   # 데이터 갱신 (data/)
  python build.py        # index.html + poke_guide.html 생성

분류 기준(상수 THRESH)과 수작업 메모(notes.json)는 이 파일/데이터만 고치면 된다.
"""
import csv
import html
import json
import os
import re
import shutil
import time
from collections import defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")

# ── 분류 기준 ─────────────────────────────────────────────────────────────
THRESH = {
    "raid_top": 50,        # Dittobase 타입별 순위 (상위 50만 수집됨)
    "both_pvp": 100,       # BOTH: 레이드 top50 + 어느 리그든 이 순위 이내
    "pvp_gl": 200,         # PVP 전용: GL
    "pvp_ul": 150,         #           UL
    "pvp_ml": 100,         #           ML
}

TYPE_KO = {"bug": "벌레", "dark": "악", "dragon": "드래곤", "electric": "전기", "fairy": "페어리",
           "fighting": "격투", "fire": "불꽃", "flying": "비행", "ghost": "고스트", "grass": "풀",
           "ground": "땅", "ice": "얼음", "normal": "노말", "poison": "독", "psychic": "에스퍼",
           "rock": "바위", "steel": "강철", "water": "물"}
TYPE_AB = {"bug": "BUG", "dark": "DRK", "dragon": "DRG", "electric": "ELE", "fairy": "FAI",
           "fighting": "FGT", "fire": "FIR", "flying": "FLY", "ghost": "GHO", "grass": "GRS",
           "ground": "GRD", "ice": "ICE", "normal": "NOR", "poison": "PSN", "psychic": "PSY",
           "rock": "RCK", "steel": "STL", "water": "WTR"}

# speciesId 접미 토큰 → 한국어 폼 이름. (prefix, suffix)
FORM = {
    "alolan": ("알로라 ", ""), "galarian": ("가라르 ", ""), "hisuian": ("히스이 ", ""), "paldean": ("팔데아 ", ""),
    "mega": ("메가", ""), "mega_x": ("메가", " X"), "mega_y": ("메가", " Y"), "primal": ("원시", ""),
    "female": ("", " ♀"), "male": ("", " ♂"),
    "incarnate": ("", " 화신폼"), "therian": ("", " 영물폼"), "origin": ("", " 오리진폼"), "altered": ("", " 어나더폼"),
    "sky": ("", " 스카이폼"), "land": ("", " 랜드폼"), "attack": ("", " 어택폼"), "defense": ("", " 디펜스폼"),
    "speed": ("", " 스피드폼"), "complete": ("", " 퍼펙트폼"), "10": ("", " 10%폼"),
    "wash": ("", " 워시"), "heat": ("", " 히트"), "frost": ("", " 프로스트"), "fan": ("", " 스핀"), "mow": ("", " 커트"),
    "small": ("", " 스몰"), "average": ("", " 보통"), "large": ("", " 라지"), "super": ("", " 특대"),
    "low_key": ("", " 로우"), "amped": ("", " 하이"),
    "plant": ("", " 초목"), "sandy": ("", " 모래땅"), "trash": ("", " 쓰레기"),
    "sunny": ("", " 태양"), "rainy": ("", " 빗방울"), "snowy": ("", " 설경"), "overcast": ("", ""),
    "standard": ("", ""), "zen": ("", " 달마모드"), "galarian_zen": ("가라르 ", " 달마모드"),
    "baile": ("", " 이글이글"), "pom_pom": ("", " 파치파치"), "pau": ("", " 훌라훌라"), "sensu": ("", " 사뿐사뿐"),
    "midday": ("", " 한낮"), "midnight": ("", " 한밤중"), "dusk": ("", " 황혼"),
    "single_strike": ("", " 일격"), "rapid_strike": ("", " 연격"),
    "dawn_wings": ("", " 황혼의갈기"), "dusk_mane": ("", " 새벽의날개"),
    "black": ("", " 블랙"), "white": ("", " 화이트"), "unbound": ("", " 굴레를벗어난"), "confined": ("", ""),
    "blue_striped": ("", " 파란줄"), "red_striped": ("", " 빨간줄"), "white_striped": ("", " 하얀줄"),
    "resolute": ("", " 각오"), "ordinary": ("", ""), "crowned_sword": ("", " 검왕"), "crowned_shield": ("", " 방패왕"),
    "hero": ("", ""), "armored": ("", " 아머드"), "aqua": ("", " 아쿠아"), "blaze": ("", " 블레이즈"), "combat": ("", " 컴뱃"),
    "shadow": ("그림자 ", ""), "apex": ("", ""),
}
# 코스튬 등 실전 무관 폼 제외
EXCLUDE_TOKENS = {"libre", "pop_star", "rock_star", "5th_anniversary", "horizons", "kariyushi", "flying", "shaymin",
                  "costume", "fall", "winter", "spring", "summer"}
# 타입 폼(아르세우스·실버디 등)
TYPE_TOKENS = set(TYPE_KO)

MOVE_ID_OVERRIDE = {"SUPER_POWER": "superpower", "VICE_GRIP": "vise-grip", "NATURES_MADNESS": "nature-s-madness",
                    "FUTURE_SIGHT": "future-sight", "TECHNO_BLAST": "techno-blast", "SPACIAL_REND": "spacial-rend",
                    "ROAR_OF_TIME": "roar-of-time", "V_CREATE": "v-create", "LOCK_ON": "lock-on", "SHADOW_FORCE": "shadow-force",
                    "WEATHER_BALL": "weather-ball", "HIDDEN_POWER": "hidden-power", "AEGISLASH_CHARGE_PSYCHO_CUT": "psycho-cut",
                    "AEGISLASH_CHARGE_AIR_SLASH": "air-slash", "POWER_UP_PUNCH": "power-up-punch", "MUD_SLAP": "mud-slap",
                    "X_SCISSOR": "x-scissor", "U_TURN": "u-turn", "WILL_O_WISP": "will-o-wisp", "TRI_ATTACK": "tri-attack",
                    "SOLAR_BEAM": "solar-beam", "DOUBLE_KICK": "double-kick", "FEINT_ATTACK": "feint-attack",
                    "SELF_DESTRUCT": "self-destruct", "SUCKER_PUNCH": "sucker-punch", "DRAGON_TAIL": "dragon-tail",
                    "SAND_ATTACK": "sand-attack", "GRASS_KNOT": "grass-knot", "UPPER_HAND": "upper-hand",
                    "FUTURESIGHT": "future-sight", "NATURES_MADNESS": "natures-madness", "VICE_GRIP": "vice-grip", "AURA_WHEEL": "aura-wheel"}


# ── 데이터 로드 ───────────────────────────────────────────────────────────
def load():
    with open(os.path.join(DATA, "gamemaster.json"), encoding="utf-8") as f:
        gm = json.load(f)
    rank = {}
    for cp in (1500, 2500, 10000):
        with open(os.path.join(DATA, f"rankings-{cp}.json"), encoding="utf-8") as f:
            rank[cp] = {d["speciesId"]: (i + 1, d) for i, d in enumerate(json.load(f))}
    with open(os.path.join(DATA, "dittobase.json"), encoding="utf-8") as f:
        ditto = json.load(f)
    ko_species = {}
    with open(os.path.join(DATA, "pokemon_species_names.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["local_language_id"] == "3":
                ko_species[int(r["pokemon_species_id"])] = r["name"]
    move_ident = {}
    with open(os.path.join(DATA, "moves.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            move_ident[r["identifier"]] = int(r["id"])
    ko_move_by_id = {}
    with open(os.path.join(DATA, "move_names.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["local_language_id"] == "3":
                ko_move_by_id[int(r["move_id"])] = r["name"]
    ko_move = {ident: ko_move_by_id.get(mid, ident) for ident, mid in move_ident.items()}
    notes = {}
    p = os.path.join(ROOT, "notes.json")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            notes = json.load(f)
    fetched = ""
    p = os.path.join(DATA, "fetched_at.txt")
    if os.path.exists(p):
        fetched = open(p).read().strip()
    return gm, rank, ditto, ko_species, ko_move, notes, fetched


# ── 이름/기술 한국어화 ────────────────────────────────────────────────────
def tokens_of(species_id: str, base_name_tokens: int = 1):
    """speciesId에서 폼 토큰만 골라낸다. (ho_oh, mr_mime 같은 이름 내부 '_'는 무시)"""
    parts = species_id.split("_")
    toks = []
    i = 1
    while i < len(parts):
        two = "_".join(parts[i:i + 2])
        if two in FORM or two in EXCLUDE_TOKENS:
            toks.append(two)
            i += 2
            continue
        one = parts[i]
        if one in FORM or one in EXCLUDE_TOKENS or one in TYPE_TOKENS:
            toks.append(one)
        i += 1
    return toks


def ko_label(dex, species_id, ko_species, gm_name=""):
    base = ko_species.get(dex, gm_name or species_id)
    pre, suf = "", ""
    for t in tokens_of(species_id):
        if t in FORM:
            p, s = FORM[t]
            pre = p + pre if t in ("mega", "mega_x", "mega_y", "primal", "shadow") else pre + p
            suf += s
        elif t in TYPE_TOKENS:
            suf += f" ({TYPE_KO[t]})"
    if base[-1:] in "♀♂" and suf.strip() in ("♀", "♂"):
        suf = ""
    return f"{pre}{base}{suf}"


def ko_move_name(move_id: str, ko_move: dict) -> str:
    mid = move_id
    extra = ""
    for key in ("WEATHER_BALL", "HIDDEN_POWER", "TECHNO_BLAST", "AURA_WHEEL"):
        if mid.startswith(key + "_"):
            extra = f"({TYPE_KO.get(mid[len(key) + 1:].lower(), mid[len(key) + 1:])})"
            mid = key
    ident = MOVE_ID_OVERRIDE.get(mid, mid.lower().replace("_", "-"))
    name = ko_move.get(ident)
    if not name:
        name = mid.replace("_", " ").title()
    return name + extra


def slug_to_move_id(slug: str) -> str:
    """dittobase 'blast-burn' → 'BLAST_BURN', 'mystical-fire-plus' → ('MYSTICAL_FIRE', plus=True)"""
    plus = slug.endswith("-plus")
    if plus:
        slug = slug[:-5]
    return slug.upper().replace("-", "_"), plus


# ── 그룹(진화 계보) 구성 ────────────────────────────────────────────────
def build_groups(gm, ko_species):
    P = {p["speciesId"]: p for p in gm["pokemon"]}
    # family 정보가 없는 종(메가·일부 진화형)은 같은 도감번호 / 진화 목록을 통해 계보를 찾는다
    fam_by_dex, fam_by_evo = {}, {}
    for p in gm["pokemon"]:
        fam = (p.get("family") or {}).get("id")
        if fam:
            fam_by_dex.setdefault(p["dex"], fam)
            for e in (p["family"].get("evolutions") or []):
                fam_by_evo[e] = fam
    groups = defaultdict(list)
    for p in gm["pokemon"]:
        sid = p["speciesId"]
        if not p.get("released", True) or sid.endswith("_shadow") or "_shadow_" in sid:
            continue
        if any(t in EXCLUDE_TOKENS for t in tokens_of(sid)):
            continue
        fam = (p.get("family") or {}).get("id") or fam_by_evo.get(sid) or fam_by_dex.get(p["dex"])
        key = fam or f"DEX{p['dex']}"
        groups[key].append(p)
    out = []
    for key, members in groups.items():
        members.sort(key=lambda m: (m["dex"], len(m["speciesId"]), m["speciesId"]))
        for m in members:
            m["_label"] = ko_label(m["dex"], m["speciesId"], ko_species, m["speciesName"])
            m["_mega"] = "mega" in tokens_of(m["speciesId"]) or "mega_x" in tokens_of(m["speciesId"]) or "mega_y" in tokens_of(m["speciesId"]) or "primal" in tokens_of(m["speciesId"])
            m["_shadow_id"] = m["speciesId"] + "_shadow" if (m["speciesId"] + "_shadow") in P else None
            m["_final"] = not (m.get("family") or {}).get("evolutions")
        roots = [m for m in members if not (m.get("family") or {}).get("parent") and not m["_mega"]] or members
        base = next((m for m in roots if not tokens_of(m["speciesId"])), roots[0])
        out.append({"key": key, "members": members, "base": base, "dex": base["dex"],
                    "names": {m["_label"] for m in members} | {ko_species.get(m["dex"], "") for m in members}})
    out.sort(key=lambda g: g["dex"])
    return out, P


# ── PvP ──────────────────────────────────────────────────────────────────
def pvp_best(group, rank, P):
    """리그별 최고 순위 (그림자 포함). → {cp: {rank, sid, moveset, member}}"""
    res = {}
    for cp, table in rank.items():
        best = None
        for m in group["members"]:
            for sid in (m["speciesId"], m["_shadow_id"]):
                if sid and sid in table:
                    r, d = table[sid]
                    if best is None or r < best["rank"]:
                        best = {"rank": r, "sid": sid, "moveset": d.get("moveset", []), "member": m,
                                "shadow": sid.endswith("_shadow"), "score": d.get("rating")}
        if best:
            res[cp] = best
    return res


# ── 레이드 ────────────────────────────────────────────────────────────────
def raid_index(ditto):
    """dex → [ {type, rank, name, slug, shadow, mega, released, fast, charged, fast_elite, charged_elite, plus} ]"""
    idx = defaultdict(list)
    for t, blob in ditto.items():
        for i, row in enumerate(blob["results"]):
            pk, mv = row["pokemon"], row["bestMoveset"]
            m = re.search(r"/(\d+)-", pk.get("imageUrl", ""))
            if not m:
                continue
            fid, fplus = slug_to_move_id(mv["fastMove"]["slug"])
            cid, cplus = slug_to_move_id(mv["chargedMove"]["slug"])
            idx[int(m.group(1))].append({
                "type": t, "rank": i + 1, "name": pk["name"], "slug": pk["slug"], "shadow": pk["isShadow"],
                "mega": pk["isMega"], "released": pk["isReleased"], "edps": mv["edps"],
                "fast": fid, "charged": cid, "fast_elite": mv["fastMove"]["isElite"], "charged_elite": mv["chargedMove"]["isElite"],
                "plus": fplus or cplus,
            })
    return idx


def raid_label(entry, ko_species):
    sid = entry["slug"].replace("-", "_")
    dex = int(re.search(r"(\d+)", entry["slug"]).group(1)) if re.match(r"^\d", entry["slug"]) else None
    return ko_label(entry["_dex"], sid, ko_species, entry["name"])


# ── 렌더 유틸 ─────────────────────────────────────────────────────────────
def esc(s):
    return html.escape(str(s), quote=False)


def rk(rank, label="", small="", cls=None):
    if rank is None:
        return f'<span class="rk n">{esc(label)}—</span>'
    c = cls or ("g" if rank <= 50 else "a" if rank <= 200 else "r")
    lab = f"<small>{esc(label)}</small>" if label else ""
    sm = f" <small>{esc(small)}</small>" if small else ""
    return f'<span class="rk {c}">{lab}#{rank}{sm}</span>'


def mv_chip(move_id, member, P, ko_move, plus=False, elite=None):
    p = P.get(member["speciesId"], member)
    fast = move_id in p.get("fastMoves", [])
    if elite is None:
        elite = move_id in (p.get("eliteMoves") or [])
    cls = "mv " + ("f" if fast else "c") + (" e" if elite else "") + (" x" if plus else "")
    name = ko_move_name(move_id, ko_move) + ("+" if plus else "")
    return f'<span class="{cls}" title="{esc(move_id)}">{esc(name)}</span>', elite, fast


# ── 메인 ─────────────────────────────────────────────────────────────────
def main():
    gm, rank, ditto, ko_species, ko_move, notes, fetched = load()
    groups, P = build_groups(gm, ko_species)
    ridx = raid_index(ditto)
    ditto_updated = max((b.get("updatedAt") or "" for b in ditto.values()), default="")[:10]

    rows = {"both": [], "raid": [], "pvp": [], "xfer": []}
    stats = defaultdict(int)
    elite_needed_total = 0
    ticker_pool = []

    for g in groups:
        dexes = {m["dex"] for m in g["members"]}
        raid = sorted((dict(e, _dex=d) for d in dexes for e in ridx.get(d, [])), key=lambda e: e["rank"])
        raid_ok = [e for e in raid if e["rank"] <= THRESH["raid_top"]]
        pvp = pvp_best(g, rank, P)
        gl = pvp.get(1500, {}).get("rank"); ul = pvp.get(2500, {}).get("rank"); ml = pvp.get(10000, {}).get("rank")

        has_raid = bool(raid_ok)
        pvp_both = any(r is not None and r <= THRESH["both_pvp"] for r in (gl, ul, ml))
        pvp_only = (gl is not None and gl <= THRESH["pvp_gl"]) or (ul is not None and ul <= THRESH["pvp_ul"]) or (ml is not None and ml <= THRESH["pvp_ml"])
        if has_raid and pvp_both:
            sec = "both"
        elif has_raid:
            sec = "raid"
        elif pvp_only:
            sec = "pvp"
        else:
            sec = "xfer"

        base = g["base"]
        note = None
        for n in g["names"]:
            if n in notes:
                note = notes[n]
                break
        finals = [m for m in g["members"] if m["_final"] and not m["_mega"]]
        megas = [m for m in g["members"] if m["_mega"]]
        evo_names = [m["_label"] for m in finals if m is not base] or [m["_label"] for m in g["members"] if m is not base and not m["_mega"]]
        evo_txt = ("→ " + " / ".join(dict.fromkeys(evo_names))) if evo_names else "진화 없음"
        if megas:
            evo_txt += " · " + " / ".join(m["_label"] for m in megas)
        has_shadow = any(m["_shadow_id"] for m in g["members"])
        tags_gm = set()
        for m in g["members"]:
            tags_gm |= set(m.get("tags") or [])
        flags = []
        if megas: flags.append("mega")
        if has_shadow: flags.append("shadow")
        if "legendary" in tags_gm or "mythical" in tags_gm or "ultrabeast" in tags_gm: flags.append("legend")
        if note: flags.append("note")

        # 기술 세팅
        mv_rows, elite_moves, plus_moves = [], [], []
        seen = set()
        for e in raid_ok[:3]:
            m = next((mm for mm in g["members"] if mm["dex"] == e["_dex"] and (mm["_mega"] == e["mega"])), None) or \
                next((mm for mm in g["members"] if mm["dex"] == e["_dex"]), base)
            key = (e["fast"], e["charged"])
            if key in seen: continue
            seen.add(key)
            c1, e1, _ = mv_chip(e["fast"], m, P, ko_move, elite=e["fast_elite"] or e["fast"] in (P.get(m["speciesId"], {}).get("eliteMoves") or []))
            c2, e2, _ = mv_chip(e["charged"], m, P, ko_move, plus=e["plus"], elite=e["charged_elite"] or e["charged"] in (P.get(m["speciesId"], {}).get("eliteMoves") or []))
            lbl = TYPE_AB[e["type"]] + ("(M)" if e["mega"] else "(S)" if e["shadow"] else "")
            mv_rows.append(f'<div class="mvrow"><span class="lbl">{lbl}</span>{c1}{c2}</div>')
            for mid, el in ((e["fast"], e1), (e["charged"], e2)):
                if el: elite_moves.append(ko_move_name(mid, ko_move))
            if e["plus"]: plus_moves.append(ko_move_name(e["charged"], ko_move))
        league_names = {1500: "GL", 2500: "UL", 10000: "ML"}
        thr = {1500: THRESH["pvp_gl"], 2500: THRESH["pvp_ul"], 10000: THRESH["pvp_ml"]}
        for cp in sorted(pvp, key=lambda c: pvp[c]["rank"]):
            b = pvp[cp]
            if b["rank"] > thr[cp] and sec in ("both", "pvp"): continue
            if sec in ("raid", "xfer") and cp != min(pvp, key=lambda c: pvp[c]["rank"]): continue
            key = tuple(b["moveset"])
            if key in seen: continue
            seen.add(key)
            chips = []
            for mid in b["moveset"]:
                c, el, _ = mv_chip(mid, b["member"], P, ko_move)
                chips.append(c)
                if el: elite_moves.append(ko_move_name(mid, ko_move))
            lbl = league_names[cp] + ("(S)" if b["shadow"] else "")
            mv_rows.append(f'<div class="mvrow"><span class="lbl">{lbl}</span>{"".join(chips)}</div>')
        elite_moves = list(dict.fromkeys(elite_moves))
        plus_moves = list(dict.fromkeys(plus_moves))
        if note and note.get("tm", "").startswith("★"):
            tm = ""
        elif elite_moves:
            tm = f'<div class="tmnote">★ {" · ".join(esc(x) for x in elite_moves)} = 특별한 기술머신 필요</div>'
            elite_needed_total += 1
            flags.append("elite")
        elif mv_rows:
            tm = '<div class="tmnote ok">✓ 전부 일반 머신</div>'
        else:
            tm = ""
        if plus_moves:
            tm += f'<div class="tmnote">+ {" · ".join(esc(x) for x in plus_moves)} = 아직 미출시(예정) 기술 기준 순위</div>'
        if note and note.get("tm"):
            tm += f'<div class="tmnote">{esc(note["tm"])}</div>'
        mvs_html = "".join(mv_rows) + tm

        # 레이드 칩: 타입별 최고 1개씩, 최대 4개
        raid_chips, seen_t = [], set()
        for e in raid_ok:
            if e["type"] in seen_t: continue
            seen_t.add(e["type"])
            lbl = TYPE_AB[e["type"]] + ("(M)" if e["mega"] else "(S)" if e["shadow"] else "")
            title = f'{ko_label(e["_dex"], e["slug"].replace("-", "_"), ko_species, e["name"])} · {e["name"]} · eDPS {e["edps"]:.1f}'
            chip = rk(e["rank"], lbl)
            if not e["released"]:
                chip = chip.replace('class="rk', 'class="rk x').replace("</span>", " <small>미출시</small></span>")
            raid_chips.append(f'<span title="{esc(title)}">{chip}</span>')
            if len(raid_chips) >= 4: break
        raid_html = "".join(raid_chips) or '<span class="rk n">50위 밖</span>'

        def member_small(b):
            small = ("(S)" if b["shadow"] else "")
            if b["member"] is not base and (not b["member"]["_final"] or len(finals) > 1 or b["member"]["_mega"]):
                small = b["member"]["_label"] + small
            return small

        def pvp_chip(cp):
            b = pvp.get(cp)
            if not b: return rk(None)
            return rk(b["rank"], "", member_small(b))

        # 자동 메모
        auto = []
        if "legend" in flags: auto.append("전설/환상")
        if "regional" in tags_gm: auto.append("지역 한정")
        if has_shadow: auto.append("그림자 있음")
        if megas: auto.append("메가진화 있음")
        if sec == "raid" and raid_ok and all(e["shadow"] or e["mega"] for e in raid_ok):
            auto.append("<b>그림자/메가 개체만</b> 50위 안 (일반은 밖)")
        memo_html = ""
        if note and note.get("memo"):
            memo_html = note["memo"]
        if auto:
            memo_html += (" " if memo_html else "") + f'<span class="auto">{" · ".join(auto)}</span>'

        name_html = f'<b>{esc(base["_label"])}</b><span class="evo">{esc(evo_txt)}</span>'
        if note: name_html += '<span class="tag note">NOTE</span>'
        data_attr = f' data-flags="{" ".join(flags)}" data-dex="{base["dex"]}"'

        if sec == "both":
            rows["both"].append((min(r for r in (gl, ul, ml) if r is not None), f"""
                <tr{data_attr}>
                    <td class="name" data-label="포켓몬">{name_html}</td>
                    <td class="num" data-label="레이드">{raid_html}</td>
                    <td class="num" data-label="GL">{pvp_chip(1500)}</td>
                    <td class="num" data-label="UL">{pvp_chip(2500)}</td>
                    <td class="num" data-label="ML">{pvp_chip(10000)}</td>
                    <td class="mvs" data-label="기술">{mvs_html}</td>
                    <td class="memo" data-label="메모">{memo_html}</td>
                </tr>"""))
        elif sec == "raid":
            best_pvp = min(pvp.values(), key=lambda b: b["rank"]) if pvp else None
            pv = rk(best_pvp["rank"], league_names[[c for c in pvp if pvp[c] is best_pvp][0]] + " ", member_small(best_pvp)) if best_pvp else rk(None)
            rows["raid"].append((raid_ok[0]["rank"], f"""
                <tr{data_attr}>
                    <td class="name" data-label="포켓몬">{name_html}</td>
                    <td class="num" data-label="레이드">{raid_html}</td>
                    <td class="num" data-label="PVP">{pv}</td>
                    <td class="mvs" data-label="기술">{mvs_html}</td>
                    <td class="memo" data-label="메모">{memo_html}</td>
                </tr>"""))
        elif sec == "pvp":
            rows["pvp"].append((min(r for r in (gl, ul, ml) if r is not None), f"""
                <tr{data_attr}>
                    <td class="name" data-label="포켓몬">{name_html}</td>
                    <td class="num" data-label="GL">{pvp_chip(1500)}</td>
                    <td class="num" data-label="UL">{pvp_chip(2500)}</td>
                    <td class="num" data-label="ML">{pvp_chip(10000)}</td>
                    <td class="mvs" data-label="기술">{mvs_html}</td>
                    <td class="memo" data-label="메모">{memo_html}</td>
                </tr>"""))
        else:
            best = min(pvp.values(), key=lambda b: b["rank"]) if pvp else None
            chip = rk(best["rank"], league_names[[c for c in pvp if pvp[c] is best][0]] + " ", member_small(best), cls="r") if best else '<span class="rk n">랭킹 밖</span>'
            small = esc(evo_txt)
            if note and note.get("memo"):
                small += f' <span class="auto">{note["memo"]}</span>'
            rows["xfer"].append((base["dex"], f'<li{data_attr}><span class="nm">{esc(base["_label"])}<small>{small}</small></span>{chip}</li>'))
        stats[sec] += 1
        for cp, b in pvp.items():
            ticker_pool.append((cp, b["rank"], b["member"]["_label"], b["shadow"]))
        for e in raid_ok:
            if e["rank"] == 1:
                ticker_pool.append(("raid", e["type"], ko_label(e["_dex"], e["slug"].replace("-", "_"), ko_species, e["name"]), e["released"]))

    for k in rows:
        rows[k].sort(key=lambda x: x[0])

    tk = []
    for cp, lab in ((1500, "GL"), (2500, "UL"), (10000, "ML")):
        for _, r, name, sh in sorted([t for t in ticker_pool if t[0] == cp], key=lambda t: t[1])[:12]:
            tk.append(f'        <span class="tk"><b>{esc(name)}</b> {lab} <span class="up">#{r}</span>{"(S)" if sh else ""}</span>')
    for _, t, name, rel in [x for x in ticker_pool if x[0] == "raid"]:
        unrel = "" if rel else ' <span class="dn">미출시</span>'
        tk.append(f'        <span class="tk"><b>{esc(name)}</b> {TYPE_AB[t]} <span class="up">#1</span>{unrel}</span>')
    ticker_html = chr(10).join(tk)
    tpl = open(os.path.join(ROOT, "template.html"), encoding="utf-8").read()
    out = (tpl
           .replace("{{TICKER}}", ticker_html)
           .replace("{{BOTH_ROWS}}", "".join(r for _, r in rows["both"]))
           .replace("{{RAID_ROWS}}", "".join(r for _, r in rows["raid"]))
           .replace("{{PVP_ROWS}}", "".join(r for _, r in rows["pvp"]))
           .replace("{{XFER_ITEMS}}", "\n".join(r for _, r in rows["xfer"]))
           .replace("{{N_BOTH}}", str(stats["both"])).replace("{{N_RAID}}", str(stats["raid"]))
           .replace("{{N_PVP}}", str(stats["pvp"])).replace("{{N_XFER}}", str(stats["xfer"]))
           .replace("{{N_TOTAL}}", str(sum(stats.values())))
           .replace("{{N_ELITE}}", str(elite_needed_total))
           .replace("{{N_NOTES}}", str(sum(1 for k in rows for _, r in rows[k] if 'data-flags="' in r and "note" in r.split('data-flags="')[1].split('"')[0])))
           .replace("{{GL_N}}", f"{len(rank[1500]):,}").replace("{{UL_N}}", f"{len(rank[2500]):,}").replace("{{ML_N}}", f"{len(rank[10000]):,}")
           .replace("{{PVPOKE_DATE}}", gm.get("timestamp", "")[:10] if isinstance(gm.get("timestamp"), str) else str(gm.get("timestamp", ""))[:10])
           .replace("{{DITTO_DATE}}", ditto_updated)
           .replace("{{BUILD_DATE}}", time.strftime("%Y-%m-%d"))
           .replace("{{FETCHED}}", fetched)
           .replace("{{T_RAID}}", str(THRESH["raid_top"])).replace("{{T_BOTH}}", str(THRESH["both_pvp"]))
           .replace("{{T_GL}}", str(THRESH["pvp_gl"])).replace("{{T_UL}}", str(THRESH["pvp_ul"])).replace("{{T_ML}}", str(THRESH["pvp_ml"]))
           )
    with open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8") as f:
        f.write(out)
    shutil.copyfile(os.path.join(ROOT, "index.html"), os.path.join(ROOT, "poke_guide.html"))
    print(f"groups: {sum(stats.values())}  both={stats['both']} raid={stats['raid']} pvp={stats['pvp']} xfer={stats['xfer']}  "
          f"elite-needed={elite_needed_total}  size={len(out):,} bytes")


if __name__ == "__main__":
    main()
