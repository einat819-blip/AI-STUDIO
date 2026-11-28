# -*- coding: utf-8 -*-
"""Edit decision list, v6: "משלוחים לכל חלקי הארץ*", rebuilt around the new
narration (ElevenLabs, 47.7 s) and the four new clips.

Structure (brief scenes in brackets):
  [1] the perfect ad, "אשכול?!" stops the music, awkward silence
  [2] VIP card: riser + fanfare, "הזכות להמתין" gets time to be read, no captions
  [3] once a week: jingle out on "באיזה יום?", clock, dry "אנחנו לא אוהבים להתחייב"
  [4] hero courier departs HQ: heroic score, applause; the line
      "בתוספת תשלום על האומץ של הנהג" is wiped in on the word, with the till
  [5] pickup point: her own effort sounds, the till on "אנחנו גובים עליו"
      + "ואם כל זה לא מתאים לכם..." on the adventure map, music runs down,
        "אנחנו פשוט לא מגיעים." (narration lines not in the brief's scene list)
      + "אבל אנחנו בישראל / מבחינה גיאוגרפית, כן / מבחינתנו..." on the flag
        and the distribution map
  [6] China -> Israel: rhythmic sub-shots, score builds to "והגיעה לישראל!",
      hard stop on the cut
  [7] control room (only version supplied): "אבל מכאן לאשכול? בואו לא נגזים."
      over the alarm, typing, beeps, tension music, error tone, short silence
  [8] CEO: calm office; 4.0 s left for his line (narration to be supplied)
  ending: the reveal billboard, "הפריפריה נמכרת בנפרד." on the end card, logo + tagline

Every VO line is placed by the absolute time of its first word (ABS below);
segment boundaries are frame-exact, so offsets are exact.

Graphics printed low in the new clips (hero banner, CEO line) sit inside the
TikTok/Reels bottom UI. They are lifted from the clip and placed higher; the
clip is framed so the original copy is out of shot.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _v6_vo import LINES  # noqa: E402

FPS = 30
W, H = 1080, 1920
DRAFT_LABEL = ""
PY_CLIPS = True
FINAL_CRF = 14
FINAL_PRESET = "veryslow"
LOSSLESS_INTERMEDIATES = True
TP_CEILING = -2.5

NARRATION_WAV = "source/audio/narration_v6.wav"
NARRATION_TRANSCRIPT = "edit/narration_v6_transcript.json"
NARRATION_WORDS = "edit/narration_v6_words.json"

C = "source/clips/"
# Sections of the plan to remove (absolute plan seconds), set by a variant file before exec.
CUT = globals().get("CUT", [])


def T(x, end=False):
    """plan time -> output time; None if x falls inside a removed section
    (with end=True a time inside a removed section maps to where it was cut)."""
    for a, b in CUT:
        if a <= x < b:
            if not end:
                return None
            x = a
            break
    return x - sum(b - a for a, b in CUT if b <= x)


GOLD = [dict(h=(8, 40), s_min=90, v_min=110)]
ORANGE_WHITE = [dict(h=(0, 22), s_min=150, v_min=150), dict(s_max=40, v_min=200)]

# (id, absolute start, segment dict without timing)
_PLAN = [
    ("1", 0.00, dict(src=C + "S01_courier_billboard.mp4", tin=0.00)),
    ("2", 3.07, dict(src=C + "S02_curly_orders_laptop.mp4", tin=3.75)),
    ("3", 4.43, dict(src=C + "S03_agent_shock_eshkol.mp4", tin=0.90, zoom=1.0, cx=0.60, cy=0.50,
                     zoom_to=1.30, cx_to=0.53, cy_to=0.33, zoom_t0=1.47, zoom_t1=1.63, ease="out")),
    ("4a", 8.80, dict(src=C + "S05a_agent_thumbs_up.mp4", tin=0.00, zoom=1.0, zoom_to=1.08, ease="linear")),
    ("vip", 10.15, dict(src=C + "S04_vip_card.mp4", tin=2.20, zoom=1.0, zoom_to=1.07, cy=0.45, cy_to=0.42,
                        ease="linear", patches=[dict(kind="soften", y0=880, feather=60, sigma=16, dark=0.45)])),
    ("5a", 13.95, dict(src=C + "S05a_agent_thumbs_up.mp4", tin=1.35)),
    ("5b", 15.45, dict(src=C + "S05a_agent_thumbs_up.mp4", tin=3.20)),
    ("5c", 16.37, dict(src=C + "S05a_agent_thumbs_up.mp4", tin=4.37, zoom=1.18, cx=0.47, cy=0.35)),
    ("6", 17.95, dict(src=C + "S06_hero_courier_departure.mp4", tin=0.25, zoom=1.26, cx=0.58, cy=0.397,
                      zoom_to=1.30, ease="linear",
                      patches=[dict(kind="reveal", rect=(20, 1090, 692, 1166), t=1.85, wipe=0.35)],
                      lift=dict(rect=(0, 985, 704, 1185), accents=GOLD, keep_n=1, width=1000, y=1190))),
    ("7", 22.05, dict(src=C + "S07_pickup_point_boxes.mp4", tin=1.00)),
    ("8", 25.75, dict(src=C + "S08_courier_binoculars_map.mp4", tin=0.25)),
    ("9", 31.35, dict(src=C + "S09_curly_israel_flag.mp4", tin=1.85)),
    ("10", 32.95, dict(src=C + "S10_agent_distribution_map.mp4", tin=0.53, zoom=1.12, cx=0.60, cy=0.48,
                       zoom_to=1.45, cx_to=0.66, cy_to=0.55, zoom_t0=1.85, zoom_t1=2.35, ease="inout")),
    ("11a", 37.55, dict(src=C + "S11_package_world_journey.mp4", tin=0.00, zoom=1.0, zoom_to=1.06, ease="linear")),
    ("11b", 38.60, dict(src=C + "S11_package_world_journey.mp4", tin=2.40, zoom=1.30, zoom_to=1.38, cx=0.22, cy=0.20,
                        ease="linear")),
    ("11c", 39.65, dict(src=C + "S11_package_world_journey.mp4", tin=3.45, zoom=1.28, zoom_to=1.34, cx=0.45, cy=0.32,
                        ease="linear")),
    ("11d", 40.80, dict(src=C + "S11_package_world_journey.mp4", tin=4.58, zoom=1.22, zoom_to=1.42, cx=0.70, cy=0.14,
                        ease="out")),
    ("14", 42.25, dict(src=C + "S14_control_room.mp4", tin=2.70, zoom=1.0, zoom_to=1.08, cx=0.55, cy=0.45,
                       cx_to=0.62, cy_to=0.40, ease="linear", hide_logo=True)),
    ("15", 45.50, dict(src=C + "S15_ceo_office.mp4", tin=1.90, zoom=1.42, cx=0.628, cy=0.352, hide_logo=True,
                       lift=dict(rect=(0, 882, 704, 1140), accents=ORANGE_WHITE, keep_n=1, width=1000, y=1110))),
    ("13", 49.50, dict(src=C + "S13_curly_uniform_billboard.mp4", tin=0.00, zoom=1.38, cx=0.612, cy=0.3615,
                       hide_logo=True)),
    ("end", 51.85, dict(kind="endcard_v4")),
]
TOTAL = 55.45
_PLAN = [(sid, T(t0), d) for sid, t0, d in _PLAN if T(t0) is not None]
TOTAL = T(TOTAL, end=True)

SEGMENTS = []
_starts = {}
for k, (sid, t0, d) in enumerate(_PLAN):
    t1 = _PLAN[k + 1][1] if k + 1 < len(_PLAN) else TOTAL
    f0, f1 = round(t0 * FPS), round(t1 * FPS)
    seg = dict(id=sid, shot=k + 1, kind=d.pop("kind", "clip"), **d)
    dur = (f1 - f0) / FPS
    if seg["kind"] == "clip":
        seg["tout"] = round(seg["tin"] + dur, 4)
    else:
        seg["dur"] = dur
    _starts[sid] = f0 / FPS
    SEGMENTS.append(seg)


def _at(t):
    """absolute time -> (segment id, offset)"""
    sid = max((s for s in _starts if _starts[s] <= t + 1e-6), key=lambda s: _starts[s])
    return sid, round(t - _starts[sid], 4)


# absolute time of the first word of every narration line (see _v6_vo.LINES)
ABS = [0.10, 2.00, 4.50, 6.05, 7.35, 7.95, 10.30, 14.05, 15.52, 16.42,
       18.30, 19.80, 22.15, 23.35, 25.90, 29.45, 31.45, 33.05, 34.90, 37.65,
       39.69, 42.40, 44.15, 49.60, 51.95]
assert len(ABS) == len(LINES)
_POS = {14: 440, 15: 440, 18: 430}   # caption heights: shot 8 above the map, shot 10 above the red zone
VO = []
for i, ((txt, hl, opt), t) in enumerate(zip(LINES, ABS)):
    opt = dict(opt)
    if i in _POS:
        opt["marginv"] = _POS[i]
    if T(t) is None:
        opt["drop"] = True
        VO.append((SEGMENTS[0]["id"], 0.0, txt, hl, opt))
    else:
        VO.append((*_at(T(t)), txt, hl, opt))


def at(t, end=False):
    return _at(T(t, end=end))


def _keep(items):
    """drop music/SFX events that start inside a removed section"""
    return [x for x in items if x is not None]


def M(t, cue, cfrom, stop, *rest):
    if T(t) is None:
        return None
    return (*at(t), cue, cfrom, at(stop, end=True) if stop is not None else None, *rest)


def S(t, *rest):
    if T(t) is None:
        return None
    return (*at(t), *rest)


JB = 60 / 124 * 4  # jingle bar
MUSIC = _keep([
    M(0.00, "jingle_commercial", 0.0, 6.03, 0.0, 0.0, 0.012),
    M(9.65, "fanfare_victory", 0.0, None, -2.0, 0.0, 0.3),                 # TAA on the VIP cut
    M(13.95, "jingle_commercial", JB * 4, 16.37, 0.0, 0.03, 0.015),   # out on "באיזה יום?" -> dry
    M(17.95, "epic_adventure", 20.0, 22.05, 0.0, 0.02, 0.12),         # heroic departure
    M(22.05, "jingle_commercial", JB * 6, 25.75, 0.0, 0.03, 0.06),
    M(25.75, "epic_adventure", 0.0, 28.85, 0.0, 0.0, 0.01, dict(tapestop=0.35)),
    M(31.38, "jingle_commercial", JB * 8, 34.88, -1.0, 0.02, 0.015),  # out on "מבחינתנו"
    M(37.55, "epic_adventure", 16.69, 42.25, 0.0, 0.0, 0.012, dict(ramp=(-8.0, 0.0, 3.3))),
    M(42.45, "tension_control_room", 0.0, 45.00, -2.0, 0.3, 0.01),
    M(45.50, "jingle_commercial", JB * 2, 49.50, -9.0, 0.3, 0.2, dict(lowpass=900)),  # muzak in the CEO office
    M(49.50, "jingle_commercial", 0.0, 51.85, 0.0, 0.0, 0.012),
])

CLIP7 = "@clip:" + C + "S07_pickup_point_boxes.mp4"
SFX = _keep([
    S(0.00, "sparkle", -7, 0.0, None),
    S(3.12, "click", -22, 0.0, None),
    S(3.29, "click", -23, 0.0, None),
    S(3.50, "click", -14, 0.0, None),
    S(3.95, "order_confirm", -12, 0.0, 0.32),
    S(6.03, "room_office", 0, 0.0, 4.15),
    S(8.55, "riser", -9, 0.0, 1.62),
    S(10.15, "sparkle", -8, 0.0, None),
    S(15.45, "clock_ticks", -12, 0.0, 2.5),
    S(16.37, "room_office", 0, 0.0, 1.58),
    S(17.95, "applause", -17, 0.0, 4.1, dict(duck=True)),
    S(20.25, "cash_register", -15, 0.0, 0.7),                # bell lands on "תשלום", kept under the voice
    S(22.05, "room_rural", -2, 0.0, 3.7),
    S(22.05, CLIP7, -12, 1.00, 3.7, dict(duck=True, gate_db=-26)),
    S(22.15, "cardboard_creak", -22, 0.0, 3.5),
    S(25.07, "cash_register", -15, 0.12, 0.6),               # till bell on "גובים"
    S(28.85, "room_rural", -6, 0.0, 2.5),
    S(29.35, "crickets", -12, 0.0, 2.0),
    S(31.35, "room_rural", -4, 0.0, 1.6),
    S(34.88, "room_office", 0, 0.0, 2.67),
    S(37.36, "buzzer_wrong", -11, 0.0, None),
    S(37.70, "plane_flyby", -22, 0.0, 2.4),
    S(39.95, "ship_horn", -21, 0.0, 2.0),
    S(42.25, "room_office", -2, 0.0, 3.25),
    S(42.25, "alarm_beeps", -12, 0.0, 2.6, dict(duck=True)),
    S(42.55, "typing", -11, 0.0, 2.2, dict(duck=True)),
    S(45.00, "computer_error", -6, 0.0, None),
    S(45.50, "room_office", -4, 0.0, 4.0),
    S(49.50, "sparkle", -9, 0.0, None),
    S(49.50, "room_rural", -4, 0.0, 2.35),
    S(51.85, "room_rural", -10, 0.0, 3.6),
    S(53.60, "sparkle", -12, 0.0, None),
])

DUCK_EXTRA = []
DUCK_OVERRIDES = [(*at(37.55), 4.7, 10.0)]

CAPTIONS = dict(
    font="Heebo Black", size=91, punch_size=104, big_size=140,
    outline=7, shadow=3, outline_color="&H00401A0B&", shadow_color="&H90000000&",
    margin_l=100, margin_r=150, margin_v=520,
    punch_color="yellow", fade_in=90, stop_at_cuts=True,
    colors={"white": "&H00FFFFFF&", "yellow": "&H001EC8FF&", "red": "&H002B32E8&", "orange": "&H001F8AFF&"},
)

ENDCARD_V4 = dict(brush_width=980, brush_y=900, logo_width=640, logo_y=840, tagline_y=1078,
                  tagline_file="v5_tagline.png", card1_dur=1.75, crossfade=0.2, wipe=0.35, tagline_delay=0.3)

LOGO = dict(width=200, x=800, y=132, opacity=0.92)
