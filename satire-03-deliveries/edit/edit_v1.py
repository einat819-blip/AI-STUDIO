# -*- coding: utf-8 -*-
"""Edit decision list, draft 1: "משלוחים לכל חלקי הארץ*".

Everything is expressed relative to segments, so when real footage or the real
narration arrives, only the segment list / VO timings change and every caption,
music cue and SFX moves with it.

STATUS OF THIS DRAFT
- The narration audio was NOT supplied. VO times below are ESTIMATES used only
  to lay out captions and music. They must be replaced by the real word timings
  (edit/narration_words.json) before the final render.
- Shots 5b, 7, 8, 9, 10, 11, 12, 13 have no footage yet -> labelled slates.
- Shot 4 (agent raising three fingers) is covered by the thumbs-up clip.
"""

FPS = 30
W, H = 1080, 1920
DRAFT_LABEL = "טיוטה 1 · ללא קריינות · תזמון זמני"

CLIPS = "source/clips/"

# ---------------------------------------------------------------- picture
# kind: clip | slate | endcard
# clip: tin/tout in source seconds; zoom 1.0 = fill 9:16 with no stretch,
#       >1 = punch-in; cx, cy = framing centre as a fraction of the source.
SEGMENTS = [
    dict(id="1a", shot=1, kind="clip", src=CLIPS + "S01_courier_billboard.mp4", tin=0.00, tout=3.30),
    dict(id="1b", shot=1, kind="clip", src=CLIPS + "S01_courier_billboard.mp4", tin=4.45, tout=5.85,
         zoom=1.12, cx=0.50, cy=0.44),
    dict(id="2", shot=2, kind="clip", src=CLIPS + "S02_curly_orders_laptop.mp4", tin=2.95, tout=6.00),
    dict(id="3a", shot=3, kind="clip", src=CLIPS + "S03_agent_shock_eshkol.mp4", tin=0.15, tout=2.45, cx=0.60),
    dict(id="3b", shot=3, kind="clip", src=CLIPS + "S03_agent_shock_eshkol.mp4", tin=2.45, tout=5.15,
         zoom=1.15, cx=0.52, cy=0.36),
    dict(id="4-5a", shot=4, kind="clip", src=CLIPS + "S05a_agent_thumbs_up.mp4", tin=0.00, tout=5.95),
    dict(id="5b", shot=5, kind="slate", dur=3.0, title="שוט 5 (המשך) · חסר חומר",
         desc="המתולתלת מחכה בפתח הבית\nמנוע מתקרב ומתרחק · לוח שנה / שעון"),
    dict(id="6a", shot=6, kind="clip", src=CLIPS + "S06_doorstep_credit_card.mp4", tin=0.55, tout=3.70),
    dict(id="6b", shot=6, kind="clip", src=CLIPS + "S06_doorstep_credit_card.mp4", tin=4.85, tout=6.00,
         zoom=1.25, cx=0.50, cy=0.30),
    dict(id="7", shot=7, kind="slate", dur=5.0, title="שוט 7 · חסר חומר",
         desc="המתולתלת סוחבת ערמת חבילות\nלתא המטען של הרכב"),
    dict(id="8", shot=8, kind="slate", dur=4.6, title="שוט 8 · חסר חומר",
         desc="השליח עם משקפת, זכוכית מגדלת\nומפת מסע"),
    dict(id="9", shot=9, kind="slate", dur=3.0, title="שוט 9 · חסר חומר",
         desc="המתולתלת עם דגל ישראל\nמצביעה על עצמה בהלם"),
    dict(id="10", shot=10, kind="slate", dur=3.2, title="שוט 10 · חסר חומר",
         desc="נציג השירות עם מפת אזורי החלוקה\nמצביע על האזור האדום"),
    dict(id="11", shot=11, kind="slate", dur=5.4, title="שוט 11 · חסר חומר",
         desc="החבילה, המטוס, אוניית המשא\nוכדור הארץ"),
    dict(id="12", shot=12, kind="slate", dur=3.6, title="שוט 12 · חסר חומר",
         desc="השליח עם תיק הישרדות\nמול כביש כפרי רגיל"),
    dict(id="13", shot=13, kind="slate", dur=4.8, title="שוט 13 · חסר חומר",
         desc="המתולתלת במדי חברת המשלוחים\nמחזיקה את החבילה של עצמה"),
    dict(id="14", shot=14, kind="endcard", dur=9.0),
]

# ---------------------------------------------------------------- narration
# (segment, offset sec, text, highlights {word: colour}, options)
# "\N" = forced line break (max two lines). caption=False -> no caption
# (text already on screen). big=True -> single-word punch style.
Y, R = "yellow", "red"
VO = [
    ("1a", 0.15, "משלוחים לכל חלקי הארץ!", {}, dict(caption=False)),  # billboard already says it
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
    ("7", 0.15, "או נקודת איסוף!", {"נקודת": Y, "איסוף!": Y}, {}),
    ("7", 1.55, "כי למה שאנחנו ניסע,\\Nאם אתם יכולים?", {"אתם": Y, "יכולים?": Y}, {}),
    ("8", 0.15, "ויש גם מסלול מיוחד!", {"מסלול": Y, "מיוחד!": Y}, {}),
    ("8", 2.20, "אנחנו לא מגיעים לשם.", {"לא": R, "מגיעים": R}, {}),
    ("9", 0.15, "אבל רגע...\\Nאנחנו לא בישראל?!", {"בישראל?!": Y}, {}),
    ("10", 0.10, "בטח שאתם בישראל!", {}, {}),
    ("10", 1.35, "פשוט לא\\Nבאזור החלוקה.", {"לא": R, "באזור": R, "החלוקה.": R}, {}),
    ("11", 0.25, "החבילה שלכם חצתה\\Nיבשות, ימים ואוקיינוסים.", {"יבשות,": Y, "ימים": Y, "ואוקיינוסים.": Y}, {}),
    ("11", 3.05, "הגיעה כל הדרך\\Nמסין לישראל!", {"מסין": Y, "לישראל!": Y}, {}),
    ("12", 0.15, "אבל להגיע לאשכול?", {"לאשכול?": R}, {}),
    ("12", 1.50, "בואו לא נגזים.", {}, {}),
    ("13", 0.10, "משלוחים לכל חלקי הארץ!", {}, {}),
    ("13", 1.90, "חוץ מהחלק שלכם.", {"חוץ": R, "מהחלק": R, "שלכם.": R}, {}),
    ("13", 3.20, "בהצלחה!", {"בהצלחה!": Y}, dict(big=True)),
]

# ---------------------------------------------------------------- music
# (segment, offset, cue, cue_from_sec, stop=(segment, offset) | None, gain_db, fade_in, fade_out)
JINGLE_BAR = 60 / 124 * 4
MUSIC = [
    # 1. commercial jingle from frame one, hard stop on "אשכול"
    ("1a", 0.00, "jingle_commercial", 0.0, ("3b", 0.03), 0.0, 0.0, 0.015),
    # 2. jingle returns "as if everything is fine" and keeps going through the doorstep + pickup point
    ("4-5a", 0.05, "jingle_commercial", JINGLE_BAR * 4, ("8", 0.0), 0.0, 0.02, 0.06),
    # 3. adventure music for the "special route", hard stop on "אנחנו לא מגיעים לשם"
    ("8", 0.00, "epic_adventure", 0.0, ("8", 2.20), 0.0, 0.0, 0.015),
    # 4. chipper jingle for "בטח שאתם בישראל!", killed by the buzzer
    ("10", 0.05, "jingle_commercial", JINGLE_BAR * 8, ("10", 2.20), -1.0, 0.02, 0.02),
    # 5. epic orchestral journey (section C downbeat on the cut) through shot 12, hard stop on "בואו לא נגזים"
    ("11", 0.00, "epic_adventure", 20.0, ("12", 1.50), 0.0, 0.0, 0.015),
    # 6. the original opening jingle returns, stopped on "חוץ מהחלק שלכם"
    ("13", 0.00, "jingle_commercial", 0.0, ("13", 1.90), 0.0, 0.0, 0.015),
    # 7. ironic victory fanfare on "בהצלחה!"
    ("13", 3.18, "fanfare_victory", 0.0, None, -1.0, 0.0, 0.3),
]

# ---------------------------------------------------------------- sfx
# (segment, offset, name, gain_db, from_sec, dur | None)
SFX = [
    ("1a", 0.00, "sparkle", -7, 0.0, None),
    # ordering: soft key taps, the click, order confirmed
    ("2", 0.08, "click", -20, 0.0, None),
    ("2", 0.31, "click", -21, 0.0, None),
    ("2", 0.52, "click", -20, 0.0, None),
    ("2", 0.78, "click", -22, 0.0, None),
    ("2", 1.23, "click", -3, 0.0, None),
    ("2", 1.48, "order_confirm", -4, 0.0, None),
    # music stop: office room tone carries the comic pause
    ("3b", 0.00, "room_office", 0, 0.0, 2.75),
    ("4-5a", 1.45, "success_ding", -9, 0.0, None),
    # waiting at the door: engine approaches... and passes by. Time flies.
    ("5b", 0.00, "room_rural", 0, 0.0, 3.0),
    ("5b", 0.00, "engine_pass", -6, 0.4, 4.2),
    ("5b", 0.25, "clock_ticks", -14, 0.0, 2.6),
    ("5b", 0.60, "page_flip", -14, 0.0, None),
    ("5b", 1.25, "page_flip", -14, 0.0, None),
    ("5b", 1.90, "page_flip", -14, 0.0, None),
    ("6a", 0.00, "room_rural", -2, 0.0, 4.3),
    ("6a", 1.45, "cash_register", -1, 0.0, None),
    # pickup point: footsteps, cardboard strain (effort breaths: record or add from a licensed library)
    ("7", 0.30, "footsteps_gravel", -10, 0.0, 4.6),
    ("7", 0.70, "cardboard_creak", -13, 0.0, 4.0),
    ("8", 2.22, "crickets", -8, 0.0, 3.9),
    ("9", 0.00, "room_rural", -4, 0.0, 3.0),
    ("10", 2.20, "buzzer_wrong", -9, 0.0, None),
    ("10", 2.20, "room_office", -2, 0.0, 1.0),
    ("11", 0.35, "plane_flyby", -12, 0.0, 3.0),
    ("11", 2.10, "ship_horn", -13, 0.0, 3.0),
    ("12", 1.50, "room_rural", 0, 0.0, 2.1),
    ("13", 0.00, "sparkle", -9, 0.0, None),
    ("13", 0.00, "room_rural", -4, 0.0, 4.8),
    ("14", 0.15, "doorbell", -5, 0.0, None),
    ("14", 0.00, "room_rural", -10, 0.0, 9.0),
]

# extra music dips (segment, offset, dur) so key SFX read clearly where there is no VO
DUCK_EXTRA = [
    ("2", 1.10, 1.10),   # trackpad click + "order confirmed" chime
]

# ---------------------------------------------------------------- end card reveal (seconds into the card)
ENDCARD_REVEAL = [
    ("title", 0.00, 0.00, "fade"),
    ("brush", 0.75, 0.35, "wipe_rtl"),
    ("satire", 1.70, 0.40, "fade"),
    ("wait", 2.60, 0.40, "fade"),
    ("logo", 3.50, 0.50, "fade"),
    ("tagline", 4.40, 0.40, "fade"),
]
ENDCARD_PUSH = 0.025  # slow 2.5% push-in over the card
# The supplied card is full-bleed; its headline and tagline would sit under the
# Reels/TikTok top bar and caption area. Scale the content into the safe band.
ENDCARD_SAFE = dict(scale=0.80, content_top=107, content_bottom=1680, target_top=232, target_bottom=1490)

# ---------------------------------------------------------------- branding
LOGO = dict(width=200, x=800, y=132, opacity=0.92)  # top-right, under the platform icon row
