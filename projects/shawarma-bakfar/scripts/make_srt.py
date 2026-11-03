# -*- coding: utf-8 -*-
"""Export the on-screen Hebrew lines as an .srt (same timings as the burn-in).

python3 make_srt.py --version main --out main.he.srt
Each line is wrapped in RLM marks so punctuation sits correctly in players
that default to left-to-right.
"""
import argparse

import edl as E

RLM = "‏"


def tc(frame):
    ms = int(round(frame / E.FPS * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def cues(version):
    v = E.VERSIONS[version]
    out = []
    for c in v["text"]:
        lines = ["".join(t for t, _ in runs) for runs in c["lines"]]
        out.append((c["start"], c["end"] + 1, lines))
    starts = E.segment_starts(v["edl"])
    for s, st in zip(v["edl"], starts):
        if s["name"] == "endcard":
            out.append((st + E.ENDCARD["tag_in"], st + s["count"], [E.ENDCARD["tag"]]))
    return out


def write(version, path):
    with open(path, "w", encoding="utf-8") as f:
        for i, (a, b, lines) in enumerate(cues(version), 1):
            f.write(f"{i}\n{tc(a)} --> {tc(b)}\n")
            for ln in lines:
                f.write(f"{RLM}{ln}{RLM}\n")
            f.write("\n")
    print("wrote", path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default="main", choices=list(E.VERSIONS))
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    write(a.version, a.out)
