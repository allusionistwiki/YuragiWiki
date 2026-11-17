#!/usr/bin/env python3
"""④ chains.jsonl へ LLM 要約（summaries.jsonl）を chain_sha1 照合付きで反映する。

入力: AllusionistWiki_work work/yuragi/L0/runs/*_l0sum/summaries.jsonl（古い順にマージ・同一 chain は新しい run 優先）
照合: ③ structured.jsonl から chain 本文を再生成し sha1 == summaries.chain_sha1（全件）。
ゲート: 全 chain に非空 summary が付くこと（削除群は「（削除投稿）」）。
出力: 各篇 chains.jsonl（summary 欄追加・LF 保存）＋ _layers_manifest.json に summary 来歴。
使い方: python tools/merge_chain_summaries.py
"""
import json
import sys
import hashlib
from pathlib import Path
from datetime import datetime, timezone, timedelta

REPO = Path(__file__).resolve().parent.parent
RAW = REPO / "raw" / "bbs"
L0 = Path(r"C:/Users/d5dx/Downloads/Code/AllusionistWiki_work/work/yuragi/L0")
JST = timezone(timedelta(hours=9))

def sha1_bytes(b: bytes) -> str:
    return hashlib.sha1(b).hexdigest()

def rd(p: Path) -> str:
    return p.read_bytes().decode("utf-8", errors="replace")

def jl(p: Path):
    return [json.loads(l) for l in rd(p).splitlines() if l.strip()]

def unit_dirs():
    """④ chains.jsonl を持つ全篇ディレクトリ。"""
    dirs = []
    for d in sorted(RAW.rglob("chains.jsonl")):
        dirs.append(d.parent)
    return dirs

def main():
    by_chain = {}
    sdirs = sorted(p for p in (L0 / "runs").iterdir() if p.name.endswith("_l0sum"))
    for sd in sdirs:
        for s in jl(sd / "summaries.jsonl"):
            by_chain[s["chain_id"]] = s
    if not by_chain:
        raise SystemExit("summaries.jsonl が見つからない")

    n_units = n_chains = n_missing = n_sha_bad = 0
    per_unit = {}
    for d in unit_dirs():
        sb = {r["post_no"]: r["body"] for r in jl(d / "structured.jsonl")}
        chains = jl(d / "chains.jsonl")
        out_rows = []
        for c in chains:
            s = by_chain.get(c["chain_id"])
            if s is None:
                n_missing += 1
                out_rows.append(c)
                continue
            text = "\n\n".join(sb[n] for n in c["post_nos"])
            if sha1_bytes(text.encode("utf-8")) != s["chain_sha1"]:
                n_sha_bad += 1
                print(f"SHA MISMATCH {c['chain_id']}", file=sys.stderr)
                out_rows.append(c)
                continue
            c = dict(c)
            c["summary"] = s["summary"]
            c["summary_sha1"] = s["chain_sha1"]
            c["summary_model"] = s.get("model", "")
            out_rows.append(c)
            n_chains += 1
        (d / "chains.jsonl").write_text(
            "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in out_rows),
            encoding="utf-8", newline="\n")
        n_units += 1
        per_unit[d.name] = len(out_rows)

    if n_missing:
        raise SystemExit(f"GATE FAIL: summary 欠損 {n_missing} 群")
    if n_sha_bad:
        raise SystemExit(f"GATE FAIL: chain_sha1 不一致 {n_sha_bad} 群")

    man_p = RAW / "_layers_manifest.json"
    man = json.loads(rd(man_p)) if man_p.exists() else {}
    man["summary_merge"] = {
        "merged_at": datetime.now(JST).isoformat(),
        "sum_runs": [sd.name for sd in sdirs],
        "summaries_sha1_combined": sha1_bytes(
            b"".join((sd / "summaries.jsonl").read_bytes() for sd in sdirs)),
        "units": n_units, "chains": n_chains,
        "source": "AllusionistWiki_work work/yuragi/L0/runs/*_l0sum",
    }
    man_p.write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print(json.dumps({"units": n_units, "chains_with_summary": n_chains}, ensure_ascii=False))

if __name__ == "__main__":
    main()
