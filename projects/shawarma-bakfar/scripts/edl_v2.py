# -*- coding: utf-8 -*-
"""V2 (final direction): client cut 9.5 s + AI NATI STUDIOS showreel cut 15 s.

All timings in OUTPUT frames @ 24 fps. Music: 120 BPM -> one beat = 12 frames.
"""
FPS = 24
W, H = 1080, 1920

SRC = {
    "tractor": "01_tractor_best_take.mp4",
    "soccer": "02_soccer_field_take.mp4",
    "coffee": "03_coffee_pouring_source.mp4",
    "food": "05_shawarma_food_original.mp4",
}

# shawarma palette: cream / orange / gold
CREAM = (255, 243, 218)
ORANGE = (255, 138, 30)
GOLD = (255, 193, 77)
# AI NATI STUDIOS palette: pink / yellow / deep purple / white
PINK = (255, 46, 136)
YELLOW = (255, 212, 0)
PURPLE = (42, 11, 74)
PURPLE_2 = (86, 22, 140)
WHITE = (255, 255, 255)


def rng(a, b):
    return list(range(a, b + 1))


def hold(n, count):
    return [n] * count


# --------------------------------------------------------- shawarma ad ----
AD = [
    # 0.00 tractor: shocked face, wheels + dust moving, engine + brakes
    dict(name="tractor_drive", src="tractor", frames=rng(46, 54), grade="village"),
    # 0.375 cut on motion to the head turn (hidden under the screech)
    dict(name="tractor_headturn", src="tractor", frames=rng(88, 93), grade="village"),
    # 0.625 FREEZE + thump exactly on the stop
    dict(name="tractor_freeze", src="tractor", frames=hold(93, 9), grade="village", freeze=True),
    # 1.00 soccer (ball rising) -> 1.33 FREEZE ball in the air
    dict(name="soccer_kick", src="soccer", frames=rng(9, 16), grade="village"),
    dict(name="soccer_freeze", src="soccer", frames=hold(17, 16), grade="village", freeze=True),
    # 2.00 coffee pour -> 2.33 FREEZE stream in the air, clock stops, silence
    dict(name="coffee_pour", src="coffee", frames=rng(18, 25), grade="village"),
    dict(name="coffee_freeze", src="coffee", frames=hold(26, 16), grade="village", freeze=True),
    # 3.00 HARD CUT on the music hit: the spit, knife at work
    dict(name="spit", src="food", frames=rng(0, 29), grade="food"),
    # 4.25 punch-in on the hot meat being sliced (cut on action)
    dict(name="cutting", src="food", frames=rng(30, 47), grade="food", zoom=1.18, center=(0.52, 0.44)),
    # 5.00 meat slides from the scoop into the pita (tight: hides the heart-shaped pita)
    dict(name="into_pita", src="food", frames=rng(105, 116), grade="food", zoom=1.32, center=(0.47, 0.36)),
    # 5.50 tahini pour on the loaded pita
    dict(name="tahini", src="food", frames=rng(158, 205), grade="food"),
    # 7.50 the ready pita, hero slow-mo (src 215-240 stretched x1.85 with motion interpolation)
    dict(name="hero", src="food", slowmo=(215, 240, 48), grade="food"),
]

AD_TEXT = [
    dict(id="hook", start=0, end=23, y=1130, size=132, font="heebo", anim="slam", stagger=2, lines=[
        [("מה ", CREAM), ("עצר", ORANGE), (" את", CREAM)],
        [("כל המושב?!", CREAM)],
    ]),
    dict(id="reveal", start=72, end=101, y=1300, size=112, font="heebo", anim="slam", lines=[
        [("חוץ ", CREAM), ("מהשווארמה.", GOLD)],
    ]),
]

CLIENT_LOGO = dict(start=192, d=600, y=470)  # 8.00 s, on the beat

# ------------------------------------------------------ studio twist -------
TWIST_START = 228  # 9.50 s
TWIST = dict(
    freeze_end=263,          # frozen ad frame (dimmed) 9.50 - 11.0
    wipe=(258, 264),         # colour wipe into the studio palette
    studio_end=360,          # 15.0 s
)
TWIST_TEXT = [
    dict(id="if_stopped", start=228, end=245, y=900, size=150, font="rubik", anim="slam", bg="freeze",
         lines=[[("אם עצרתם...", WHITE)]]),
    dict(id="it_worked", start=246, end=263, y=900, size=250, font="rubik", anim="punch", bg="freeze",
         lines=[[("זה עבד.", YELLOW)]]),
    dict(id="q1", start=264, end=287, y=820, size=140, font="rubik", anim="pop", exit="shrink",
         lines=[[("בעלי עסקים,", WHITE)]]),
    dict(id="q2", start=276, end=287, y=1060, size=124, font="rubik", anim="pop", exit="shrink",
         lines=[[("רוצים ", WHITE), ("שיזכרו", YELLOW)], [("אתכם?", WHITE)]]),
    dict(id="tagline", start=294, end=359, y=1015, size=96, font="rubik", anim="rise",
         lines=[[("פרסומות", WHITE)], [("שלא גוללים עליהן.", WHITE)]]),
    dict(id="cta", start=306, end=359, y=1235, size=104, font="rubik", anim="pop",
         lines=[[("שלחו הודעה", YELLOW)]]),
]
STUDIO_LOGO = dict(start=288, y=650, width=820)
HANDLE = dict(text="@ainati_studios", start=309, y=1355, size=66)
CTA_ICON = dict(start=306, wiggles=(318, 336))

SYNC_CLIENT = dict(
    freeze_tractor=15, cut_soccer=24, freeze_soccer=32, cut_coffee=48, freeze_coffee=56,
    drop=72, knife_wide=84, cutting=102, into_pita=120, tahini=132, hero=180,
    logo=192, final_hit=216, end=228,
)
SYNC_STUDIO = dict(SYNC_CLIENT, final_hit=None, end=360,
                   twist=228, it_worked=246, riser=252, wipe=258, studio_drop=264,
                   q2=276, studio_logo=288, tagline=294, cta=306, wiggles=(318, 336),
                   studio_final=348)

VERSIONS = {
    "client": dict(out="Shawarma_Bakfar_Final.mp4", frames=228, sync=SYNC_CLIENT, twist=False),
    "studio": dict(out="AI_NATI_Shawarma_Showreel.mp4", frames=360, sync=SYNC_STUDIO, twist=True),
}


def seg_len(s):
    if "slowmo" in s:
        return s["slowmo"][2]
    return len(s["frames"])


def starts(edl):
    out, f = [], 0
    for s in edl:
        out.append(f)
        f += seg_len(s)
    return out


if __name__ == "__main__":
    tot = 0
    for s, st in zip(AD, starts(AD)):
        print(f"{st:4d} {st / FPS:6.3f}s {s['name']}")
        tot = st + seg_len(s)
    print("ad frames", tot, tot / FPS)
