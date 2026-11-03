# -*- coding: utf-8 -*-
"""V2 (final direction): client cut 9.5 s + AI NATI STUDIOS showreel cut 15 s.

All timings in OUTPUT frames @ 24 fps. Music: 120 BPM -> one beat = 12 frames.
"""
FPS = 24
W, H = 1080, 1920

SRC = {
    "tractor": "01_tractor_best_take.mp4",
    # new hook take (uploaded later): grandpa brakes and the tractor comes to a halt
    "tractor_new": "01b_tractor_hook_new.mp4",
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
    # 0.00 HOOK (2.5 s): grandpa charging on the tractor, dust, shocked face;
    #      ~1.1 s he slams the brakes, the tractor lurches and halts (src 11-57)
    dict(name="hook_drive", src="tractor_new", frames=rng(11, 57), grade="village"),
    # 1.96 FREEZE on the halt (src 58: tractor stopped, eyes to the side) + thump
    dict(name="hook_freeze", src="tractor_new", frames=hold(58, 13), grade="village", freeze=True),
    # 2.50 soccer (ball rising) -> 2.83 FREEZE ball in the air
    dict(name="soccer_kick", src="soccer", frames=rng(9, 16), grade="village"),
    dict(name="soccer_freeze", src="soccer", frames=hold(17, 12), grade="village", freeze=True),
    # 3.33 coffee pour -> 3.67 FREEZE stream in the air, clock stops, silence
    dict(name="coffee_pour", src="coffee", frames=rng(18, 25), grade="village"),
    dict(name="coffee_freeze", src="coffee", frames=hold(26, 20), grade="village", freeze=True),
    # 4.50 HARD CUT on the music hit: the spit, knife at work
    dict(name="spit", src="food", frames=rng(0, 23), grade="food"),
    # 5.50 punch-in on the hot meat being sliced (cut on action)
    dict(name="cutting", src="food", frames=rng(36, 47), grade="food", zoom=1.18, center=(0.52, 0.44)),
    # 6.00 meat slides from the scoop into the pita (tight: hides the heart-shaped pita)
    dict(name="into_pita", src="food", frames=rng(105, 116), grade="food", zoom=1.32, center=(0.47, 0.36)),
    # 6.50 tahini pour on the loaded pita
    dict(name="tahini", src="food", frames=rng(164, 193), grade="food"),
    # 7.75 the ready pita, hero slow-mo (src 215-240 stretched x1.6 with motion interpolation)
    dict(name="hero", src="food", slowmo=(215, 240, 42), grade="food"),
]

AD_TEXT = [
    dict(id="hook", start=24, end=59, y=1130, size=132, font="heebo", anim="slam", stagger=2, lines=[
        [("מה ", CREAM), ("עצר", ORANGE), (" את", CREAM)],
        [("כל המושב?!", CREAM)],
    ]),
    dict(id="reveal", start=108, end=131, y=1300, size=112, font="heebo", anim="slam", lines=[
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
STUDIO_LOGO = dict(start=288, y=650, width=860)
# contact line under the CTA: Einat's mobile for studio enquiries
HANDLE = dict(text="052-2858774", start=309, y=1365, size=84)
CTA_ICON = dict(start=306, wiggles=(318, 336))

SYNC_CLIENT = dict(
    brake=26, freeze_tractor=47, cut_soccer=60, freeze_soccer=68, cut_coffee=80, freeze_coffee=88,
    drop=108, knife_wide=120, cutting=132, into_pita=144, tahini=156, hero=186,
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
