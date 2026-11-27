# Shared timeline for the AI NATI STUDIOS "reality script" ad, version 2.
# Output: 1080x1920 at 30 fps. Source clips are 24 fps and are sampled frame-accurately
# (no motion interpolation, so faces are never re-synthesised).
# All times are in seconds on the output timeline. TIMING IS PROVISIONAL until the
# voice files arrive: every dialogue word time below is meant to be replaced by the
# real word timings of the recordings.
import random

FPS = 30
SRC_FPS = 24
W, H = 1080, 1920
TOTAL_FRAMES = 900  # 30.0 s

# (clip, first source frame at 24 fps, output start frame, output end frame, camera move)
SEGMENTS = [
    ("v1", 44, 0, 156, "static"),     # S1  0.000 to 5.200   opening prompt
    ("v2", 38, 156, 226, "roar"),     # S2a 5.200 to 7.533   lion roar, push and shake
    ("v2", 138, 226, 294, "deadpan"), # S2b 7.533 to 9.800   deadpan close-up in silence
    ("v3", 20, 294, 496, "erase"),    # S3  9.800 to 16.533  romance, snap zoom, erase
    ("v4", 0, 496, 669, "static"),    # S4  16.533 to 22.300 snap and reveal (untouched)
    ("v5", 0, 669, 900, "static"),    # S5  22.300 to 30.000 end card
]
CUT1 = 156 / FPS
CUT2A = 226 / FPS
CUT2 = 294 / FPS
CUT4 = 496 / FPS
CUT5 = 669 / FPS

T1 = "אישה אלגנטית יושבת בסלון יוקרתי."
T2 = "פתאום מופיע אריה ענק בסלון."
T3 = "גבר מסתורי נכנס לחייה."


def char_times(text, t0, t1, seed):
    """Per-character key times with a human jitter, fitted to [t0, t1]."""
    rnd = random.Random(seed)
    w = []
    for ch in text:
        base = 1.0 + rnd.uniform(-0.35, 0.35)
        if ch == " ":
            base *= 1.35
        w.append(base)
    tot = sum(w)
    out, acc = [], 0.0
    for x in w:
        out.append(t0 + (t1 - t0) * acc / tot)
        acc += x
    return out


def backspace_times(n, t0, t1, power=0.6):
    """Accelerating backspace, like a held key that speeds up."""
    return [t0 + (t1 - t0) * ((i / max(1, n - 1)) ** power) for i in range(n)]


# ---- S1 opening
TYPE1 = char_times(T1, 0.10, 1.25, 11)
SELECT_AT, CLEAR_AT = 3.70, 3.83
TYPE2 = char_times(T2, 3.87, 4.70, 12)
ENTER1 = 4.93

# ---- S2 lion
ROAR_A, ROAR_B = CUT1, 6.30          # roar takes, the second is cut dead on CUT2A
P2_SHOW = 8.85
TYPE3 = char_times(T3, 8.93, 9.38, 13)
ENTER2 = 9.57

# ---- S3 the mysterious man (comic peak)
ROMANCE_STOP = 11.60                 # her eyes land on the lens (clip 3 at 2.62 s)
SNAP_IN = (11.60, 11.75, 1.00, 1.20) # snap zoom onto her face
YEHUDA_PUSH = (12.60, 12.72, 1.20, 1.26)
ZOOM_OUT = (13.42, 13.70, 1.26, 1.00)
P3_SHOW = 11.82                      # prompt returns on the first "תמחק"
BKSP = backspace_times(len(T3), 12.05, 13.28)
P3_HIDE = 13.34
GLITCH0, GLITCH1 = 13.80, 14.03      # the man vanishes (clip 3 at 4.83 s)

# ---- S4 snap and reveal
SNAP_T = CUT4 + 0.35
IMPACT_T = CUT4 + 3.93               # music impact lands as the walls open

# ---- S5 end card
PULSE0, PULSE1 = 26.45, 26.95        # "אתם כן" pulse on the voice-over
CTA_IN = 26.95
FINAL_HIT = CUT4 + 11.85

# Dialogue: (marker, [[(word, highlight, start time)]], end time)
# highlight: None, "gold" (brand / punch), "coral" (panic), "cyan" (sarcasm)
DIALOGUE = [
    ("d1", [[("אלגנטית?", "cyan", 2.20), ("התחלת", None, 2.85), ("טוב.", None, 3.08)]], 3.60),
    ("d2", [[("אריה?", None, 7.85), ("איזה", None, 8.32), ("מקורי…", "cyan", 8.52)]], 9.00),
    ("d3", [[("תמחק,", "coral", 11.80), ("תמחק!", "coral", 12.10)],
            [("יהודה", "gold", 12.60), ("רואה", None, 12.86), ("את", None, 13.02), ("זה!", None, 13.12)]], 13.45),
    ("d4", [[("טוב,", None, 14.30), ("מספיק!", None, 14.52)],
            [("תן", None, 15.05), ("לי", None, 15.18), ("לכתוב", None, 15.33), ("את", None, 15.60), ("התסריט.", "gold", 15.76)]], 16.40),
    ("d5", [[("עכשיו", None, 22.45), ("אנחנו", None, 22.72), ("מדברים!", "gold", 23.00)]], 23.70),
]
VO_SLOT = ("vo", 23.95, 26.90)  # "אצלנו המציאות לא קובעת את התסריט. אתם כן."

# End card copy and timing
CTA_HEAD = [("יש", 26.95), ("לכם", 27.04), ("רעיון", 27.13), ("לסרט?", 27.24)]
CTA_LINE2 = [("בואו", 27.40), ("נהפוך", 27.49), ("אותו", 27.58), ("למציאות.", 27.72)]
SERVICES = ["סרטים אישיים", "פרסומות", "הזמנות לאירועים"]
SERVICES_IN = 27.95
SOCIALS = [("instagram", "@ainati_studios", 28.08), ("facebook", "AI NATI STUDIOS", 28.20),
           ("tiktok", "@einat.cohen.elyas", 28.32)]
