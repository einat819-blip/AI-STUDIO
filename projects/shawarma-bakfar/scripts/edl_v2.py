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
# Shot order and the hook take are locked (approved). Freezes are long enough
# to READ the caption that lands on them.
AD = [
    # 0.00 HOOK: grandpa charging on the tractor, dust; ~1.1 s he slams the
    #      brakes, the tractor lurches and halts (src 11-57)
    dict(name="hook_drive", src="tractor_new", frames=rng(11, 57), grade="village"),
    # 1.96 FREEZE on the halt (src 58) + thump
    dict(name="hook_freeze", src="tractor_new", frames=hold(58, 13), grade="village", freeze=True),
    # 2.50 soccer (ball rising) -> 2.83 FREEZE ball in the air + "אפילו הזמן עצר"
    dict(name="soccer_kick", src="soccer", frames=rng(9, 16), grade="village"),
    dict(name="soccer_freeze", src="soccer", frames=hold(17, 22), grade="village", freeze=True),
    # 3.75 coffee pour -> 4.08 FREEZE stream in the air + "לראות מה קרה..."
    dict(name="coffee_pour", src="coffee", frames=rng(18, 25), grade="village"),
    dict(name="coffee_freeze", src="coffee", frames=hold(26, 24), grade="village", freeze=True),
    # 5.08 HARD CUT on the music burst: the spit + "שווארמה בכפר נפתחה!"
    dict(name="spit", src="food", frames=rng(0, 23), grade="food"),
    # 6.08 punch-in on the hot meat being sliced (cut on action)
    dict(name="cutting", src="food", frames=rng(36, 47), grade="food", zoom=1.18, center=(0.52, 0.44)),
    # 6.58 meat slides from the scoop into the pita (tight: hides the heart-shaped pita)
    dict(name="into_pita", src="food", frames=rng(105, 116), grade="food", zoom=1.32, center=(0.47, 0.36)),
    # 7.08 tahini pour on the loaded pita (no caption on it)
    dict(name="tahini", src="food", frames=rng(166, 189), grade="food"),
    # 8.08 the ready pita, slow-mo; "עכשיו כולם בדרך!" sits on the dark apron above it
    dict(name="hero", src="food", slowmo=(215, 229, 24), grade="food"),
    # 9.08 END CARD: same shot continues blurred behind a big logo + closing line
    dict(name="endcard", src="food", slowmo=(229, 240, 42), grade="food", endcard=True),
]

AD_TEXT = [
    dict(id="hook", start=26, end=56, y=1130, size=132, font="heebo", anim="slam", stagger=2, exit="shrink",
         lines=[[("מה ", CREAM), ("עצר", ORANGE), (" את", CREAM)], [("כל המושב?!", CREAM)]]),
    dict(id="time1", start=68, end=89, y=1450, size=120, font="heebo", anim="slam",
         lines=[[("אפילו הזמן ", CREAM), ("עצר", ORANGE)]]),
    dict(id="time2", start=98, end=121, y=1450, size=120, font="heebo", anim="slam",
         lines=[[("לראות מה קרה...", CREAM)]]),
    dict(id="opened1", start=122, end=145, y=1150, size=124, font="heebo", anim="slam",
         lines=[[("שווארמה בכפר", CREAM)]]),
    dict(id="opened2", start=125, end=145, y=1355, size=210, font="heebo", anim="punch",
         lines=[[("נפתחה!", ORANGE)]]),
    dict(id="on_the_way", start=194, end=217, y=300, size=104, font="heebo", anim="slam",
         lines=[[("עכשיו כולם בדרך!", CREAM)]]),
    dict(id="closing", start=224, end=259, y=1385, size=96, font="heebo", anim="rise",
         lines=[[("יש דברים ששווה", CREAM)], [("לעצור בשבילם.", CREAM)]]),
]

CLIENT_ENDCARD = dict(start=218, d=780, y=800)  # big badge, on the beat

# ------------------------------------------------------ studio twist -------
TWIST_START = 260  # client cut ends here (10.83 s)
TW = TWIST_START
TWIST = dict(freeze_end=TW + 35, wipe=(TW + 30, TW + 36), studio_end=TW + 132)
TWIST_TEXT = [
    dict(id="if_stopped", start=TW, end=TW + 17, y=900, size=150, font="rubik", anim="slam", bg="freeze",
         lines=[[("אם עצרתם...", WHITE)]]),
    dict(id="it_worked", start=TW + 18, end=TW + 35, y=900, size=250, font="rubik", anim="punch", bg="freeze",
         lines=[[("זה עבד.", YELLOW)]]),
    dict(id="q1", start=TW + 36, end=TW + 59, y=820, size=140, font="rubik", anim="pop", exit="shrink",
         lines=[[("בעלי עסקים,", WHITE)]]),
    dict(id="q2", start=TW + 48, end=TW + 59, y=1060, size=124, font="rubik", anim="pop", exit="shrink",
         lines=[[("רוצים ", WHITE), ("שיזכרו", YELLOW)], [("אתכם?", WHITE)]]),
    dict(id="tagline", start=TW + 66, end=TW + 131, y=1015, size=96, font="rubik", anim="rise",
         lines=[[("פרסומות", WHITE)], [("שלא גוללים עליהן.", WHITE)]]),
    dict(id="cta", start=TW + 78, end=TW + 131, y=1235, size=104, font="rubik", anim="pop",
         lines=[[("שלחו הודעה", YELLOW)]]),
]
STUDIO_LOGO = dict(start=TW + 60, y=650, width=860)
# contact line under the CTA (spec: the Instagram handle; --contact can swap in the phone)
HANDLE = dict(text="@ainati_studios", start=TW + 81, y=1360, size=80)
PHONE = "052-2858774"
CTA_ICON = dict(start=TW + 78, wiggles=(TW + 90, TW + 108))

SYNC_CLIENT = dict(
    brake=26, hook_text=26, freeze_tractor=47, cut_soccer=60, freeze_soccer=68, cut_coffee=90,
    freeze_coffee=98, drop=122, knife_wide=134, cutting=146, into_pita=158, tahini=170, hero=194,
    on_the_way=194, logo=218, closing=224, final_hit=242, end=260,
)
SYNC_STUDIO = dict(SYNC_CLIENT, final_hit=None, end=TW + 132,
                   twist=TW, it_worked=TW + 18, riser=TW + 24, wipe=TW + 30, studio_drop=TW + 36,
                   q2=TW + 48, studio_logo=TW + 60, tagline=TW + 66, cta=TW + 78,
                   wiggles=(TW + 90, TW + 108), studio_final=TW + 120)

VERSIONS = {
    "client": dict(out="Shawarma_Bakfar_Final.mp4", frames=TW, sync=SYNC_CLIENT, twist=False),
    "studio": dict(out="AI_NATI_Shawarma_Showreel.mp4", frames=TW + 132, sync=SYNC_STUDIO, twist=True),
}


# ----------------------------------------------------------- formats -----
# "reels": 9:16 1080x1920 (Reels / Stories / TikTok) - the layouts above.
# "fb45":  4:5 1080x1350, Meta's recommended Facebook/Instagram FEED format.
#          Every shot is reframed (vertical window), every caption re-laid out.
ASPECT = 9 / 16
FORMATS = {
    "fb45": dict(
        H=1350, aspect=4 / 5,
        centers={"hook_drive": 0.42, "hook_freeze": 0.42, "soccer_kick": 0.42, "soccer_freeze": 0.42,
                 "coffee_pour": 0.48, "coffee_freeze": 0.48, "spit": 0.40, "tahini": 0.47,
                 "hero": 0.47, "endcard": 0.47},
        cues={"hook": dict(y=820, size=120), "time1": dict(y=1250, size=112), "time2": dict(y=1250, size=112),
              "opened1": dict(y=1045, size=116), "opened2": dict(y=1210, size=180),
              "on_the_way": dict(y=100, size=92), "closing": dict(y=1035, size=90),
              "if_stopped": dict(y=640, size=140), "it_worked": dict(y=640, size=230),
              "q1": dict(y=540, size=130), "q2": dict(y=770, size=116),
              "tagline": dict(y=705, size=90), "cta": dict(y=905, size=100)},
        client_endcard=dict(d=620, y=470), studio_logo=dict(y=390, width=760), handle=dict(y=1015),
    ),
}


def apply_format(name):
    """mutate the layout constants in place for a delivery format."""
    global H, ASPECT
    if name in (None, "reels"):
        return
    F = FORMATS[name]
    H, ASPECT = F["H"], F["aspect"]
    for seg in AD:
        if seg["name"] in F["centers"]:
            seg["center"] = (seg.get("center", (0.5, 0.5))[0], F["centers"][seg["name"]])
    for cue in AD_TEXT + TWIST_TEXT:
        cue.update(F["cues"].get(cue["id"], {}))
    CLIENT_ENDCARD.update(F["client_endcard"])
    STUDIO_LOGO.update(F["studio_logo"])
    HANDLE.update(F["handle"])


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
