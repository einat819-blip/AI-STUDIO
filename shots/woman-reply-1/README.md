# שוט: האישה עונה לשופט

כרטיס שוט להפקת AI. שוט ליפסינק אחד, 16:9, באותו אולם בית משפט, באותו טיפול כמו שוט התובע (`shots/prosecutor-evidence-1`).

## קבצי מקור

| קובץ | מה זה |
|---|---|
| `woman_frame.jpg` | תמונת האישה המקורית, 1672x941. זהה לתמונה שכבר נמצאת בספריית Hedra בשם "Woman Speaking at a Hearing" |
| `woman_vo_trim.wav` | הדיבוב המקורי (OGG), חתוך: 0.31 שניות לפני ״סליחה״, נגמר אחרי ״מזעזע״, ואחריו 0.9 שניות שקט לצחוק. אורך 5.72 שניות, בדיוק המשבצת של סצנה 2 בעריכה |
| `woman_vo_trim.mp3` | אותו אודיו ב MP3 320k, להעלאה ל Hedra |

**חיתוך:** בקובץ המקורי היו 1.42 שניות של שקט לפני המילה הראשונה, ואחרי ״מזעזע״ היה עוד משפט, ״אני לא יכולה לעבוד ככה״, שלא מופיע בתסריט. שניהם הוסרו. הטקסט שנשאר: ״סליחה רגע, מי אחראי פה על התאורה? זה פשוט מזעזע.״

**עדכון:** זה השוט של סצנה 2 (עינת מתלוננת על התאורה) בעריכת חלק 1, `edits/part1`. גרסה קודמת של הקובץ הזה כללה גם את המשפט הנוסף. אם הורדת אותה, צריך להחליף.

**איכות:** הקובץ המקורי הוא הודעה קולית ב 19kbps. לסנכרון שפתיים זה מספיק, אבל הוא יישמע חלש יותר מהדיבוב של התובע. אם יש ייצוא באיכות גבוהה של אותה הקלטה, עדיף להשתמש בו.

## מפת הדיבור (נמדדה מהאודיו החתוך)

| קטע | זמן |
|---|---|
| ״סליחה רגע,״ | 0.31 עד 1.48 |
| ״מי אחראי פה על התאורה? זה פשוט מזעזע.״ | 1.64 עד 4.83 |
| הפסקה לצחוק | 4.83 עד 5.72 |

הטקסט אומת בתמלול. לפי התסריט ההערה צריכה להישמע מקצועית ורצינית, לא כמו בדיחה.

## כרטיס שוט

- **תמונת מקור:** `asset_6d1c64c9-b422-475b-992e-04b912e61266` בספריית Hedra.
- **קומפוזיציה:** קלוז אפ, האישה במרכז, דגל ישראל מאחורי כתף שמאל שלה (ימין הפריים), קהל מטושטש משמאל, מיקרופון שחור בפינה הימנית התחתונה.
- **פעולה מרכזית:** עונה לשופט מחוץ לפריים, בהתגוננות רגועה ומעט מתפלאת, עם תנועת כף יד פתוחה.
- **מצלמה:** חצובה נעולה, פוש אין איטי ועדין מאוד.
- **תאורה ואווירה:** אור יום רך מצד ימין, חיפוי עץ חם, כמו בשוט התובע.
- **פרטי רציפות:** שיער בלונדיני עם שורשים כהים בקוקו גבוה ומבולגן, בלייזר שחור, שרשרת כסף דקה, עגילי חישוק קטנים. הרקע והמיקרופון לא משתנים.
- **לבדוק בתוצאה:** כף היד הפתוחה (מספר אצבעות), השיער הרופף לא "זז" בלי סיבה, המיקרופון נשאר במקום, סנכרון שפתיים בעברית, הפה נסגר בהפסקה בסוף.

### מודל

**Omnihuman 2.0** ב Hedra, 720p, כמו שוט התובע, כדי ששני השוטים ייראו אותו דבר כשהם נחתכים זה לזה.

### פרומפט

```
Photorealistic cinematic close-up in the same dark wood-paneled Israeli courtroom, soft daylight from the right, Israeli flag behind her, blurred gallery on the left. The same woman from the start frame: highlighted blonde hair with dark roots in a messy high ponytail with loose strands, black blazer, thin silver necklace, small hoop earrings, seated at a desk with a black microphone in the lower right corner. She answers the judge just off-camera to the right, speaking Hebrew with precise lip sync to the audio.
Her attitude: a serious, professional complaint about the courtroom lighting, critical and matter-of-fact, as if she is the only competent person in the room. A small open-palm gesture with her raised hand while she speaks, a critical glance up toward the ceiling lights, eyebrows slightly raised. No smiling, not trying to be funny.
After the last word she closes her mouth and holds a steady, unimpressed look at the judge for the remaining beat.
Camera: locked on a tripod, only a very slow, subtle push-in. Natural skin texture, consistent identity, hair, wardrobe, microphone and background. No subtitles, no on-screen text, no exaggerated gestures, no comedic mugging.
```

### חלופה אם הביצוע נכשל

אם כף היד מתעוותת: להריץ שוב בלי תנועת היד ולהשאיר רק מבט והטיית ראש. אם המשחק יוצא קומי מדי: להוריד את ״incredulous״ ולהשאיר ״calm, defensive, matter-of-fact״.
