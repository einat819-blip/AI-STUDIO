# Shared timeline for AI NATI STUDIOS ad (approval cut). Times in seconds, 24 fps.
import random
FPS = 24
W, H = 1080, 1920
TOTAL_FRAMES = 720  # 30.0 s

# (clip, first source frame, number of frames, punch-in zoom start, zoom end)
SEGMENTS = [
    ("v1", 44, 125, 1.0, 1.0),    # S1  0.000 - 5.208
    ("v2", 38, 56, 1.0, 1.0),     # S2a 5.208 - 7.542  lion roar
    ("v2", 138, 54, 1.10, 1.16),  # S2b 7.542 - 9.792  deadpan, slow push
    ("v3", 20, 162, 1.0, 1.0),    # S3  9.792 - 16.542 romance / erase
    ("v4", 0, 138, 1.0, 1.0),     # S4  16.542 - 22.292 snap / reveal
    ("v5", 0, 185, 1.0, 1.0),     # S5  22.292 - 30.000 end card
]
assert sum(s[2] for s in SEGMENTS) == TOTAL_FRAMES

T1 = "אישה אלגנטית יושבת בסלון יוקרתי."
T2 = "פתאום מופיע אריה ענק בסלון."
T3 = "גבר מסתורי נכנס לחייה."
CTA1 = "יש לכם רעיון לסרט?"
CTA2 = "בואו נהפוך אותו למציאות."

def char_times(text, t0, t1, seed):
    """Per-character key times with human-ish jitter, fitted to [t0, t1]."""
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

def backspace_times(n, t0, t1):
    """Accelerating backspace (key repeat speeding up)."""
    out = []
    for i in range(n):
        u = i / max(1, n - 1)
        out.append(t0 + (t1 - t0) * (u ** 0.6))
    return out

TYPE1 = char_times(T1, 0.125, 1.33, 11)
SELECT_AT, CLEAR_AT = 3.70, 3.83
TYPE2 = char_times(T2, 3.875, 4.75, 12)
ENTER1 = 4.96
CUT1 = 125 / FPS

P2_SHOW = 8.85
TYPE3 = char_times(T3, 8.95, 9.42, 13)
ENTER2 = 9.58
CUT2 = 235 / FPS

P3_SHOW = 12.70
BKSP = backspace_times(len(T3), 12.95, 13.72)
GLITCH0, GLITCH1 = 331 / FPS, 338 / FPS
P3_HIDE = 14.04

SNAP_T = 397 / FPS + 0.35
CUT4 = 397 / FPS
CUT5 = 535 / FPS

PULSE0, PULSE1 = 26.45, 26.95
P4_SHOW = 26.95
TYPE_CTA1 = char_times(CTA1, 27.05, 27.50, 21)
TYPE_CTA2 = char_times(CTA2, 27.62, 28.25, 22)
INFO_IN = 28.39

# Dialogue slots: (start, end, lines[[(word, highlight)]], marker)
#   highlight: None | "gold" | "coral"
DIALOGUE = [
    (2.20, 3.60, [[("אלגנטית?", "gold"), ("התחלת", None), ("טוב.", None)]], "דיאלוג 1"),
    (7.85, 9.05, [[("אריה?", None), ("איזה", None), ("מקורי…", "gold")]], "דיאלוג 2"),
    (11.70, 13.68, [[("תמחק,", "coral"), ("תמחק!", "coral")],
                    [("יהודה", "gold"), ("רואה", None), ("את", None), ("זה!", None)]], "דיאלוג 3"),
    (14.35, 16.45, [[("טוב,", None), ("מספיק!", None)],
                    [("תן", None), ("לי", None), ("לכתוב", None), ("את", None), ("התסריט.", "gold")]], "דיאלוג 4"),
    (22.44, 23.74, [[("עכשיו", None), ("אנחנו", None), ("מדברים!", "gold")]], "דיאלוג 5"),
]
VO_SLOT = (23.95, 26.90, "קריינות הסיום")
