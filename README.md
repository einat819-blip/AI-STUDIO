# AI-STUDIO

מאגר העבודה של AI NATI STUDIOS.

## סקיל: מנהל הקריאייטיב וההפקה של AI NATI STUDIOS

התיקייה: `.claude/skills/ainati-creative-director/`

| קובץ | מה יש בו |
|---|---|
| `SKILL.md` | ההנחיות המלאות ותיאור ההפעלה |
| `references/templates.md` | תבניות: טבלת שוטים, כרטיס שוט להפקת AI, כרטיס דוגמה ממחקר, תכנון ניסוי |
| `references/video-review.md` | איך לבדוק סרטון בפועל ומה הבדיקה לא מראה |
| `scripts/inspect_video.sh` | מפת שוטים, פריימים עם חותמת זמן, עוצמת סאונד ושקטים מתוך קובץ וידאו |

### התקנה

- **Claude Code בתוך המאגר הזה:** הסקיל נטען אוטומטית מתוך `.claude/skills`.
- **Claude Code בכל פרויקט:** העתיקי את התיקייה `ainati-creative-director` אל `~/.claude/skills/`.
- **Claude באתר ובאפליקציה:** העלי את `dist/ainati-creative-director.zip` באזור הסקילים בהגדרות. אם כבר קיים אצלך סקיל בשם הזה, החליפי אותו כדי שלא יפעלו שתי גרסאות במקביל.

### עדכון

אחרי שינוי בתיקיית הסקיל, צרי מחדש את קובץ ה ZIP מתיקיית השורש של המאגר:

```bash
rm -f dist/ainati-creative-director.zip
(cd .claude/skills && zip -r ../../dist/ainati-creative-director.zip ainati-creative-director)
```
