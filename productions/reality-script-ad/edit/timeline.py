# Shared timeline for the AI NATI STUDIOS "reality script" ad, version 3.
# Output 1080x1920 at 30 fps. Source clips are 24 fps and are sampled frame-accurately
# (no interpolation, faces are never re-synthesised).
# TIMING IS PROVISIONAL until the voice files arrive: dialogue word times are placeholders.
import random

FPS = 30
SRC_FPS = 24
W, H = 1080, 1920


def char_times(text, t0, t1, seed):
    rnd = random.Random(seed)
    w = [(1.35 if ch == " " else 1.0) * (1.0 + rnd.uniform(-0.35, 0.35)) for ch in text]
    tot, acc, out = sum(w), 0.0, []
    for x in w:
        out.append(t0 + (t1 - t0) * acc / tot)
        acc += x
    return out


def backspace_times(n, t0, t1, power=0.6):
    return [t0 + (t1 - t0) * ((i / max(1, n - 1)) ** power) for i in range(n)]


def f30(t):
    """Snap a time to the 30 fps output grid."""
    return round(t * FPS) / FPS


T1 = "אישה אלגנטית יושבת בסלון יוקרתי."
T2 = "פתאום מופיע אריה ענק בסלון."
T3 = "גבר מסתורי נכנס לחייה."

# ------------------------------------------------------------------ S1 the elegant woman
V1_IN = 1.90                 # clip 1 start
V1_BLINK = 7.71              # eyes closed: the cut to clip 2 hides here
CUT_A = f30(V1_BLINK - V1_IN)            # 6.10  clip 1 -> clip 2 (matched framing)
TYPE1 = char_times(T1, 0.10, 1.25, 11)
SELECT_AT = 4.50
CLEAR_AT = 4.62
TYPE2 = char_times(T2, 4.66, 5.50, 12)
PUSH1 = (4.50, CUT_A)        # slow push on clip 1 while the lion prompt is typed
ENTER1 = 7.00                # after 1.5 s of reading
REVEAL = (7.06, 7.66)        # pull back from her face, the lion is revealed

# ------------------------------------------------------------------ S2 lion
V2_IN = 0.30
V2_ROAR_END = 3.00
CUT_B = f30(REVEAL[1] + 0.84)               # deadpan close-up
V2_ROAR_END = V2_IN + (CUT_B - CUT_A)
ROAR_ON = REVEAL[0] + 0.03
V2B_IN = 5.55                # she turns from the lion to the lens
V2B_TURN = 8.00              # play forward to here, then hold by running back
P2_SHOW = CUT_B + 1.80
TYPE3 = char_times(T3, P2_SHOW + 0.08, P2_SHOW + 0.78, 13)
ENTER2 = TYPE3[-1] + 1.50    # 1.5 s of reading
CUT_C = f30(ENTER2 + 0.15)

# ------------------------------------------------------------------ S3 the mysterious man
V3_IN = 1.00
V3_LOOK = 2.62               # her eyes land on the lens
HOLD_A, HOLD_B = 3.00, 3.40  # her frozen stare: play to B, run back to A, play on
V3_ERASE = 4.79              # last clean frame before the generated vanish (bouquet still)
V3_AFTER = 5.42              # first clean frame after the vanish
ERASE_DUR = 8 / FPS
LOOK_T = f30(CUT_C + (V3_LOOK - V3_IN))
S3B_T = f30(CUT_C + (HOLD_B - V3_IN))                    # start of the run back
S3C_T = f30(S3B_T + (HOLD_B - HOLD_A))                   # forward again from HOLD_A
ERASE_T = f30(S3C_T + (V3_ERASE - HOLD_A))               # digital erase starts
S3E_T = f30(ERASE_T + ERASE_DUR)                         # clean room, she is alone
SNAP_IN = (LOOK_T, LOOK_T + 0.15, 1.00, 1.20)
YEHUDA_T = f30(LOOK_T + 1.03)
YEHUDA_PUSH = (YEHUDA_T, YEHUDA_T + 0.12, 1.20, 1.26)
ZOOM_OUT = (ERASE_T - 0.42, ERASE_T - 0.05, 1.26, 1.00)
P3_SHOW = LOOK_T + 0.13
BKSP = backspace_times(len(T3), YEHUDA_T + 0.05, ERASE_T - 0.12)
V3_OUT = 7.72
PIX_OUT = 0.13               # clip 3 breaks into blocks ...
PIX_SWAP = 0.17              # ... blocks of the new reality switch in, laptop first ...
PIX_IN = 0.17                # ... and clip 4 sharpens just before the snap
CUT_D = f30(S3E_T + (V3_OUT - V3_AFTER))

# ------------------------------------------------------------------ S4 snap and reveal
V4_REVEAL = 3.40             # the castle world opens up
V4_OUT = 3.90                # shortened: no lingering once the world is revealed
SNAP_T = CUT_D + 0.35
IMPACT_T = CUT_D + V4_REVEAL
CUT_E = f30(CUT_D + V4_OUT)
MUSIC_FINALE_START = IMPACT_T - 3.93     # finale cue: impact at 3.93 s, final hit at 11.85 s
FINAL_HIT = MUSIC_FINALE_START + 11.85

# ------------------------------------------------------------------ S5 end card
X = CUT_E
VO_SLOT = ("vo", X + 1.62, X + 4.42)     # "אצלנו המציאות לא קובעת את התסריט. אתם כן."
PULSE0, PULSE1 = X + 3.92, X + 4.42      # "אתם כן" pulse
CTA_IN = X + 4.52
SLATE_T = f30(FINAL_HIT - 0.50)          # slate opens, the last network row lands on the final hit
SLATE_HOLD = 4.0                         # contact details fully on screen at least this long
SOC_T0 = SLATE_T + 0.20
SOC_STAGGER = 0.15
END_T = f30(SOC_T0 + 2 * SOC_STAGGER + 0.25 + SLATE_HOLD)
TOTAL_FRAMES = int(round(END_T * FPS))

CTA_HEAD = [("יש", 0.00), ("לכם", 0.09), ("רעיון", 0.18), ("לסרט?", 0.29)]
CTA_LINE2 = [("בואו", 0.50), ("נהפוך", 0.59), ("אותו", 0.68), ("למציאות.", 0.82)]
SERVICES = ["סרטים אישיים", "פרסומות", "הזמנות לאירועים"]
SOCIALS = [("instagram", "@ainati_studios"), ("facebook", "AI NATI STUDIOS"), ("tiktok", "@einat.cohen.elyas")]

# ------------------------------------------------------------------ dialogue (placeholders until the voice)
# (slot, [[(word, colour, start)]], end, style)   colour: None | "teal" | "gold" | "coral"
DIALOGUE = [
    ("d1", [[("אלגנטית?", "teal", 2.00), ("התחלת", None, 3.65), ("טוב.", None, 3.88)]], 4.42, None),
    ("d2", [[("אריה?", None, CUT_B + 0.30), ("איזה", None, CUT_B + 0.74), ("מקורי…", "teal", CUT_B + 0.93)]], CUT_B + 1.60, None),
    ("d3a", [[("תמחק,", "coral", LOOK_T + 0.08), ("תמחק!", "coral", LOOK_T + 0.38)]], YEHUDA_T - 0.10, "shake"),
    ("d3b", [[("יהודה", "gold", YEHUDA_T), ("רואה", None, YEHUDA_T + 0.27),
              ("את", None, YEHUDA_T + 0.43), ("זה!", None, YEHUDA_T + 0.55)]], S3E_T + 0.12, None),
    ("d4", [[("טוב,", None, S3E_T + 0.10), ("מספיק!", None, S3E_T + 0.33)],
            [("תן", None, S3E_T + 0.80), ("לי", None, S3E_T + 0.93), ("לכתוב", None, S3E_T + 1.08),
             ("את", None, S3E_T + 1.35), ("התסריט.", "gold", S3E_T + 1.50)]], CUT_D - 0.22, None),
    ("d5", [[("עכשיו", None, X + 0.15), ("אנחנו", None, X + 0.42), ("מדברים!", "gold", X + 0.70)]], X + 1.42, None),
]

# ------------------------------------------------------------------ edit list
# Each entry: (clip, output start, output end, source time function name, camera)
# source time functions are evaluated in video.py
SEGMENTS = [
    ("v1", 0.0, CUT_A, ("lin", V1_IN), "s1"),
    ("v2", CUT_A, CUT_B, ("lin", V2_IN), "s2"),
    ("v2", CUT_B, CUT_C, ("pingpong", V2B_IN, V2B_TURN), "deadpan"),
    ("v3", CUT_C, S3B_T, ("lin", V3_IN), "s3"),
    ("v3", S3B_T, S3C_T, ("rev", HOLD_B), "s3"),
    ("v3", S3C_T, ERASE_T, ("lin", HOLD_A), "s3"),
    ("v3", ERASE_T, S3E_T, ("hold", V3_ERASE), "s3"),
    ("v3", S3E_T, CUT_D, ("lin", V3_AFTER), "s3"),
    ("v4", CUT_D, CUT_E, ("lin", 0.0), "static"),
    ("v5", CUT_E, END_T, ("clamp", 0.0, 8.0), "static"),
]
