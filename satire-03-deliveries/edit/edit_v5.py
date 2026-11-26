# -*- coding: utf-8 -*-
"""Edit decision list, V5_APPROVED: v4 + the three approved final fixes only.

1. "הזמנת משלוח? מזל טוב, התקבלת לעבודה כשליחה!" removed. It is printed on a
   paper banner at the bottom of the source clip of shot 13 (source y >= ~915);
   13b and 13c are reframed tighter (window bottom at source y 904) so the banner
   is out of frame. Her face, the box and the billboard punch line stay in shot.
2. Studio tagline on the end card +25% (54 -> 68 px), same font, colour and timing.
3. Maximum-quality export: lossless intermediates, final H.264 High CRF 12,
   preset veryslow, 1080x1920, 30 fps, AAC 320k / 48 kHz.

Narration, music, SFX, scene order, timing and all other captions: unchanged from v4.
"""

FPS = 30
W, H = 1080, 1920
DRAFT_LABEL = ""
PY_CLIPS = True
FINAL_CRF = 12   # maximum-quality master
FINAL_PRESET = "veryslow"
LOSSLESS_INTERMEDIATES = True
TP_CEILING = -2.5  # headroom for AAC overshoot on transients

C = "source/clips/"

SEGMENTS = [
    # 1-2: the perfect ad (cut to her ordering on "ועד")
    dict(id="1", shot=1, kind="clip", src=C + "S01_courier_billboard.mp4", tin=0.00, tout=3.10),
    dict(id="2", shot=2, kind="clip", src=C + "S02_curly_orders_laptop.mp4", tin=3.75, tout=5.07),
    # 3: "רגע... איפה אתם גרים? אשכול?!" crash zoom lands on "אשכול"
    dict(id="3", shot=3, kind="clip", src=C + "S03_agent_shock_eshkol.mp4", tin=0.90, tout=5.68,
         zoom=1.0, cx=0.60, cy=0.50, zoom_to=1.30, cx_to=0.53, cy_to=0.33, zoom_t0=1.38, zoom_t1=1.54, ease="out"),
    # 4-5: the options
    dict(id="4", shot=4, kind="clip", src=C + "S05a_agent_thumbs_up.mp4", tin=0.00, tout=2.20,
         zoom=1.0, zoom_to=1.10, ease="linear"),
    dict(id="5a", shot=5, kind="clip", src=C + "S05a_agent_thumbs_up.mp4", tin=3.20, tout=4.10),
    dict(id="5b", shot=5, kind="clip", src=C + "S05a_agent_thumbs_up.mp4", tin=4.58, tout=5.40,
         zoom=1.18, cx=0.47, cy=0.35),
    # 6: doorstep
    dict(id="6a", shot=6, kind="clip", src=C + "S06_doorstep_credit_card.mp4", tin=0.55, tout=3.45),
    dict(id="6b", shot=6, kind="clip", src=C + "S06_doorstep_credit_card.mp4", tin=4.85, tout=5.60,
         zoom=1.25, cx=0.50, cy=0.30),
    # 7: pickup point
    dict(id="7", shot=7, kind="clip", src=C + "S07_pickup_point_boxes.mp4", tin=1.00, tout=5.45),
    # 8: the special route (map zooms to "אשכול ✗" on "אנחנו לא מגיעים לשם")
    dict(id="8", shot=8, kind="clip", src=C + "S08_courier_binoculars_map.mp4", tin=0.55, tout=5.20),
    # 9: "we're not in Israel?!"
    dict(id="9", shot=9, kind="clip", src=C + "S09_curly_israel_flag.mp4", tin=1.85, tout=4.20),
    # 10: the distribution map; finger hits the red zone on "לא", the map fills the frame
    dict(id="10", shot=10, kind="clip", src=C + "S10_agent_distribution_map.mp4", tin=0.53, tout=4.20,
         zoom=1.12, cx=0.60, cy=0.48, zoom_to=1.45, cx_to=0.66, cy_to=0.55, zoom_t0=1.62, zoom_t1=2.12, ease="inout"),
    # 11: the journey, cut on the words
    dict(id="11a", shot=11, kind="clip", src=C + "S11_package_world_journey.mp4", tin=0.00, tout=1.02,
         zoom=1.0, zoom_to=1.06, ease="linear"),
    dict(id="11b", shot=11, kind="clip", src=C + "S11_package_world_journey.mp4", tin=1.02, tout=2.10,
         zoom=1.30, zoom_to=1.38, cx=0.55, cy=0.16, ease="linear"),
    dict(id="11c", shot=11, kind="clip", src=C + "S11_package_world_journey.mp4", tin=2.10, tout=3.55,
         zoom=1.28, zoom_to=1.34, cx=0.45, cy=0.30, ease="linear"),
    dict(id="11d", shot=11, kind="clip", src=C + "S11_package_world_journey.mp4", tin=3.55, tout=4.85,
         zoom=1.05, zoom_to=1.12, ease="linear"),
    dict(id="11e", shot=11, kind="clip", src=C + "S11_package_world_journey.mp4", tin=4.85, tout=6.03,
         zoom=1.22, zoom_to=1.42, cx=0.70, cy=0.14, ease="out"),
    # 12: survival-gear courier, gentle zooms
    dict(id="12a", shot=12, kind="clip", src=C + "S12_courier_survival_gear.mp4", tin=0.00, tout=1.85,
         zoom=1.0, zoom_to=1.08, ease="linear"),
    dict(id="12b", shot=12, kind="clip", src=C + "S12_courier_survival_gear.mp4", tin=2.60, tout=3.35, zoom=1.04),
    dict(id="12c", shot=12, kind="clip", src=C + "S12_courier_survival_gear.mp4", tin=3.60, tout=5.10,
         zoom=1.06, zoom_to=1.16, ease="linear"),
    # 13: back to the ad, then the reveal
    dict(id="13a", shot=13, kind="clip", src=C + "S01_courier_billboard.mp4", tin=0.00, tout=2.36),
    # 13b/13c reframed: the paper banner at the bottom of the source is out of frame
    dict(id="13b", shot=13, kind="clip", src=C + "S13_curly_uniform_billboard.mp4", tin=0.00, tout=1.36,
         zoom=1.38, cx=0.612, cy=0.3615,
         hide_logo=True, patch=dict(rect=(405, 225, 630, 304), keep_below=250)),   # "בהצלחה!" hidden until it is said
    dict(id="13c", shot=13, kind="clip", src=C + "S13_curly_uniform_billboard.mp4", tin=4.40, tout=5.81,
         zoom=1.42, cx=0.612, cy=0.373, hide_logo=True),
    # 14: end card
    dict(id="14", shot=14, kind="endcard_v4", dur=4.6),
]

Y, R = "yellow", "red"
VO = [
    ("1", 0.10, "משלוחים לכל חלקי הארץ!", {}, dict(caption=False)),            # billboard
    ("1", 2.04, "מהירים, נוחים\\Nועד פתח הבית!", {"פתח": Y, "הבית!": Y}, {}),
    ("3", 0.06, "רגע...", {}, {}),
    ("3", 0.67, "איפה אתם גרים?", {}, {}),
    ("3", 1.53, "אשכול?!", {"אשכול?!": R}, dict(big=True)),
    ("3", 2.88, "אה...", {}, {}),
    ("3", 3.75, "אז יש לנו כמה אפשרויות!", {"אפשרויות!": Y}, {}),
    ("4", 0.79, "משלוח פעם בשבוע!", {"פעם": Y, "בשבוע!": Y}, {}),
    ("5a", 0.05, "באיזה יום?", {}, {}),
    ("5b", 0.02, "כשיהיה נהג.", {}, dict(punch=True)),
    ("6a", 0.10, "משלוח עד הבית!", {}, {}),
    ("6a", 1.77, "בתוספת תשלום,", {}, dict(punch=True)),
    ("6b", 0.14, "כמובן.", {}, dict(gain_db=8.0)),        # quiet aside in the read: clip gain
    ("7", 0.10, "או נקודת איסוף!", {}, dict(caption=False)),                   # sign: נקודת איסוף
    ("7", 1.47, "כי למה שאנחנו ניסע,\\Nאם אתם יכולים?", {"אתם": Y, "יכולים?": Y}, {}),
    ("8", 0.10, "ויש גם מסלול מיוחד!", {"מסלול": Y, "מיוחד!": Y}, dict(marginv=440)),
    ("8", 2.30, "אנחנו לא מגיעים לשם.", {}, dict(punch=True, marginv=440)),
    ("9", 0.10, "אבל רגע...\\Nאנחנו לא בישראל?!", {"בישראל?!": Y}, {}),
    ("10", 0.05, "בטח שאתם בישראל!", {"בישראל!": Y}, {}),
    ("10", 1.65, "פשוט לא\\Nבאזור החלוקה.", {}, dict(punch=True, marginv=430)),
    ("11a", 0.10, "החבילה שלכם חצתה\\Nיבשות, ימים ואוקיינוסים.", {"יבשות,": Y, "ימים": Y, "ואוקיינוסים.": Y}, {}),
    ("11d", 0.25, "הגיעה כל הדרך\\Nמסין לישראל!", {"מסין": Y, "לישראל!": Y}, {}),
    ("12a", 0.40, "אבל להגיע לאשכול?", {"לאשכול?": R}, {}),   # a beat of silence after the music stops
    ("12c", 0.18, "בואו לא נגזים.", {}, dict(punch=True)),
    ("13a", 0.10, "משלוחים לכל חלקי הארץ!", {}, dict(caption=False)),           # billboard
    ("13b", 0.05, "חוץ מהחלק שלכם.", {}, dict(caption=False)),                  # billboard
    ("13c", 0.05, "בהצלחה!", {}, dict(caption=False)),                          # billboard
]

JB = 60 / 124 * 4  # jingle bar
MUSIC = [
    # the perfect ad, hard stop on "אשכול"
    ("1", 0.00, "jingle_commercial", 0.0, ("3", 1.51), 0.0, 0.0, 0.012),
    # "as if everything is fine": back on "אז יש לנו", out on "כשיהיה נהג"
    ("3", 3.75, "jingle_commercial", JB * 4, ("5b", 0.0), 0.0, 0.02, 0.015),
    ("6a", 0.00, "jingle_commercial", JB * 6, ("8", 0.0), 0.0, 0.03, 0.06),
    # adventure music runs down before "אנחנו לא מגיעים לשם"
    ("8", 0.00, "epic_adventure", 0.0, ("8", 1.85), 0.0, 0.0, 0.01, dict(tapestop=0.35)),
    # chipper jingle killed by the buzzer
    ("10", 0.03, "jingle_commercial", JB * 8, ("10", 2.92), -1.0, 0.02, 0.02),
    # the journey: builds from section B, epic downbeat on "הגיעה", full stop on the cut to 12
    ("11a", 0.00, "epic_adventure", 16.20, ("12a", 0.0), 0.0, 0.0, 0.012, dict(ramp=(-8.0, 0.0, 3.8))),
    # back to the ad, stopped on "חוץ"
    ("13a", 0.00, "jingle_commercial", 0.0, ("13b", 0.0), 0.0, 0.0, 0.012),
    ("13c", 0.03, "fanfare_victory", 0.0, None, -1.0, 0.0, 0.3),
]

CLIP7 = "@clip:" + C + "S07_pickup_point_boxes.mp4"
SFX = [
    ("1", 0.00, "sparkle", -7, 0.0, None),
    ("2", 0.05, "click", -22, 0.0, None),
    ("2", 0.22, "click", -23, 0.0, None),
    ("2", 0.43, "click", -9, 0.0, None),
    ("2", 1.10, "order_confirm", -8, 0.0, 0.32),       # short: must not ring into "רגע..."
    ("3", 1.53, "room_office", 0, 0.0, 2.25),
    ("4", 0.50, "success_ding", -11, 0.0, None),
    ("4", 0.75, "sparkle", -14, 0.0, None),
    ("5b", 0.00, "room_office", 0, 0.0, 0.82),
    ("6a", 0.00, "room_rural", -2, 0.0, 2.9),
    ("6a", 2.63, "cash_register", -6, 0.0, 0.45),
    ("6b", 0.00, "room_rural", -2, 0.0, 0.75),
    ("7", 0.00, "room_rural", -2, 0.0, 4.45),
    ("7", 0.00, CLIP7, -6, 1.00, 4.45, dict(duck=True, gate_db=-26)),   # her own effort sounds, steps, boot thud
    ("7", 0.10, "cardboard_creak", -22, 0.0, 4.2),
    ("7", 4.30, "box_thud", -20, 0.0, None),
    ("8", 1.85, "room_rural", -6, 0.0, 2.8),
    ("8", 3.50, "crickets", -8, 0.0, 1.6),
    ("9", 0.00, "room_rural", -4, 0.0, 2.35),
    ("10", 2.92, "buzzer_wrong", -9, 0.0, None),
    ("10", 2.92, "room_office", -2, 0.0, 0.75),
    ("11b", 0.00, "plane_flyby", -16, 0.0, 2.5),
    ("11c", 0.15, "ship_horn", -16, 0.0, 2.4),
    ("12a", 0.00, "room_rural", 0, 0.0, 4.1),
    ("13a", 0.00, "sparkle", -9, 0.0, None),
    ("13b", 0.00, "room_rural", -4, 0.0, 2.8),
    ("14", 0.00, "room_rural", -10, 0.0, 4.6),
]

DUCK_EXTRA = []
DUCK_OVERRIDES = [("11a", 0.0, 6.03, 9.0)]   # let the journey music swell closer under the voice

CAPTIONS = dict(
    font="Heebo Black", size=91, punch_size=104, big_size=140,
    outline=7, shadow=3, outline_color="&H00401A0B&", shadow_color="&H90000000&",
    margin_l=100, margin_r=150, margin_v=520,
    punch_color="yellow", fade_in=90,
    colors={"white": "&H00FFFFFF&", "yellow": "&H001EC8FF&", "red": "&H002B32E8&", "orange": "&H001F8AFF&"},
)

ENDCARD_V4 = dict(brush_width=980, brush_y=900, logo_width=640, logo_y=840, tagline_y=1078,
                  tagline_file="v5_tagline.png",
                  card1_dur=1.8, crossfade=0.2, wipe=0.35, tagline_delay=0.35)

LOGO = dict(width=200, x=800, y=132, opacity=0.92)
