# -*- coding: utf-8 -*-
"""Edit decision list for "Shawarma BaKfar - the day the moshav stopped".

Everything is expressed in OUTPUT frames at 24 fps (the native rate of all
sources), so video and audio are cut from the same timeline.

Source frame indices are 0-based decoded frame numbers of each source file.
"""

FPS = 24
W, H = 1080, 1920

# Source files, named as in the brief. build.sh links the uploaded files to
# these names. 04_coffee_freeze_ready.mp4 was NOT in the delivered package, so
# the coffee freeze is built from 03_coffee_pouring_source.mp4.
SRC = {
    "tractor": "01_tractor_best_take.mp4",
    "soccer": "02_soccer_field_take.mp4",
    "coffee": "03_coffee_pouring_source.mp4",
    "food": "05_shawarma_food_original.mp4",
}

CREAM = (255, 243, 218)
ORANGE = (255, 150, 40)


def rng(a, b):
    """inclusive source-frame range"""
    return list(range(a, b + 1))


def hold(n, count):
    """true freeze frame: the same decoded frame repeated"""
    return [n] * count


# --------------------------------------------------------------------------
# MAIN  - 276 frames = 11.5 s
# --------------------------------------------------------------------------
# zoom/center: optional punch-in (crop of the 9:16 frame, center in 0..1)
MAIN = [
    # 00:00.00 tractor - shocked face from frame 1, wheels + dust moving
    dict(name="tractor_drive", src="tractor", frames=rng(42, 55), grade="village"),
    # jump inside the take to the head-turn (~3.7-3.9 s in source), cut on motion,
    # hidden under the brake screech
    dict(name="tractor_headturn", src="tractor", frames=rng(88, 93), grade="village"),
    # 00:00.83 FREEZE (whole frame, no wheel motion)
    dict(name="tractor_freeze", src="tractor", frames=hold(93, 16), grade="village", freeze=True),
    # 00:01.50 soccer - kick follow-through, ball rising (src 0-4 skipped: ghost ball)
    dict(name="soccer_kick", src="soccer", frames=rng(5, 16), grade="village"),
    # 00:02.00 FREEZE with ball in the air above the kids' heads
    dict(name="soccer_freeze", src="soccer", frames=hold(17, 19), grade="village", freeze=True),
    # 00:02.79 coffee pour (04_coffee_freeze_ready missing -> built from 03)
    dict(name="coffee_pour", src="coffee", frames=rng(14, 25), grade="village"),
    # 00:03.29 FREEZE - coffee stream hangs in the air
    dict(name="coffee_freeze", src="coffee", frames=hold(26, 29), grade="village", freeze=True),
    # 00:04.50 HARD CUT - glowing spit, knife slicing (the only thing moving)
    dict(name="spit_wide", src="food", frames=rng(0, 23), grade="food"),
    # 00:05.50 punch-in cut on the beat - knife through the meat
    dict(name="cut_a", src="food", frames=rng(24, 35), grade="food", zoom=1.12, center=(0.46, 0.42)),
    # 00:06.00 tighter punch-in - slice peeling off
    dict(name="cut_b", src="food", frames=rng(36, 47), grade="food", zoom=1.22, center=(0.55, 0.45)),
    # 00:06.50 tahini pour on the loaded pita (heart-pita filling + floating meat skipped)
    dict(name="tahini_pour", src="food", frames=rng(158, 205), grade="food"),
    # 00:08.50 full sandwich in hands, tahini drip (crossfade frames 207-214 skipped)
    dict(name="hero_hands", src="food", frames=rng(216, 239), grade="food"),
    # 00:09.50 END CARD (logo + line) - 2.0 s
    dict(name="endcard", src=None, count=48, bg=("food", 239)),
]

MAIN_TEXT = [
    dict(id="t1", start=0, end=66, y=1150, size=128, lines=[
        [("מה עצר את", CREAM)],
        [("כל המושב", CREAM), ("?!", ORANGE)],
    ]),
    dict(id="t2", start=88, end=107, y=1470, size=132, lines=[
        [("הכול נעצר...", CREAM)],
    ]),
    dict(id="t3", start=108, end=155, y=1300, size=110, lines=[
        [("חוץ ", CREAM), ("מהשווארמה.", ORANGE)],
    ]),
]

# end card timing, relative to the start of the endcard segment
ENDCARD = dict(logo_in=0, tag_in=12, hit=24, logo_d=780, logo_y=860,
               tag_y=1420, tag_size=100, tag="עוצרים בשביל ביס.")

# music / sfx sync points for the main cut (output frames)
MAIN_SYNC = dict(
    freeze_tractor=20, cut_soccer=36, freeze_soccer=48, cut_coffee=67,
    freeze_coffee=79, drop=108, knife_wide=120, cut_a=132, cut_b=144,
    pour=156, hands=204, logo=228, final_hit=252, end=276,
)

# --------------------------------------------------------------------------
# SHORT - 156 frames = 6.5 s : tractor -> frozen ball -> shawarma -> logo
# --------------------------------------------------------------------------
SHORT = [
    dict(name="tractor_drive", src="tractor", frames=rng(42, 55), grade="village"),
    dict(name="tractor_headturn", src="tractor", frames=rng(88, 93), grade="village"),
    dict(name="tractor_freeze", src="tractor", frames=hold(93, 12), grade="village", freeze=True),
    dict(name="soccer_kick", src="soccer", frames=rng(5, 16), grade="village"),
    dict(name="soccer_freeze", src="soccer", frames=hold(17, 16), grade="village", freeze=True),
    dict(name="spit_wide", src="food", frames=rng(0, 23), grade="food"),
    dict(name="tahini_pour", src="food", frames=rng(168, 191), grade="food"),
    dict(name="endcard", src=None, count=48, bg=("food", 239)),
]

SHORT_TEXT = [
    dict(id="t1", start=0, end=59, y=1150, size=128, lines=[
        [("מה עצר את", CREAM)],
        [("כל המושב", CREAM), ("?!", ORANGE)],
    ]),
    dict(id="t3", start=60, end=83, y=1300, size=110, lines=[
        [("חוץ ", CREAM), ("מהשווארמה.", ORANGE)],
    ]),
]

SHORT_SYNC = dict(
    freeze_tractor=20, cut_soccer=32, freeze_soccer=44, drop=60, knife_wide=72,
    pour=84, logo=108, final_hit=132, end=156,
)

VERSIONS = {
    "main": dict(edl=MAIN, text=MAIN_TEXT, sync=MAIN_SYNC),
    "short": dict(edl=SHORT, text=SHORT_TEXT, sync=SHORT_SYNC),
}


def total_frames(edl):
    return sum(len(s["frames"]) if s.get("src") else s["count"] for s in edl)


def segment_starts(edl):
    out, f = [], 0
    for s in edl:
        out.append(f)
        f += len(s["frames"]) if s.get("src") else s["count"]
    return out


if __name__ == "__main__":
    for k, v in VERSIONS.items():
        n = total_frames(v["edl"])
        print(k, n, "frames =", n / FPS, "s")
        for s, st in zip(v["edl"], segment_starts(v["edl"])):
            print(f"   {st:4d} {st / FPS:6.3f}s  {s['name']}")
