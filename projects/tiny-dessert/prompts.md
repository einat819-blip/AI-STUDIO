# פרומפטים — הקטן

## איך להשתמש

- הפרומפטים באנגלית, כי מודלים של תמונה ווידאו מבצעים אנגלית בצורה הכי מדויקת. הדיאלוג לא נמצא בפרומפטים: מקליטים אותו ומוסיפים בעריכה.
- השורה האחרונה בכל פרומפט היא רשימת בלוקים, למשל `[EINAT] [MINI] [DESSERT] [STYLE]`. מחליפים כל בלוק בטקסט שלו מהסעיף "בלוקים קבועים".
- בכל כלי שמקבל תמונות רפרנס, מצרפים תמיד את דף הדמות ואת תמונת הקינוח. הטקסט משלים את הרפרנס, הוא לא מחליף אותו.
- לכל שוט יש תמונת פתיחה (Start frame) ופרומפט וידאו (Video). בשוטים עם מעבר יש גם תמונת סיום (End frame), לכלים שתומכים בפריים ראשון ואחרון.
- פרומפט הווידאו מתאר בעיקר תנועה, כי המראה מגיע מתמונת הפתיחה. בכלים שעובדים בלי תמונת פתיחה, מוסיפים לסוף פרומפט הווידאו את כל הבלוקים של תמונת הפתיחה.
- 4–6 גרסאות לכל שוט, באורך 5–8 שניות. בוחרים את 3 השניות הטובות.
- אם הכלי מייצר סאונד בעצמו, מכבים או מתעלמים. הסאונד נבנה בנפרד ([sound.md](sound.md)).

## בלוקים קבועים

### [STYLE]

```
Photoreal high-end food commercial. Bright, airy white tabletop set by a large window, warm golden late-morning sunlight from frame left and slightly behind, soft white bounce fill. Palette: clean white, turquoise and warm gold, with deep chocolate brown and raspberry red accents. Rich, true-to-life textures, crisp detail, gentle filmic contrast, clean neutral whites. Vertical 9:16, 24fps. No text, no logos, no watermarks.
```

### [EINAT]

לפי התמונות שלך, עם השיער שבחרת (בלונד עד הכתפיים):

```
EINAT: a woman with shoulder-length wavy blonde hair with darker roots, worn loose, dark defined eyebrows, hazel-brown eyes and warm tan skin. She wears a fitted solid deep-turquoise top with sleeves rolled to the elbow, high-waisted cream trousers and white sneakers. Same face, hair and outfit in every shot.
```

### [MINI]

לכל שוט שבו עינת זעירה:

```
Miniature EINAT is exactly 3.5 cm tall, about a third of the dessert's height: a real human being shrunk down, with real skin texture, real fabric and natural proportions. Not a figurine, not a toy, not a doll, not stylized.
```

### [DESSERT]

```
THE DESSERT: a single-serving chocolate dome, 9 cm tall and 8 cm wide, on a wide-rimmed matte white ceramic plate 26 cm across. A high-gloss tempered dark-chocolate shell, mirror-smooth with sharp sunlight reflections, on a thin round chocolate sablé base, crowned with a soft swirled peak of vanilla chantilly cream. Irresistible and edible, never plastic.
```

### [RASPBERRY]

משוט 3B והלאה:

```
A single fresh raspberry, 2.5 cm, sits on top of the cream peak.
```

### [BITE]

משוט 5 והלאה (בשוט 4B הביס נלקח מול המצלמה):

```
One spoonful is missing from the side facing the camera, showing a silky dark chocolate mousse inside the cracked shell.
```

### מה להימנע

לכלים שיש בהם negative prompt:

```
cartoon, toy, figurine, doll, plastic, CGI look, warped hands, extra fingers, melting chocolate, matte or dull chocolate, deformed spoon, text, letters, watermark, logo
```

בשוטים הרחבים (2B, 3B, 5) מוסיפים גם:

```
tilt-shift, miniature effect, blurry edges, shallow depth of field
```

---

## 0. רפרנסים — מייצרים פעם אחת

### דף דמות

```
Character reference sheet. Five views on one sheet: full body front, full body three-quarter, full body side profile, full body back, and a head-and-shoulders close-up. Neutral relaxed pose, plain white seamless background, soft even daylight, photoreal, identical face, hair and outfit in every view. Match the face to the attached photos exactly.
[EINAT]
```

### הקינוח

```
Hero product photo of the dessert, three-quarter view from slightly above, 100mm macro lens, on a white table by a sunny window.
[DESSERT] [STYLE]
```

---

## 1. "קטן. הבנתי." · 0:00–0:04

**Start frame**

```
Macro close-up at tabletop height, 100mm macro lens, shallow depth of field. The dessert fills the upper two-thirds of the vertical frame, its glossy chocolate catching warm sunlight. On the wide white rim of the plate, right beside it, stands miniature EINAT in sharp focus, seen from the front three-quarter. A neatly folded turquoise linen napkin lies on the white table next to the plate, one corner draped over the plate rim at her feet. Soft, creamy background of a bright white room.
[EINAT] [MINI] [DESSERT] [STYLE]
```

**Video**

```
Very slow push-in. Miniature EINAT stands still beside the towering chocolate dessert, listening. She slowly tilts her head back and her gaze climbs the dessert from base to summit, taking in its size. A short beat. Then a small, dry, knowing nod. Subtle natural body movement, realistic weight, a few strands of hair moving. Shallow depth of field.
[MINI] [STYLE]
```

---

## 2A. המפית · 0:04–0:07

**Start frame**

```
Close tabletop shot at the eye level of miniature EINAT, 50mm macro lens. She stands on the rim of the white plate and grips the corner of a folded turquoise linen napkin with both hands, leaning back, ready to pull. The dessert rises beside her. The linen weave is clearly visible.
[EINAT] [MINI] [DESSERT] [STYLE]
```

**End frame**

```
High three-quarter view from above the table. The white plate with the dessert now sits in the middle of a small, calm turquoise sea that covers the tabletop around it: real water, gentle ripples, sparkling sun glints. At its outer border the water ends in the napkin's neat hemmed edge, which still faintly shows a linen weave. Miniature EINAT stands on the plate rim at the water's edge.
[EINAT] [MINI] [DESSERT] [STYLE]
```

**Video**

```
In one continuous, fluid motion, miniature EINAT pulls the corner of the turquoise linen napkin. The napkin unfurls outward across the white table in a single rolling wave, and as each fold lands it turns into real water: the linen weave dissolves into rippling liquid, fold crests become small wave crests, and sunlight begins to sparkle on the surface, until the plate is encircled by a small turquoise sea with a hemmed fabric border. The camera rises and pulls back in one smooth move to reveal it.
[MINI] [STYLE]
```

---

## 2B. האי · 0:07–0:10

**Start frame**

```
Camera at water level on a turquoise sea, 18mm wide lens, deep focus, everything sharp from foreground to background. The dessert rises from the sea like a majestic tropical island: glossy chocolate cliffs gleaming in warm sunlight, the cream peak glowing like a snowcap against a bright, hazy white sky, the white plate rim a pale beach ring at its base. Small realistic waves with sun sparkles in the foreground. A tiny sailboat with a white sail in the mid-ground. Light atmospheric haze, epic scale. It looks like a real seascape, not a miniature.
[DESSERT] [STYLE]
```

**Video**

```
The camera descends smoothly to just above the water surface and glides slowly forward, so the chocolate dessert grows into a towering island. A small sailboat with a white sail glides from right to left across the foreground, its bow cutting a little wake. Gentle swell, water droplets and sun glints sparkle. Real ocean physics and scale, deep focus throughout.
[STYLE]
```

---

## 3A. עבודת יד · 0:10–0:13.4

**Start frame**

```
Close-up near the summit of the dessert, 50mm macro lens, eye level with the top of the cream peak. Miniature EINAT stands on the top rung of a tiny ladder made of rolled wafer cookies tied together with baker's twine, leaning against the glossy chocolate dome. She hugs a fresh, perfect raspberry almost as big as her torso in both arms, about to place it on the cream peak. Glossy chocolate reflecting sunlight, visible cream texture. Background: soft out-of-focus turquoise sea with sparkles.
[EINAT] [MINI] [DESSERT] [STYLE]
```

לסולם עץ רגיל, מחליפים את `a tiny ladder made of rolled wafer cookies tied together with baker's twine` ב־`a tiny wooden step ladder`.

**Video**

```
Miniature EINAT carefully lifts the big raspberry with both arms, steadies herself on the wafer ladder, and gently sets it on top of the cream peak, where it settles softly into the cream. She lets go, steps back half a step on the rung and admires it. Realistic weight and effort, clean, precise hand movements. Nearly static camera with a very slight drift.
[MINI] [STYLE]
```

---

## 3B. פריים המותג · 0:13.4–0:17

**Start frame:** הפריים האחרון של הקליפ שנבחר לשוט 3A.

**End frame**

```
Luxury campaign hero frame, vertical, perfectly composed. The dessert is centered in the lower middle of the frame on its white plate, in a calm turquoise miniature sea. Warm sunlight rim-lights it from behind left: the cream glows and the chocolate shell carries one long, clean specular highlight. A path of sun sparkles on the water leads to the dessert. Generous clean white negative space above. Miniature EINAT stands at the foot of the wafer ladder on the plate rim, very small, looking up at her work. Elegant, minimal, high-end patisserie advertising.
[EINAT] [MINI] [DESSERT] [RASPBERRY] [STYLE]
```

**Video**

```
A smooth, elegant crane move: the camera pulls back and rises from the raspberry close-up to a perfectly composed hero frame of the whole dessert island, then eases to a complete stop and holds. The water calms, sun sparkles twinkle, the light blooms slightly. Slow, controlled, luxurious.
[STYLE]
```

---

## 4A. הצל · 0:17–0:19.6

**Start frame**

```
Low angle from behind and beside miniature EINAT, who stands on the plate rim at the foot of the dessert. A wafer ladder leans on the dome. We look up the glossy chocolate dome toward a bright, sunlit sky.
[EINAT] [MINI] [DESSERT] [RASPBERRY] [STYLE]
```

**Video**

```
A huge shadow in the shape of a spoon sweeps across the scene, darkening miniature EINAT and the dessert. She slowly turns and looks up. From the top of the frame, the polished silver bowl of a normal-size dessert spoon descends into view, enormous compared to her, wider than she is tall, reflecting the sunlight. Suspenseful but playful, not scary.
[MINI] [STYLE]
```

---

## 4B. הביס · 0:19.6–0:23

**Start frame**

```
Extreme macro close-up from the side, 100mm macro lens, shallow depth of field. The tip of a polished silver dessert spoon just touches the swirled vanilla cream and the glossy tempered dark-chocolate shell of the dessert. Warm sunlight, rich texture.
[DESSERT] [RASPBERRY] [STYLE]
```

**Video**

```
Slow motion, extreme macro. The silver spoon presses down through the swirl of vanilla cream and into the glossy tempered chocolate shell. The shell cracks into crisp, clean shards, revealing a silky dark chocolate mousse inside. The spoon scoops one perfect bite and lifts slightly, a shard of chocolate resting on the cream. Static camera, focus on the point of the crack. Appetizing, tactile, high-end food commercial.
[STYLE]
```

---

## 5. "אז זה הקטן." · 0:23–0:26

**Start frame**

```
Close shot at plate height. A tiny wafer ladder leans on the dessert's dome. The plate sits in a small turquoise sea, gentle waves lapping at its rim.
[DESSERT] [RASPBERRY] [BITE] [STYLE]
```

**End frame — גרסה A (לפי הבריף)**

```
Medium shot at eye level, 35mm lens. EINAT, at normal human size, sits at a white table by a sunlit window, holding a silver dessert spoon with a bite of the chocolate dessert, looking straight into the camera with a dry, satisfied half-smile. In front of her, the dessert sits on its plate in a small square turquoise sea the size of a napkin, with neat hemmed edges, tiny waves lapping at the plate, and a tiny white sailboat on the water. A tiny wafer ladder leans on the dome. Bright white room, warm sunlight.
[EINAT] [DESSERT] [RASPBERRY] [BITE] [STYLE]
```

**End frame — גרסה B (העולם השתלט)**

```
Medium shot at eye level, 35mm lens. EINAT, at normal human size, sits at a white table by a sunlit window, holding a silver dessert spoon with a bite of the chocolate dessert, looking straight into the camera with a dry, satisfied half-smile. A turquoise sea with gentle waves now covers the entire tabletop, and the dessert stands in it like an island. A tiny white sailboat sails past her coffee cup. At the edge of the table the sea spills over as a small waterfall into a puddle on the white floor. Bright white room, warm sunlight.
[EINAT] [DESSERT] [RASPBERRY] [BITE] [STYLE]
```

**Video**

```
The camera pulls back and rises from plate height to an eye-level medium shot, revealing EINAT at normal size sitting at the table with the spoon in her hand. The small sea keeps moving around the plate with little lapping waves. The camera settles and holds. She looks into the lens with a dry half-smile and says one short line.
[STYLE]
```

את השפתיים מסנכרנים אחר כך, עם ההקלטה שלך ([sound.md](sound.md)).

---

## 6. מסך סיום

לא מייצרים ב־AI. המפרט ב־[shot-list.md](shot-list.md), שוט 6.
