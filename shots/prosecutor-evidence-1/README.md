# שוט: התובע מציג את ראיה 1

כרטיס שוט להפקת AI. שוט ליפסינק אחד, 16:9, באותו אולם בית משפט של סצנות הפתיחה.

## קבצי מקור

| קובץ | מה זה |
|---|---|
| `prosecutor_frame.jpg` | תמונת התובע המקורית, 1672x941, הומרה מ WEBP ל JPG באיכות מקסימלית |
| `prosecutor_vo_pause.wav` | הדיבוב המקורי, נחתך בסוף הדיבור (10.446 שניות) ונוספה הפסקה שקטה. אורך 10.75 שניות |
| `prosecutor_vo_pause.mp3` | אותו אודיו ב MP3 320k, לכלים שלא מקבלים WAV |

ההפסקה בסוף נמדדה: שקט מ 10.40 עד 10.75, כלומר כ 0.35 שניות. המודל מייצר וידאו לכל אורך האודיו, כך שההפסקה נכנסת לשוט עצמו ולא צריך להקפיא פריים בעריכה.

## מפת הדיבור (נמדדה מהאודיו)

| קטע | זמן | הערה |
|---|---|---|
| 1 | 0.17 עד 0.91 | פתיחה |
| 2 | 1.34 עד 3.41 | |
| 3 | 3.88 עד 5.95 | |
| 4 | 6.93 עד 8.19 | אחרי השקט הארוך ביותר (כמעט שנייה). כנראה ״כעבור שבע דקות״ |
| 5 | 8.64 עד 10.45 | כנראה ״היא כבר ניהלה את כל האירוע״ |

השיוך של המשפטים לקטעים 4 ו 5 הוא הערכה לפי מבנה השקטים. לא בוצע תמלול.

## כרטיס שוט

- **תמונת מקור:** `prosecutor_frame.jpg` כפריים פתיחה, `prosecutor_vo_pause.mp3` כאודיו מניע.
- **קומפוזיציה:** מדיום קלוז אפ, התובע במרכז ימין, תיק ״ראיה 1״ בצד שמאל של הפריים, דגל ישראל וקהל מטושטש ברקע. 16:9.
- **פעולה מרכזית:** פונה לשופט מחוץ לפריים בימין, אצבע מורמת, מבט חמור.
- **מצלמה:** חצובה נעולה, פוש אין איטי ועדין מאוד לכל אורך השוט.
- **תאורה ואווירה:** מנורות קיר חמות על חיפוי עץ כהה, ערב, טמפרטורת צבע חמה.
- **פרטי רציפות:** חליפה שחורה, חולצה לבנה, עניבה שחורה, זקן אפור קצר, תיק שחור עם מדבקת ״ראיה 1״ אדומה. הרקע לא משתנה.
- **לבדוק בתוצאה:** אצבע מורמת (מספר אצבעות, עיוות), המדבקה על התיק נשארת קריאה, סנכרון שפתיים בעברית, שאין חיוך או משחק קומי, שהפה נסגר בהפסקה בסוף.

### מודל מומלץ

**Omnihuman 1.5** דרך Hedra: מקבל פריים פתיחה, אודיו ופרומפט, ומפיק 16:9 ב 1080p. מחיר מחירון: 16 סנט לשנייה, שנייה חלקית מחויבת כשלמה, כלומר 11 שניות.

### פרומפט

```
Photorealistic cinematic medium close-up in a dark wood-paneled Israeli courtroom, warm wall sconces, Israeli flag and a blurred gallery behind him. The same prosecutor from the start frame: black suit, white shirt, black tie, short grey beard. He holds the black evidence binder labeled "ראיה 1" against his body with his left hand, the label unchanged, and keeps his right index finger raised. He addresses the judge just off-camera to the right with a very stern, grave expression, speaking Hebrew with precise lip sync to the audio.
Beat 1: absolute seriousness, finger raised, almost no body movement.
Beat 2: on the words "don't touch anything" he stresses each word with a small, controlled downward tap of the raised hand.
Beat 3: on "seven minutes later" he glances down briefly at the binder, then lifts his eyes back to the judge.
Beat 4: the final line "she was already running the whole event" is delivered with heavy gravity, as if exposing a serious crime, a slight lean forward, eyes locked on the judge.
After the last word he holds still with his mouth closed and a stern gaze for a brief beat.
Camera: locked on a tripod, only a very slow, subtle push-in. Natural skin texture, consistent identity, wardrobe, binder and background. No subtitles, no on-screen text, no exaggerated gestures, no comedic acting.
```

### חלופה אם הביצוע נכשל

אם האצבע או המדבקה מתעוותות: להריץ שוב עם פרומפט שמוריד את תנועות היד הקטנות ומשאיר רק את המבט אל התיק בקטע 4. אם הסנכרון חלש: לנסות Kling AI Avatar v2 Pro עם אותם קבצים.
