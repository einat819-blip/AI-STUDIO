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
CUT_D = None                 # the laptop / fantasy section is gone in this version
PIX_OUT = PIX_SWAP = PIX_IN = 0.0

# ------------------------------------------------------------------ new ending: the AI resigns
V3_TAIL = 0.20               # her open palm right after the erase: the cut on action into clip 6
VS6 = f30(S3E_T + V3_TAIL)   # clip 6: both palms up
NOTIF_T = VS6 + 2.35         # alert sound and the resignation notice
MUSIC_STOP = VS6 + 5.20      # the music drops out before the punch
PUSH = (f30(VS6 + 6.45), f30(VS6 + 6.85))   # push in on her eyes, into the close-up
VS7 = PUSH[1]                # clip 7: the personal close-up
EYES_V6 = (328, 596)         # eye midpoint, clip 6 at 6.5 s (source px)
EYES_V7 = (382, 498)         # eye midpoint, clip 7 at 0.0 s
PUSH_ZOOM = 1.74             # interocular distance ratio clip 7 / clip 6

# ------------------------------------------------------------------ music for the close-up and the end slide
M6_IN, M6_PEAK, M6_LOOP_S, M6_LOOP_E, M6_HIT = 2.54, 7.37, 8.38, 10.42, 11.68
T_SHAPES = f30(VS7 + 4.43)                   # colour shapes sweep in exactly on the peak
M6_START = T_SHAPES - (M6_PEAK - M6_IN)      # starts softly right after the punch
FINAL_HIT = T_SHAPES + (M6_HIT - M6_PEAK) + (M6_LOOP_E - M6_LOOP_S)
END_T = f30(FINAL_HIT + 0.45)
TOTAL_FRAMES = int(round(END_T * FPS))
EIGHTH = 0.254
SLIDE = dict(logo=T_SHAPES + 1 * EIGHTH, tag1=T_SHAPES + 3 * EIGHTH, tag2=T_SHAPES + 4 * EIGHTH,
             serv=T_SHAPES + 5 * EIGHTH, cta=T_SHAPES + 6 * EIGHTH)
SOC_TIMES = [T_SHAPES + 7 * EIGHTH, T_SHAPES + 8 * EIGHTH, T_SHAPES + 9 * EIGHTH]

NOTICE = "הבינה המלאכותית מבקשת להתפטר."
TAG1, TAG2 = "אתם מדמיינים.", "אני מביימת."
SERVICES = ["סרטים אישיים", "פרסומות", "הזמנות לאירועים"]
CTA_PILL = "יש לכם רעיון? בואו נדבר."
SOCIALS = [("instagram", "@ainati_studios"), ("facebook", "AI NATI STUDIOS"), ("tiktok", "@einat.cohen.elyas")]

# ------------------------------------------------------------------ dialogue (placeholders until the voice)
# (slot, [[(word, colour, start)]], end, style)   colour: None | "teal" | "gold" | "coral"
DIALOGUE = [
    ("d1", [[("אלגנטית?", "teal", 2.00), ("התחלת", None, 3.65), ("טוב.", None, 3.88)]], 4.42, None),
    ("d2", [[("אריה?", None, CUT_B + 0.30), ("איזה", None, CUT_B + 0.74), ("מקורי…", "teal", CUT_B + 0.93)]], CUT_B + 1.60, None),
    ("d3a", [[("תמחק,", "coral", LOOK_T + 0.08), ("תמחק!", "coral", LOOK_T + 0.38)]], YEHUDA_T - 0.10, "shake"),
    ("d3b", [[("יהודה", "gold", YEHUDA_T), ("רואה", None, YEHUDA_T + 0.27),
              ("את", None, YEHUDA_T + 0.43), ("זה!", None, YEHUDA_T + 0.55)]], S3E_T + 0.02, None),
    ("d4", [[("טוב,", None, VS6 + 0.15), ("מספיק!", None, VS6 + 0.38)],
            [("תן", None, VS6 + 0.85), ("לי", None, VS6 + 0.98), ("לכתוב", None, VS6 + 1.13),
             ("את", None, VS6 + 1.40), ("התסריט.", "gold", VS6 + 1.55)]], VS6 + 2.15, None),
    ("d6", [[("מה", None, VS6 + 4.45), ("לעשות?", None, VS6 + 4.65)],
            [("אני", None, VS6 + 5.35), ("קשה", None, VS6 + 5.52), ("עם", None, VS6 + 5.72), ("ספקים.", "gold", VS6 + 5.85)]],
     VS6 + 6.42, None),
    ("d7a", [[("יש", None, VS7 + 0.40), ("לכם", None, VS7 + 0.55), ("רעיון", "teal", VS7 + 0.72), ("לסרט?", "teal", VS7 + 0.97)]],
     VS7 + 1.72, None),
    ("d7b", [[("תשאירו", "teal", VS7 + 1.90), ("את", None, VS7 + 2.25), ("העבודה", None, VS7 + 2.40)],
             [("הקשה", None, VS7 + 2.75), ("לי.", "teal", VS7 + 3.05)]], VS7 + 3.80, None),
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
    ("v3", S3E_T, VS6, ("lin", V3_AFTER), "s3"),
    ("v6", VS6, VS7, ("lin", 0.0), "s6"),
    ("v7", VS7, END_T, ("clamp", 0.0, 8.0), "s7"),
]
