#!/usr/bin/env python3
"""SubagentStop hook: save gpt-scout, hike-researcher and photo-scout reports to gpt-reports/ and enforce the report format.

It doesn't rely on the exact SubagentStop payload schema. It looks for the report text in
any field that might hold it (last message, agent transcript), and acts only on text whose
first line is "GPT-SCOUT REPORT: <slug>", "HIKE-RESEARCH REPORT: <slug>" or "PHOTO-SCOUT REPORT: <slug>". Every other subagent is ignored.
The payload's top-level keys (never values) are logged to gpt-reports/.hook-debug.log, so
you can see the real schema."""
import datetime as dt, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS = os.path.join(ROOT, "gpt-reports")
STATE = os.path.join(REPORTS, ".hook-state.json")
MARK = re.compile(r"^\s*(GPT-SCOUT|HIKE-RESEARCH|PHOTO-SCOUT) REPORT:\s*([a-z0-9][a-z0-9-]*)\s*$", re.M)
REQUIRED = {
 "GPT-SCOUT": ({"id", "name", "kind", "verdict", "conf", "area", "ref", "dist", "gain", "time",
                "terrain", "cost", "caution", "why", "pts", "fits"}, ("ADD", "ADD*", "MAYBE")),
 "HIKE-RESEARCH": ({"id", "name", "area", "dist", "gain", "time", "sac", "kind", "nights", "hazards",
                    "note", "pts", "verdict", "conf"}, ("ADD", "ADD*", "MAYBE")),
 "PHOTO-SCOUT": ({"key", "verdict", "looked", "note", "photos"}, ("OK", "NONE")),
}
PHOTO_FIELDS = {"title", "w", "thumb", "full", "page", "shows"}

def photo_problems(i, o):
    """Extra checks for one PHOTO-SCOUT json item."""
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    from photos import all_keys, HOSTS
    out, ph = [], o.get("photos")
    if o.get("key") not in all_keys():
        out.append(f"json item {i}: key {o.get('key')!r} is not a hike id from tools/catalog.py or a place in PLACE_Q")
    if not isinstance(ph, list):
        return out + [f"json item {i}: photos must be a list"]
    if o.get("verdict") == "OK" and not 1 <= len(ph) <= 3:
        out.append(f"json item {i} ({o.get('key')}): verdict OK needs 1-3 photos, got {len(ph)}")
    if o.get("verdict") == "NONE" and ph:
        out.append(f"json item {i} ({o.get('key')}): verdict NONE must have an empty photos list")
    for j, x in enumerate(ph):
        miss = PHOTO_FIELDS - set(x)
        if miss: out.append(f"json item {i} ({o.get('key')}) photo {j}: missing {sorted(miss)}")
        for f in ("thumb", "full"):
            if isinstance(x.get(f), str) and not x[f].startswith(HOSTS):
                out.append(f"json item {i} ({o.get('key')}) photo {j}: {f} must be on upload.wikimedia.org or thumb.wikimedia.org")
        if isinstance(x.get("page"), str) and not x["page"].startswith("https://commons.wikimedia.org/"):
            out.append(f"json item {i} ({o.get('key')}) photo {j}: page must be on commons.wikimedia.org")
    return out
MAX_BLOCKS = 2

def texts_from_transcript(path):
    found = []
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                try:
                    o = json.loads(line)
                except Exception:
                    continue
                c = (o.get("message") or {}).get("content")
                if isinstance(c, str):
                    found.append(c)
                elif isinstance(c, list):
                    for x in c:
                        if x.get("type") == "text":
                            found.append(x.get("text", ""))
                        elif x.get("type") == "tool_use":  # some harnesses hand back via a tool call
                            for v in (x.get("input") or {}).values():
                                if isinstance(v, str):
                                    found.append(v)
    except OSError:
        pass
    return found

def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return
    os.makedirs(REPORTS, exist_ok=True)
    with open(os.path.join(REPORTS, ".hook-debug.log"), "a") as fh:
        fh.write(f"{dt.datetime.now():%Y-%m-%d %H:%M:%S} keys={sorted(payload.keys())} agent_type={payload.get('agent_type')!r}\n")

    candidates = []
    for k in ("last_assistant_message", "agent_last_message", "result"):
        if isinstance(payload.get(k), str):
            candidates.append(payload[k])
    for k in ("agent_transcript_path", "transcript_path"):
        if isinstance(payload.get(k), str):
            candidates += texts_from_transcript(payload[k])
    reports = [t for t in candidates if MARK.match(t.lstrip().splitlines()[0] if t.strip() else "")]
    if not reports:
        return  # not a gpt-scout report
    text = reports[-1].strip()
    kind_, slug = MARK.match(text.splitlines()[0]).groups()
    required, verdicts = REQUIRED[kind_]
    slug = {"HIKE-RESEARCH": "hikes-", "PHOTO-SCOUT": "photos-"}.get(kind_, "") + slug

    # --- format checks
    problems = []
    if "Date check:" not in text[:600]:
        problems.append("missing the 'Date check:' line right after the header")
    blocks = re.findall(r"```json\s*(.*?)```", text, re.S)
    data = None
    if len(blocks) != 1:
        problems.append(f"expected exactly one ```json block, found {len(blocks)}")
    else:
        try:
            data = json.loads(blocks[0])
            if not isinstance(data, list):
                problems.append("the json block must be a list")
            else:
                for i, o in enumerate(data):
                    miss = required - set(o)
                    if miss:
                        problems.append(f"json item {i} ({o.get('id', '?')}) is missing keys: {sorted(miss)}")
                    if o.get("verdict") not in verdicts:
                        problems.append(f"json item {i}: verdict must be one of {', '.join(verdicts)}"
                                        + (" (NO items belong only in the prose)" if kind_ != "PHOTO-SCOUT" else ""))
                    if kind_ == "PHOTO-SCOUT":
                        problems += photo_problems(i, o)
                    elif not (isinstance(o.get("pts"), list) and o["pts"] and all(isinstance(p, list) and len(p) == 2 for p in o["pts"])):
                        problems.append(f"json item {i}: pts must be a non-empty list of [lat, lon]")
        except json.JSONDecodeError as e:
            problems.append(f"the json block doesn't parse: {e}")
    if not re.search(r"https?://", text):
        problems.append("no source URLs found")

    state = {}
    try:
        state = json.load(open(STATE))
    except Exception:
        pass
    if problems and state.get(slug, 0) < MAX_BLOCKS:
        state[slug] = state.get(slug, 0) + 1
        json.dump(state, open(STATE, "w"))
        print(json.dumps({"decision": "block",
                          "reason": f"Your {kind_} report isn't in the required format yet. Fix these and send the full report again:\n- " + "\n- ".join(problems)}))
        return

    stamp = dt.date.today().isoformat()
    md = os.path.join(REPORTS, f"{stamp}-{slug}.md")
    with open(md, "w", encoding="utf-8") as fh:
        fh.write(f"# {kind_.replace('-', ' ').title()} report: {slug}\n\n*Saved automatically by the SubagentStop hook on {stamp}."
                 + (" Format problems left unfixed: " + "; ".join(problems) if problems else "") + "*\n\n" + text + "\n")
    saved = [os.path.relpath(md, ROOT)]
    if data is not None and not problems:
        js = os.path.join(REPORTS, f"{stamp}-{slug}.json")
        json.dump(data, open(js, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        saved.append(os.path.relpath(js, ROOT))
    state.pop(slug, None)
    json.dump(state, open(STATE, "w"))
    print(json.dumps({"systemMessage": f"{kind_.lower()} report saved: " + ", ".join(saved)}))

if __name__ == "__main__":
    main()
