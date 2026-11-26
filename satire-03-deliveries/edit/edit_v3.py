# -*- coding: utf-8 -*-
"""Edit decision list, version 3: "משלוחים לכל חלקי הארץ*", cut to the real narration.

Narration: ElevenLabs, "Itamar - Israeli Hebrew Narrator" (44.4 s).
Transcribed word by word with ivrit-ai Whisper (88/88 words match the script),
word times refined against the waveform (scripts/align_words.py).

The narration is split at its natural pauses into one chunk per VO line below.
Each chunk is placed so its FIRST WORD lands at (segment, offset). The words
inside a line keep the narrator's own timing; only the gaps between lines are
edited (comic pauses, visual beats).

Still not supplied: shot 4 (three fingers; the thumbs-up clip covers it) and
shot 5's continuation (waiting at the door). That beat is left out of this cut
instead of showing a placeholder; insert it after "4-5a" when it exists.
"""

FPS = 30
W, H = 1080, 1920
DRAFT_LABEL = ""

C = "source/clips/"

SEGMENTS = [
    dict(id="1a", shot=1, kind="clip", src=C + "S01_courier_billboard.mp4", tin=0.00, tout=3.10),
    dict(id="1b", shot=1, kind="clip", src=C + "S01_courier_billboard.mp4", tin=4.45, tout=5.85,
         zoom=1.12, cx=0.50, cy=0.44),
    dict(id="2", shot=2, kind="clip", src=C + "S02_curly_orders_laptop.mp4", tin=3.35, tout=6.00),
    dict(id="3a", shot=3, kind="clip", src=C + "S03_agent_shock_eshkol.mp4", tin=0.60, tout=2.45, cx=0.60),
    dict(id="3b", shot=3, kind="clip", src=C + "S03_agent_shock_eshkol.mp4", tin=2.45, tout=5.05,
         zoom=1.15, cx=0.52, cy=0.36),
    dict(id="4-5a", shot=4, kind="clip", src=C + "S05a_agent_thumbs_up.mp4", tin=0.00, tout=5.95),
    dict(id="6a", shot=6, kind="clip", src=C + "S06_doorstep_credit_card.mp4", tin=0.55, tout=3.75),
    dict(id="6b", shot=6, kind="clip", src=C + "S06_doorstep_credit_card.mp4", tin=4.85, tout=6.00,
         zoom=1.25, cx=0.50, cy=0.30),
    dict(id="7", shot=7, kind="clip", src=C + "S07_pickup_point_boxes.mp4", tin=0.00, tout=5.60),
    dict(id="8", shot=8, kind="clip", src=C + "S08_courier_binoculars_map.mp4", tin=0.25, tout=5.45),
    dict(id="9", shot=9, kind="clip", src=C + "S09_curly_israel_flag.mp4", tin=1.55, tout=4.40),
    # 10 starts at src 0.53 so the finger lands on the red zone exactly on "לא באזור החלוקה"
    dict(id="10", shot=10, kind="clip", src=C + "S10_agent_distribution_map.mp4", tin=0.53, tout=4.25),
    dict(id="11", shot=11, kind="clip", src=C + "S11_package_world_journey.mp4", tin=0.00, tout=6.03),
    dict(id="12", shot=12, kind="clip", src=C + "S12_courier_survival_gear.mp4", tin=0.00, tout=5.50),
    dict(id="13a", shot=13, kind="clip", src=C + "S01_courier_billboard.mp4", tin=1.45, tout=3.69),
    dict(id="13b", shot=13, kind="clip", src=C + "S13_curly_uniform_billboard.mp4", tin=0.00, tout=1.90,
         hide_logo=True),
    dict(id="13c", shot=13, kind="clip", src=C + "S13_curly_uniform_billboard.mp4", tin=4.40, tout=6.00,
         zoom=1.08, cx=0.50, cy=0.40, hide_logo=True),
    dict(id="14", shot=14, kind="endcard", dur=8.0),
]

Y, R = "yellow", "red"
VO = [
    ("1a", 0.15, "משלוחים לכל חלקי הארץ!", {}, dict(caption=False)),          # billboard
    ("1a", 2.09, "מהירים, נוחים\\Nועד פתח הבית!", {"פתח": Y, "הבית!": Y}, {}),
    ("3a", 0.10, "רגע...", {}, {}),
    ("3a", 0.87, "איפה אתם גרים?", {}, {}),
    ("3b", 0.05, "אשכול?!", {"אשכול?!": R}, dict(big=True)),
    ("3b", 1.55, "אה...", {}, {}),
    ("4-5a", 0.10, "אז יש לנו כמה אפשרויות!", {"אפשרויות!": Y}, {}),
    ("4-5a", 1.95, "משלוח פעם בשבוע!", {"פעם": Y, "בשבוע!": Y}, {}),
    ("4-5a", 3.45, "באיזה יום?", {}, {}),
    ("4-5a", 4.40, "כשיהיה נהג.", {"כשיהיה": Y, "נהג.": Y}, {}),
    ("6a", 0.10, "משלוח עד הבית!", {}, {}),
    # "בתוספת תשלום," [ka-ching in the pause] "כמובן." over her close-up
    ("6a", 1.81, "בתוספת תשלום,", {"בתוספת": R, "תשלום,": R}, {}),
    ("6b", 0.25, "כמובן.", {}, dict(gain_db=8.0)),   # delivered as a quiet aside: clip gain so it reads
    ("7", 0.15, "או נקודת איסוף!", {}, dict(caption=False)),                 # sign: נקודת איסוף
    ("7", 1.56, "כי למה שאנחנו ניסע,\\Nאם אתם יכולים?", {"אתם": Y, "יכולים?": Y}, {}),
    ("8", 0.10, "ויש גם מסלול מיוחד!", {"מסלול": Y, "מיוחד!": Y}, dict(marginv=440)),
    ("8", 2.75, "אנחנו לא מגיעים לשם.", {"לא": R, "מגיעים": R}, dict(marginv=440)),
    ("9", 0.10, "אבל רגע...\\Nאנחנו לא בישראל?!", {"בישראל?!": Y}, {}),
    ("10", 0.05, "בטח שאתם בישראל!", {}, {}),
    ("10", 1.65, "פשוט לא\\Nבאזור החלוקה.", {"לא": R, "באזור": R, "החלוקה.": R}, {}),
    ("11", 0.10, "החבילה שלכם חצתה\\Nיבשות, ימים ואוקיינוסים.", {"יבשות,": Y, "ימים": Y, "ואוקיינוסים.": Y}, {}),
    ("11", 3.85, "הגיעה כל הדרך\\Nמסין לישראל!", {"מסין": Y, "לישראל!": Y}, {}),
    ("12", 0.45, "אבל להגיע לאשכול?", {"לאשכול?": R}, {}),
    ("12", 3.72, "בואו לא נגזים.", {}, {}),
    ("13a", 0.10, "משלוחים לכל חלקי הארץ!", {}, dict(caption=False)),         # billboard
    ("13b", 0.05, "חוץ מהחלק שלכם.", {}, dict(caption=False)),                # billboard
    ("13c", 0.10, "בהצלחה!", {}, dict(caption=False)),                        # billboard
]

JINGLE_BAR = 60 / 124 * 4
MUSIC = [
    # commercial jingle from frame one, hard stop on "אשכול"
    ("1a", 0.00, "jingle_commercial", 0.0, ("3b", 0.03), 0.0, 0.0, 0.015),
    # back "as if everything is fine": through the options, the doorstep and the pickup point
    ("4-5a", 0.05, "jingle_commercial", JINGLE_BAR * 4, ("8", 0.0), 0.0, 0.02, 0.06),
    # adventure music, hard stop on "אנחנו לא מגיעים לשם"
    ("8", 0.00, "epic_adventure", 0.0, ("8", 2.75), 0.0, 0.0, 0.015),
    # chipper jingle for "בטח שאתם בישראל!", killed by the buzzer
    ("10", 0.03, "jingle_commercial", JINGLE_BAR * 8, ("10", 2.95), -1.0, 0.02, 0.02),
    # epic journey through shot 12, hard stop on "בואו לא נגזים"
    ("11", 0.00, "epic_adventure", 20.0, ("12", 3.72), 0.0, 0.0, 0.015),
    # the opening jingle returns, stopped on "חוץ"
    ("13a", 0.00, "jingle_commercial", 0.0, ("13b", 0.0), 0.0, 0.0, 0.012),
    # ironic victory fanfare on "בהצלחה!"
    ("13c", 0.08, "fanfare_victory", 0.0, None, -1.0, 0.0, 0.3),
]

SFX = [
    ("1a", 0.00, "sparkle", -7, 0.0, None),
    ("2", 0.05, "click", -20, 0.0, None),
    ("2", 0.25, "click", -21, 0.0, None),
    ("2", 0.45, "click", -20, 0.0, None),
    ("2", 0.62, "click", -22, 0.0, None),
    ("2", 0.83, "click", -3, 0.0, None),
    ("2", 1.10, "order_confirm", -4, 0.0, None),
    ("3b", 0.00, "room_office", 0, 0.0, 2.6),
    ("4-5a", 1.62, "success_ding", -9, 0.0, None),
    ("6a", 0.00, "room_rural", -2, 0.0, 4.35),
    ("6a", 2.62, "cash_register", -6, 0.0, 0.8),       # clack on the end of "תשלום", bell in the pause
    ("7", 0.00, "room_rural", -2, 0.0, 5.6),
    ("7", 0.20, "footsteps_gravel", -18, 0.0, 3.9),
    ("7", 0.10, "cardboard_creak", -21, 0.0, 4.2),
    ("7", 4.85, "box_thud", -8, 0.0, None),
    ("7", 5.20, "box_thud", -12, 0.0, None),
    ("8", 2.75, "room_rural", -6, 0.0, 2.45),         # music stops: only the outdoors remain
    ("8", 3.95, "crickets", -8, 0.0, 2.2),            # after "אנחנו לא מגיעים לשם."
    ("9", 0.00, "room_rural", -4, 0.0, 2.85),
    ("10", 2.95, "buzzer_wrong", -9, 0.0, None),
    ("10", 2.95, "room_office", -2, 0.0, 0.77),
    ("11", 0.25, "plane_flyby", -17, 0.0, 3.0),
    ("11", 1.90, "ship_horn", -17, 0.0, 3.0),
    ("12", 3.72, "room_rural", 0, 0.0, 1.78),
    ("13a", 0.00, "sparkle", -9, 0.0, None),
    ("13b", 0.00, "room_rural", -4, 0.0, 3.5),
    ("14", 0.15, "doorbell", -5, 0.0, None),
    ("14", 0.00, "room_rural", -10, 0.0, 8.0),
]

DUCK_EXTRA = [
    ("2", 0.70, 1.10),   # trackpad click + "order confirmed" chime
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
