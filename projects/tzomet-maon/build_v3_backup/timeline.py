# Timeline v2 for "צומת מעון": built on the real ElevenLabs narration (src/vo.mp3).
# Narration is split only inside its own silences and re-spaced with short pauses
# (time-lapse breath, comic pause before the punch). The words themselves are untouched.

FPS = 30
W, H = 1080, 1920

# ---- narration placement: (src_start, src_end, offset). dst = src + offset
VO_SEGS = [
    (0.00, 1.95, 0.00),    # איך מתכננים צומת בעוטף?
    (1.95, 3.20, 0.00),    # קחו כביש אחד.
    (3.20, 7.17, 0.00),    # תכניסו אליו תושבים, חיילים ומשאיות לכרם שלום.
    (7.17, 9.35, 0.00),    # תנקזו את כולם לצומת אחת.
    (9.35, 10.72, 0.35),   # תוסיפו עבודות!            (+0.35: let the honks breathe)
    (10.72, 14.00, 0.35),  # ותאריך סיום שלא נראה באופק...
    (14.00, 17.75, 1.65),  # והנה לכם הפלא ההנדסי של צומת מעון!   (+1.30: time-lapse)
    (17.75, 19.86, 1.65),  # רמזור שעוד לא הותקן...
    (19.86, 22.70, 2.10),  # אבל האדום שלו כבר עובד.   (+0.45: awkward silence)
    (22.70, 27.09, 2.10),  # צומת מעון. העתיד ירוק. ההווה פחות.
]


def d(src_t):
    """source narration time -> timeline time"""
    for a, b, off in VO_SEGS:
        if a <= src_t < b:
            return round(src_t + off, 3)
    return round(src_t + VO_SEGS[-1][2], 3)


YEL = (255, 214, 64)
RED = (255, 70, 58)
# subtitle chunks in SOURCE narration time (measured word onsets), converted below
_CHUNKS = [
    (0.00, 1.80, "איך מתכננים צומת בעוטף?", {}),
    (2.20, 3.20, "קחו כביש אחד.", {"אחד.": YEL}),
    (3.38, 4.80, "תכניסו אליו תושבים,", {}),
    (4.80, 5.50, "חיילים", {}),
    (5.50, 7.15, "ומשאיות לכרם שלום.", {}),
    (7.30, 8.40, "תנקזו את כולם", {}),
    (8.40, 9.30, "לצומת אחת.", {"אחת.": YEL}),
    (9.52, 10.70, "תוסיפו עבודות!", {"עבודות!": YEL}),
    (10.85, 12.13, "ותאריך סיום", {}),
    (12.13, 13.95, "שלא נראה באופק...", {}),
    (14.20, 15.33, "והנה לכם", {}),
    (15.33, 16.30, "הפלא ההנדסי", {"הפלא": YEL, "ההנדסי": YEL}),
    (16.30, 17.70, "של צומת מעון!", {}),
    (17.92, 19.75, "רמזור שעוד לא הותקן...", {}),
    (20.12, 20.62, "אבל", {}),
    (20.62, 21.65, "אבל האדום שלו", {"האדום": RED}),   # punch word only once it is spoken
    (21.65, 22.45, "כבר עובד.", {}),
]
SPEECH = [(d(a), d(b - 1e-3), t, hl) for a, b, t, hl in _CHUNKS]

TITLES = [
    (d(23.15), "צומת מעון", (255, 255, 255)),
    (d(24.26), "העתיד ירוק.", (64, 214, 96)),
    (d(25.73), "ההווה פחות.", (255, 66, 54)),
]
DURATION = round(TITLES[-1][0] + 2.85, 2)       # last title stays ~2.9 s

# ---- picture. clip numbers: 1 aerial, 2 jam master, 3 family between trucks, 4 soldiers,
# 5 truck driver, 6 work site (traffic light appears 1.1-4.3 s: never used), 7 base -> empty sky
T_WORKS = d(9.52)            # "תוסיפו עבודות!"
T_WORKS2 = 10.62             # second works angle (driver behind the barriers)
T_DATE = d(10.85)            # "ותאריך סיום"
T_SHELO = d(12.13)           # "שלא נראה"
T_OFEK = d(12.85)            # "באופק" -> time-lapse
T_BASE = 15.55               # cut to the concrete base, in the pause before "והנה לכם"
T_SKY = 19.55                # tilt lands on the empty sky, fanfare dies
T_ADOM = d(20.62)            # "האדום"
T_KVAR = d(21.70) - 0.02     # "כבר עובד."
T_END = 24.95                # end card

SHOTS = [
    dict(t0=0.00, t1=3.38, kind="still", clip=1, src=0.00, zoom=(1.00, 1.10), center=(0.50, 0.56)),
    dict(t0=3.38, t1=4.08, kind="clip", clip=2, src=0.00, zoom=(1.00, 1.02), center=(0.50, 0.55)),
    dict(t0=4.08, t1=4.80, kind="clip", clip=2, src=2.75, zoom=(1.22, 1.26), center=(0.60, 0.62)),
    dict(t0=4.80, t1=5.52, kind="clip", clip=4, src=0.00, zoom=(1.04, 1.07), center=(0.50, 0.45)),
    dict(t0=5.52, t1=7.25, kind="clip", clip=5, src=4.20, zoom=(1.00, 1.04), center=(0.55, 0.45)),
    dict(t0=7.25, t1=8.42, kind="clip", clip=2, src=3.90, zoom=(1.00, 1.02), center=(0.50, 0.50)),
    dict(t0=8.42, t1=T_WORKS, kind="clip", clip=3, src=0.15, zoom=(1.00, 1.04), center=(0.50, 0.50)),
    dict(t0=T_WORKS, t1=T_WORKS2, kind="clip", clip=6, src=0.00, speed=0.90, zoom=(1.30, 1.34), center=(0.70, 0.50)),
    dict(t0=T_WORKS2, t1=T_DATE, kind="clip", clip=7, src=0.90, zoom=(1.45, 1.50), center=(0.26, 0.48)),
    dict(t0=T_DATE, t1=T_SHELO, kind="clip", clip=5, src=0.75, zoom=(1.02, 1.08), center=(0.50, 0.42)),
    dict(t0=T_SHELO, t1=T_OFEK, kind="clip", clip=4, src=1.35, zoom=(1.06, 1.10), center=(0.50, 0.45)),
    dict(t0=T_OFEK, t1=T_BASE, kind="timelapse", clip=2, src=2.00, zoom=(1.00, 1.06), center=(0.50, 0.50)),
    dict(t0=T_BASE, t1=T_SKY, kind="clip", clip=7, src=0.00, zoom=(1.00, 1.00), center=(0.50, 0.50)),
    dict(t0=T_SKY, t1=T_ADOM, kind="clip", clip=7, src=4.00, speed=0.64, zoom=(1.00, 1.03), center=(0.50, 0.45)),
    dict(t0=T_ADOM, t1=T_KVAR, kind="clip", clip=6, src=4.60, zoom=(1.34, 1.38), center=(0.40, 0.42)),
    dict(t0=T_KVAR, t1=T_END, kind="clip", clip=3, src=4.86, zoom=(1.00, 1.02), center=(0.50, 0.50)),
    dict(t0=T_END, t1=DURATION, kind="endcard", clip=7, src=6.00, zoom=(1.12, 1.00), center=(0.50, 0.55)),
]
TITLE_Y = [600, 785, 945]
ENDCARD_DIM = 0.22

# ---- sound marks
MARKS = dict(
    birds_out=3.90,
    traffic_in=3.38,
    honk1=d(9.10), honk2=d(9.10) + 0.27,
    works_in=T_WORKS, works_out=T_DATE + 0.10,
    flourish_land=d(9.90),            # "עבודות"
    clock_in=T_DATE, timelapse_in=T_OFEK, timelapse_out=T_BASE - 0.15,
    roll_in=15.70, fanfare_in=d(15.33) - 0.08, fanfare_cut=T_SKY - 0.03,
    silence_out=T_ADOM,              # jam slams back on "האדום"
    honk_desperate=d(22.30) + 0.10,
    end_music=T_END,
    final_chord=d(26.62) + 0.15,
)

LOGO_POS = 'top-right'
DRAFT_LABEL = None


# =====================================================================================
# v3: "פנייה שמאלה מאופקים" insert. Placed after the approved "באופק..." time-lapse and
# before "והנה לכם". Everything from INS_AT on moves later by SEG_L, untouched.
# =====================================================================================
INS_AT = T_BASE              # 15.55: the cut from the time-lapse to the concrete base
SEG_L = 385 / 30             # 12.83 s: length of the insert, set by the real narration; whole frames so
                             # every approved shot after it lands on exactly the same frame grid as before


def sh(t):
    return round(t + SEG_L, 3) if t >= INS_AT - 1e-6 else t


VO_SEGS = [(a, b, off + (SEG_L if a + off >= INS_AT else 0)) for a, b, off in VO_SEGS]
SPEECH = [(sh(a), sh(b), txt, hl) for a, b, txt, hl in SPEECH]
TITLES = [(sh(a), txt, col) for a, txt, col in TITLES]
DURATION = sh(DURATION)
for s in SHOTS:
    if s['t0'] >= INS_AT - 1e-6:
        s['t0'], s['t1'] = sh(s['t0']), sh(s['t1'])
MARKS = {k: (sh(v) if k not in ('timelapse_out',) else v) for k, v in MARKS.items()}
T_BASE_OLD = T_BASE
T_BASE, T_SKY, T_ADOM, T_KVAR, T_END = sh(T_BASE), sh(T_SKY), sh(T_ADOM), sh(T_KVAR), sh(T_END)

S0 = INS_AT                  # insert starts here (absolute)
# narration 2 placement: (src_a, src_b, offset relative to S0)
VO2_SEGS = [
    (0.00, 2.40, 0.25),      # מגיעים מאופקים ורוצים לפנות שמאלה?
    (2.40, 5.66, 0.25),      # בקלי קלות! רק חמישים דקות.
    (5.66, 7.24, 0.25),      # ובסוף אפילו תצליחו לפנות!
    (7.24, 10.58, 0.25),     # אם לא חתכו אתכם ונכנסו בכם בדרך.
    (10.58, 11.96, 0.40),    # בהצלחה!   (+0.15: a beat on her shock)
]


def d2(src_t):
    for a, b, off in VO2_SEGS:
        if a <= src_t < b:
            return round(S0 + src_t + off, 3)
    return round(S0 + src_t + VO2_SEGS[-1][2], 3)


_CHUNKS2 = [
    (0.05, 1.15, "מגיעים מאופקים", {}),
    (1.15, 2.37, "ורוצים לפנות שמאלה?", {}),
    (2.50, 3.60, "בקלי קלות!", {}),
    (3.60, 5.60, "רק חמישים דקות.", {"רק": YEL, "חמישים": YEL, "דקות.": YEL}),
    (5.78, 6.61, "ובסוף אפילו", {}),
    (6.61, 7.35, "תצליחו לפנות!", {}),
    (7.40, 7.98, "אם לא", {}),
    (7.98, 8.50, "אם לא חתכו אתכם", {"חתכו": RED}),          # twist word only once spoken
    (8.50, 10.45, "ונכנסו בכם בדרך.", {}),
    (10.75, 11.90, "בהצלחה!", {}),
]
SPEECH = sorted(SPEECH + [(d2(a), d2(b - 1e-3), t, hl) for a, b, t, hl in _CHUNKS2])

# insert picture (absolute times)
N_WATCH = S0 + 3.70           # cut to the watch close-up
N_TURN = d2(5.78) - 0.10      # "ובסוף": she spots a gap and goes
N_CUT = d2(7.98)              # "חתכו": hard cut, white SUV, brakes
N_HELP = S0 + 11.00           # helpless look before "בהצלחה!"
SHOTS += [
    dict(t0=S0, t1=N_WATCH, kind="clip", clip=9, src=0.00, zoom=(1.00, 1.04), center=(0.50, 0.50)),
    dict(t0=N_WATCH, t1=N_TURN, kind="clip", clip=8, src=0.30, zoom=(1.00, 1.05), center=(0.42, 0.50)),
    dict(t0=N_TURN, t1=N_CUT, kind="clip", clip=9, src=3.95, speed=2.09 / (N_CUT - N_TURN), zoom=(1.00, 1.00), center=(0.50, 0.50)),
    dict(t0=N_CUT, t1=N_HELP, kind="clip", clip=10, src=0.00, zoom=(1.00, 1.03), center=(0.45, 0.50)),
    dict(t0=N_HELP, t1=S0 + SEG_L, kind="clip", clip=10, src=4.35, zoom=(1.12, 1.16), center=(0.38, 0.45)),
]
SHOTS.sort(key=lambda s: s['t0'])

# 50-minute counter: runs from "בקלי" and locks on 50:00 exactly on "חמישים"
COUNTER = dict(t_start=d2(2.55), t_lock=d2(4.00), t_end=d2(5.62), pos=(540, 360))

# turn-signal: visible blink onsets measured in clip9 (src seconds)
BLINK9_ON = [0.0, 0.875, 1.583, 2.25, 3.0, 3.667, 4.333]
BLINK_P = 0.70

MARKS.update(
    seg_in=S0, seg_out=S0 + SEG_L,
    counter_start=COUNTER['t_start'], counter_lock=COUNTER['t_lock'],
    victory_build=d2(5.78), victory_hit=d2(7.04) + 0.02, victory_cut=N_CUT,
    squeal=N_CUT + 0.06,
    jingle=d2(11.05),
)
