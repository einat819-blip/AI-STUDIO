# -*- coding: utf-8 -*-
"""Edit decision list, draft 2: "משלוחים לכל חלקי הארץ*".

Draft 2 adds the footage for shots 7 to 13.

STATUS
- Narration audio still NOT supplied: VO times are ESTIMATES (captions, ducking,
  music stops). Replace with real word timings (edit/narration_words.json).
- Still missing: shot 4 (three fingers, covered by the thumbs-up clip) and
  shot 5 continuation (waiting at the door) -> labelled slate.
- Shot 8 uses the take where the map reads "אשכול". The other take reads
  "אשכיל" (typo) and is not used.
- Shot 13: the billboard in the clip already shows the punch ("חוץ מהחלק שלכם.
  בהצלחה!"). To avoid revealing it early, "משלוחים לכל חלקי הארץ!" plays over a
  reprise of the opening shot, and the cut to her lands exactly on "חוץ".
"""

FPS = 30
W, H = 1080, 1920
DRAFT_LABEL = "טיוטה 2 · ללא קריינות · תזמון זמני"

C = "source/clips/"

SEGMENTS = [
    dict(id="1a", shot=1, kind="clip", src=C + "S01_courier_billboard.mp4", tin=0.00, tout=3.30),
    dict(id="1b", shot=1, kind="clip", src=C + "S01_courier_billboard.mp4", tin=4.45, tout=5.85,
         zoom=1.12, cx=0.50, cy=0.44),
    dict(id="2", shot=2, kind="clip", src=C + "S02_curly_orders_laptop.mp4", tin=2.95, tout=6.00),
    dict(id="3a", shot=3, kind="clip", src=C + "S03_agent_shock_eshkol.mp4", tin=0.15, tout=2.45, cx=0.60),
    dict(id="3b", shot=3, kind="clip", src=C + "S03_agent_shock_eshkol.mp4", tin=2.45, tout=5.15,
         zoom=1.15, cx=0.52, cy=0.36),
    dict(id="4-5a", shot=4, kind="clip", src=C + "S05a_agent_thumbs_up.mp4", tin=0.00, tout=5.95),
    dict(id="5b", shot=5, kind="slate", dur=3.0, title="שוט 5 (המשך) · חסר חומר",
         desc="המתולתלת מחכה בפתח הבית\nמנוע מתקרב ומתרחק · לוח שנה / שעון"),
    dict(id="6a", shot=6, kind="clip", src=C + "S06_doorstep_credit_card.mp4", tin=0.55, tout=3.70),
    dict(id="6b", shot=6, kind="clip", src=C + "S06_doorstep_credit_card.mp4", tin=4.85, tout=6.00,
         zoom=1.25, cx=0.50, cy=0.30),
    dict(id="7", shot=7, kind="clip", src=C + "S07_pickup_point_boxes.mp4", tin=0.00, tout=5.60),
    dict(id="8", shot=8, kind="clip", src=C + "S08_courier_binoculars_map.mp4", tin=0.25, tout=5.90),
    dict(id="9", shot=9, kind="clip", src=C + "S09_curly_israel_flag.mp4", tin=1.55, tout=4.75),
    dict(id="10", shot=10, kind="clip", src=C + "S10_agent_distribution_map.mp4", tin=1.10, tout=4.35),
    dict(id="11", shot=11, kind="clip", src=C + "S11_package_world_journey.mp4", tin=0.00, tout=4.90),
    dict(id="12", shot=12, kind="clip", src=C + "S12_courier_survival_gear.mp4", tin=0.00, tout=5.75),
    # 13: reprise of the opening ad shot for "משלוחים לכל חלקי הארץ!", then the reveal
    dict(id="13a", shot=13, kind="clip", src=C + "S01_courier_billboard.mp4", tin=1.95, tout=3.55),
    # hide_logo: the corner logo would sit on top of the billboard punch line
    dict(id="13b", shot=13, kind="clip", src=C + "S13_curly_uniform_billboard.mp4", tin=0.00, tout=2.20,
         hide_logo=True),
    dict(id="13c", shot=13, kind="clip", src=C + "S13_curly_uniform_billboard.mp4", tin=4.55, tout=5.95,
         zoom=1.08, cx=0.50, cy=0.40, hide_logo=True),
    dict(id="14", shot=14, kind="endcard", dur=9.0),
]

# (segment, offset, text, highlights, options). caption=False where the same
# words are already printed in the picture (billboards, the pickup-point sign).
Y, R = "yellow", "red"
VO = [
    ("1a", 0.15, "משלוחים לכל חלקי הארץ!", {}, dict(caption=False)),          # billboard
    ("1a", 2.00, "מהירים, נוחים\\Nועד פתח הבית!", {"פתח": Y, "הבית!": Y}, {}),
    ("3a", 0.10, "רגע...", {}, {}),
    ("3a", 0.85, "איפה אתם גרים?", {}, {}),
    ("3b", 0.05, "אשכול?!", {"אשכול?!": R}, dict(big=True)),
    ("3b", 1.65, "אה...", {}, {}),
    ("4-5a", 0.10, "אז יש לנו כמה אפשרויות!", {"אפשרויות!": Y}, {}),
    ("4-5a", 1.80, "משלוח פעם בשבוע!", {"פעם": Y, "בשבוע!": Y}, {}),
    ("4-5a", 3.25, "באיזה יום?", {}, {}),
    ("4-5a", 4.45, "כשיהיה נהג.", {"כשיהיה": Y, "נהג.": Y}, {}),
    ("6a", 0.10, "משלוח עד הבית!", {}, {}),
    ("6a", 1.40, "בתוספת תשלום, כמובן.", {"בתוספת": R, "תשלום,": R}, {}),
    ("7", 0.15, "או נקודת איסוף!", {}, dict(caption=False)),                 # sign: נקודת איסוף
    ("7", 1.45, "כי למה שאנחנו ניסע,\\Nאם אתם יכולים?", {"אתם": Y, "יכולים?": Y}, {}),
    # shot 8: captions sit lower so the map's "אשכול ✗" stays clear
    ("8", 0.10, "ויש גם מסלול מיוחד!", {"מסלול": Y, "מיוחד!": Y}, dict(marginv=440)),
    ("8", 2.75, "אנחנו לא מגיעים לשם.", {"לא": R, "מגיעים": R}, dict(marginv=440)),
    ("9", 0.10, "אבל רגע...\\Nאנחנו לא בישראל?!", {"בישראל?!": Y}, {}),
    ("10", 0.05, "בטח שאתם בישראל!", {}, {}),
    ("10", 1.10, "פשוט לא\\Nבאזור החלוקה.", {"לא": R, "באזור": R, "החלוקה.": R}, {}),
    ("11", 0.20, "החבילה שלכם חצתה\\Nיבשות, ימים ואוקיינוסים.", {"יבשות,": Y, "ימים": Y, "ואוקיינוסים.": Y}, {}),
    ("11", 3.00, "הגיעה כל הדרך\\Nמסין לישראל!", {"מסין": Y, "לישראל!": Y}, {}),
    ("12", 0.10, "אבל להגיע לאשכול?", {"לאשכול?": R}, {}),
    ("12", 3.75, "בואו לא נגזים.", {}, {}),
    ("13a", 0.10, "משלוחים לכל חלקי הארץ!", {}, dict(caption=False)),         # billboard
    ("13b", 0.05, "חוץ מהחלק שלכם.", {}, dict(caption=False)),                # billboard
    ("13c", 0.10, "בהצלחה!", {}, dict(caption=False)),                        # billboard
]

JINGLE_BAR = 60 / 124 * 4
MUSIC = [
    ("1a", 0.00, "jingle_commercial", 0.0, ("3b", 0.03), 0.0, 0.0, 0.015),
    ("4-5a", 0.05, "jingle_commercial", JINGLE_BAR * 4, ("8", 0.0), 0.0, 0.02, 0.06),
    ("8", 0.00, "epic_adventure", 0.0, ("8", 2.75), 0.0, 0.0, 0.015),
    ("10", 0.03, "jingle_commercial", JINGLE_BAR * 8, ("10", 1.58), -1.0, 0.02, 0.02),
    ("11", 0.00, "epic_adventure", 20.0, ("12", 3.75), 0.0, 0.0, 0.015),
    ("13a", 0.00, "jingle_commercial", 0.0, ("13b", 0.0), 0.0, 0.0, 0.012),
    ("13c", 0.08, "fanfare_victory", 0.0, None, -1.0, 0.0, 0.3),
]

SFX = [
    ("1a", 0.00, "sparkle", -7, 0.0, None),
    ("2", 0.08, "click", -20, 0.0, None),
    ("2", 0.31, "click", -21, 0.0, None),
    ("2", 0.52, "click", -20, 0.0, None),
    ("2", 0.78, "click", -22, 0.0, None),
    ("2", 1.23, "click", -3, 0.0, None),
    ("2", 1.48, "order_confirm", -4, 0.0, None),
    ("3b", 0.00, "room_office", 0, 0.0, 2.75),
    ("4-5a", 1.45, "success_ding", -9, 0.0, None),
    ("5b", 0.00, "room_rural", 0, 0.0, 3.0),
    ("5b", 0.00, "engine_pass", -6, 0.4, 4.2),
    ("5b", 0.25, "clock_ticks", -14, 0.0, 2.6),
    ("5b", 0.60, "page_flip", -14, 0.0, None),
    ("5b", 1.25, "page_flip", -14, 0.0, None),
    ("5b", 1.90, "page_flip", -14, 0.0, None),
    ("6a", 0.00, "room_rural", -2, 0.0, 4.3),
    ("6a", 1.45, "cash_register", -1, 0.0, None),
    # 7: struggling walk to the car, cardboard strain, boxes into the boot
    ("7", 0.00, "room_rural", -2, 0.0, 5.6),
    ("7", 0.20, "footsteps_gravel", -9, 0.0, 3.9),
    ("7", 0.10, "cardboard_creak", -12, 0.0, 4.2),
    ("7", 4.85, "box_thud", -8, 0.0, None),
    ("7", 5.20, "box_thud", -12, 0.0, None),
    # 8: hard stop -> crickets into shot 9
    ("8", 2.77, "crickets", -8, 0.0, 4.0),
    ("9", 0.00, "room_rural", -4, 0.0, 3.2),
    ("10", 1.58, "buzzer_wrong", -9, 0.0, None),
    ("10", 1.58, "room_office", -2, 0.0, 1.67),
    ("11", 0.25, "plane_flyby", -12, 0.0, 3.0),
    ("11", 1.90, "ship_horn", -13, 0.0, 3.0),
    ("12", 3.75, "room_rural", 0, 0.0, 2.0),
    ("13a", 0.00, "sparkle", -9, 0.0, None),
    ("13b", 0.00, "room_rural", -4, 0.0, 3.6),
    ("14", 0.15, "doorbell", -5, 0.0, None),
    ("14", 0.00, "room_rural", -10, 0.0, 9.0),
]

DUCK_EXTRA = [
    ("2", 1.10, 1.10),
]

ENDCARD_REVEAL = [
    ("title", 0.00, 0.00, "fade"),
    ("brush", 0.75, 0.35, "wipe_rtl"),
    ("satire", 1.70, 0.40, "fade"),
    ("wait", 2.60, 0.40, "fade"),
    ("logo", 3.50, 0.50, "fade"),
    ("tagline", 4.40, 0.40, "fade"),
]
ENDCARD_PUSH = 0.025
ENDCARD_SAFE = dict(scale=0.80, content_top=107, content_bottom=1680, target_top=232, target_bottom=1490)

LOGO = dict(width=200, x=800, y=132, opacity=0.92)
