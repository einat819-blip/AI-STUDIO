# Shared timeline for the AI NATI STUDIOS "reality script" ad, version 3.
# Output 1080x1920 at 30 fps. Source clips are 24 fps and are sampled frame-accurately
# (no interpolation, faces are never re-synthesised).
# TIMING IS PROVISIONAL until the voice files arrive: dialogue word times are placeholders.
import json, os, random

_WORK = os.environ.get('AINATI_WORK', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.work'))
try:
    VO = json.load(open(os.path.join(_WORK, 'vo', 'lines.json')))
except FileNotFoundError:
    VO = {}
VO_PLACE = {}                # slot -> edit time where its clip starts


def vo_dur(slot, fallback):
    return VO[slot]['dur'] if slot in VO else fallback


def vo_words(slot, t0, fallback):
    """Word start times on the edit timeline: from the recording when we have it, else the placeholder."""
    if slot not in VO:
        return fallback
    VO_PLACE[slot] = t0
    return [t0 + w[1] for w in VO[slot]['words']]

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
D1A_T, D1B_T = 2.00, 3.55   # "אלגנטית?" while she looks up, "התחלת טוב." on the smirk to camera
D1_W = vo_words('d1a', D1A_T, [2.00]) + vo_words('d1b', D1B_T, [3.65, 3.88])
D1_END = (D1B_T + vo_dur('d1b', 0.9))
SELECT_AT = D1_END + 0.08
CLEAR_AT = SELECT_AT + 0.12
TYPE2 = char_times(T2, CLEAR_AT + 0.04, CLEAR_AT + 0.88, 12)
PUSH1 = (SELECT_AT, CUT_A)   # slow push on clip 1 while the lion prompt is typed
ENTER1 = TYPE2[-1] + 1.50    # after 1.5 s of reading
REVEAL = (ENTER1 + 0.06, ENTER1 + 0.66)   # pull back from her face, the lion is revealed

# ------------------------------------------------------------------ S2 lion
V2_IN = 0.30
V2_ROAR_END = 3.00
CUT_B = f30(REVEAL[1] + 0.84)               # deadpan close-up
V2_ROAR_END = V2_IN + (CUT_B - CUT_A)
ROAR_ON = REVEAL[0] + 0.03
V2B_IN = 5.55                # she turns from the lion to the lens
V2B_TURN = 8.00              # play forward to here, then hold by running back
D2A_T = CUT_B + 0.25         # "אריה?" as she settles on the lens
D2_W = vo_words('d2a', D2A_T, [CUT_B + 0.30])
D2B_T = D2A_T + vo_dur('d2a', 0.45) + 0.25   # a dry beat before "איזה מקורי"
D2_W += vo_words('d2b', D2B_T, [CUT_B + 0.74, CUT_B + 0.93])
D2_END = D2B_T + vo_dur('d2b', 0.9)
P2_SHOW = D2_END + 0.16      # the next prompt only after the lion punch has landed
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
NOTIF_T = VS6 + 2.35         # alert sound and the resignation notice (kept after her line, see below)
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

# ------------------------------------------------------------------ dialogue (word times from the recording, placeholders where a line is missing)
# (slot, [[(word, colour, start)]], end, style)   colour: None | "teal" | "gold" | "coral"
D3A_W = vo_words('d3a', LOOK_T + 0.08, [LOOK_T + 0.08, LOOK_T + 0.38])
D3B_W = vo_words('d3b', YEHUDA_T, [YEHUDA_T, YEHUDA_T + 0.27, YEHUDA_T + 0.43, YEHUDA_T + 0.55])
D4_W = vo_words('d4', VS6 + 0.15, [VS6 + 0.15, VS6 + 0.38, VS6 + 0.85, VS6 + 0.98, VS6 + 1.13, VS6 + 1.40, VS6 + 1.55])
D4_END = VS6 + 0.15 + vo_dur('d4', 2.0)
D7A_W = vo_words('d7a', VS7 + 0.40, [VS7 + 0.40, VS7 + 0.55, VS7 + 0.72, VS7 + 0.97])
D7A_END = VS7 + 0.40 + vo_dur('d7a', 1.3)
D7B_T = max(VS7 + 1.90, D7A_END + 0.12)
BRAND_W = vo_words('brand', SLIDE['logo'] + 0.05, [])
# not in the current take: captions only, at the placeholder timing, until the recording arrives
D6_W = vo_words('d6', VS6 + 4.45, [VS6 + 4.45, VS6 + 4.65, VS6 + 5.35, VS6 + 5.52, VS6 + 5.72, VS6 + 5.85])
if 'd6' in VO:
    MUSIC_STOP = D6_W[2] - 0.15   # the music drops out right before "אני קשה עם ספקים."
D7B_W = vo_words('d7b', D7B_T, [D7B_T, D7B_T + 0.35, D7B_T + 0.50, D7B_T + 0.85, D7B_T + 1.15])
D7B_END = max(VS7 + 3.80, D7B_T + vo_dur('d7b', 0) + 0.10)

DIALOGUE = [
    ("d1", [[("אלגנטית?", "teal", D1_W[0]), ("התחלת", None, D1_W[1]), ("טוב.", None, D1_W[2])]], D1_END + 0.15, None),
    ("d2", [[("אריה?", None, D2_W[0]), ("איזה", None, D2_W[1]), ("מקורי…", "teal", D2_W[2])]], D2_END + 0.15, None),
    ("d3a", [[("תמחק,", "coral", D3A_W[0]), ("תמחק!", "coral", D3A_W[1])]], YEHUDA_T - 0.10, "shake"),
    ("d3b", [[("יהודה", "gold", D3B_W[0]), ("רואה", None, D3B_W[1]),
              ("את", None, D3B_W[2]), ("זה!", None, D3B_W[3])]], S3E_T + 0.02, None),
    ("d4", [[("טוב,", None, D4_W[0]), ("מספיק!", None, D4_W[1])],
            [("תן", None, D4_W[2]), ("לי", None, D4_W[3]), ("לכתוב", None, D4_W[4]),
             ("את", None, D4_W[5]), ("התסריט.", "gold", D4_W[6])]], D4_END + 0.12, None),
    ("d6", [[("מה", None, D6_W[0]), ("לעשות?", None, D6_W[1])],
            [("אני", None, D6_W[2]), ("קשה", None, D6_W[3]), ("עם", None, D6_W[4]), ("ספקים.", "gold", D6_W[5])]],
     VS6 + 6.42, None),
    ("d7a", [[("יש", None, D7A_W[0]), ("לכם", None, D7A_W[1]), ("רעיון", "teal", D7A_W[2]), ("לסרט?", "teal", D7A_W[3])]],
     D7A_END + 0.08, None),
    ("d7b", [[("תשאירו", "teal", D7B_W[0]), ("את", None, D7B_W[1]), ("העבודה", None, D7B_W[2])],
             [("הקשה", None, D7B_W[3]), ("לי.", "teal", D7B_W[4])]], D7B_END, None),
]

# ------------------------------------------------------------------ edit list
# Each entry: (clip, output start, output end, source time function name, camera)
# source time functions are evaluated in video.py
SEGMENTS = [
    ("v1", 0.0, CUT_A, ("lin", V1_IN), "s1"),
    ("v2", CUT_A, CUT_B, ("lin", V2_IN), "s2"),
    ("v2", CUT_B, CUT_C, ("pingpong", V2B_IN, V2B_TURN, 6.05), "deadpan"),
    ("v3", CUT_C, S3B_T, ("lin", V3_IN), "s3"),
    ("v3", S3B_T, S3C_T, ("rev", HOLD_B), "s3"),
    ("v3", S3C_T, ERASE_T, ("lin", HOLD_A), "s3"),
    ("v3", ERASE_T, S3E_T, ("hold", V3_ERASE), "s3"),
    ("v3", S3E_T, VS6, ("lin", V3_AFTER), "s3"),
    ("v6", VS6, VS7, ("lin", 0.0), "s6"),
    ("v7", VS7, END_T, ("clamp", 0.0, 8.0), "s7"),
]
