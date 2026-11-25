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
# v4: final order. The approved run (rural road ... "אבל האדום שלו כבר עובד") plays first and the
# left-turn segment closes the film on "סעו בזהירות!" + a held frame + hard cut.
# End card and its narration are removed. Subtitles are re-timed from a real transcription of both
# narration files (Whisper turbo and large-v3 agree) plus measured word onsets.
# =====================================================================================
VO_SEGS = VO_SEGS[:-1]                       # drop "צומת מעון. העתיד ירוק. ההווה פחות."
TITLES = []
SHOTS = [s_ for s_ in SHOTS if s_['kind'] != 'endcard']
# three approved cuts moved onto the measured word onsets ("חיילים", "ומשאיות", "לצומת"); content unchanged
_RETIME = {4.80: 4.74, 5.52: 5.46, 8.42: 8.30}
for s_ in SHOTS:
    s_['t0'] = _RETIME.get(s_['t0'], s_['t0'])
    s_['t1'] = _RETIME.get(s_['t1'], s_['t1'])

# main narration: (onset, end) in source seconds, measured
_CHUNKS = [
    (0.00, 1.66, "איך מתכננים צומת בעוטף?", {}),
    (2.18, 3.13, "קחו כביש אחד.", {"אחד.": YEL}),
    (3.36, 4.74, "תכניסו אליו תושבים,", {}),
    (4.74, 5.46, "חיילים", {}),
    (5.46, 7.08, "ומשאיות לכרם שלום.", {}),
    (7.33, 8.30, "תנקזו את כולם", {}),
    (8.30, 9.10, "לצומת אחת.", {"אחת.": YEL}),
    (9.51, 10.52, "תוסיפו עבודות!", {"עבודות!": YEL}),
    (10.84, 12.13, "ותאריך סיום", {}),
    (12.13, 13.83, "שלא נראה באופק...", {}),
    (14.20, 15.17, "והנה לכם", {}),
    (15.17, 16.33, "הפלא ההנדסי", {"הפלא": YEL, "ההנדסי": YEL}),
    (16.33, 17.67, "של צומת מעון!", {}),
    (17.92, 19.68, "רמזור שעוד לא הותקן...", {}),
    (20.12, 20.62, "אבל", {}),
    (20.62, 21.66, "אבל האדום שלו", {"האדום": RED}),
    (21.67, 22.36, "כבר עובד.", {}),
]
SPEECH = [(d(a), d(b - 1e-3), t, hl) for a, b, t, hl in _CHUNKS]

S0 = T_END                                   # 24.95: after the hold on the family + hopeless honk
VO2_SEGS = [
    (0.00, 2.40, 0.25),      # מגיעים מאופקים ורוצים לפנות שמאלה?
    (2.40, 5.66, 0.25),      # אין בעיה! זה ייקח לכם רק חמישים דקות!
    (5.66, 7.24, 0.75),      # אבל בסוף תצליחו!      (+0.5: a beat on the locked 50:00)
    (7.24, 10.58, 0.75),     # בתנאי שלא חתכו אתכם בדרך ונכנסו לכם באוטו.
    (10.58, 11.96, 0.90),    # סעו בזהירות!          (+0.15: a beat on her shock)
]


def d2(src_t):
    for a, b, off in VO2_SEGS:
        if a <= src_t < b:
            return round(S0 + src_t + off, 3)
    return round(S0 + src_t + VO2_SEGS[-1][2], 3)


_CHUNKS2 = [
    (0.05, 1.05, "מגיעים מאופקים", {}),
    (1.05, 2.33, "ורוצים לפנות שמאלה?", {}),
    (2.51, 3.50, "אין בעיה!", {}),
    (3.56, 4.29, "זה ייקח לכם", {}),
    (4.29, 5.54, "רק חמישים דקות!", {"רק": YEL, "חמישים": YEL, "דקות!": YEL}),
    (5.80, 7.14, "אבל בסוף תצליחו!", {}),
    (7.40, 8.16, "בתנאי שלא", {}),
    (8.16, 9.24, "חתכו אתכם בדרך", {"חתכו": RED}),              # twist word only once spoken
    (9.24, 10.48, "ונכנסו לכם באוטו.", {}),
    (10.80, 11.77, "סעו בזהירות!", {}),
]
SPEECH = sorted(SPEECH + [(d2(a), d2(b - 1e-3), t, hl) for a, b, t, hl in _CHUNKS2])

SEG_L = round((d2(11.67) + 1.0 - S0) * FPS) / FPS     # last word + ~1 s held frame, whole frames
DURATION = round(S0 + SEG_L, 4)
N_WATCH = S0 + 2.65                          # "אין בעיה!": the 50-minute wait (watch close-up)
N_TURN = S0 + 5.85                           # signals, looks around, then goes
N_CUT = d2(8.16)                             # "חתכו" (measured onset): hard cut, white SUV, brakes
N_SHOCK = S0 + 11.55                         # "סעו בזהירות!": shock -> despair -> disbelief, held
SHOTS += [
    dict(t0=S0, t1=N_WATCH, kind="clip", clip=9, src=0.00, zoom=(1.00, 1.04), center=(0.50, 0.50)),
    dict(t0=N_WATCH, t1=N_TURN, kind="clip", clip=8, src=0.00, speed=3.10 / (N_TURN - N_WATCH), zoom=(1.00, 1.05), center=(0.42, 0.50)),
    dict(t0=N_TURN, t1=N_CUT, kind="clip", clip=9, src=2.60, speed=(6.04 - 2.60) / (N_CUT - N_TURN), zoom=(1.00, 1.00), center=(0.50, 0.50)),
    dict(t0=N_CUT, t1=N_SHOCK, kind="clip", clip=10, src=0.00, zoom=(1.00, 1.03), center=(0.45, 0.50)),
    dict(t0=N_SHOCK, t1=DURATION, kind="clip", clip=10, src=6.03 - (DURATION - N_SHOCK), zoom=(1.12, 1.17), center=(0.38, 0.45)),
]
SHOTS.sort(key=lambda s_: s_['t0'])

COUNTER = dict(t_start=N_WATCH + 0.05, t_lock=d2(4.60), t_end=N_TURN, pos=(540, 360))
BLINK9_ON = [0.0, 0.875, 1.583, 2.25, 3.0, 3.667, 4.333]
BLINK_P = 0.70

for k_ in ('final_chord',):
    MARKS.pop(k_, None)
MARKS.update(
    end_music=S0,                             # music comes back with the segment
    seg_in=S0, seg_out=DURATION,
    counter_start=COUNTER['t_start'], counter_lock=COUNTER['t_lock'],
    victory_build=d2(5.83), victory_hit=d2(7.04) + 0.03, victory_cut=N_CUT,
    squeal=N_CUT + 0.06,
    blinker_only=d2(11.67) + 0.05,            # from here only the turn signal is heard
)

# v4.1: the work-site beat ("תוסיפו עבודות!") uses the dedicated clip supplied for it (clip11:
# excavator + foreman spreading his arms). Same in/out times as before, nothing else moves.
_w0, _w1 = 9.87, T_DATE
SHOTS = [s_ for s_ in SHOTS if not (_w0 - 1e-6 <= s_['t0'] < _w1 - 1e-6)]
SHOTS.append(dict(t0=_w0, t1=_w1, kind="clip", clip=11, src=1.95, zoom=(1.00, 1.04), center=(0.50, 0.50)))
SHOTS.sort(key=lambda s_: s_['t0'])
