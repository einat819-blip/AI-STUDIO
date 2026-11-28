# -*- coding: utf-8 -*-
"""v6 short variant: identical to edit_v6.py except that the section
"ואם כל זה לא מתאים לכם, יש לנו פתרון נוסף. / אנחנו פשוט לא מגיעים."
(binoculars + map shot, plan 25.75-31.35 s) is removed. Its punch repeats what the
control room and the CEO now deliver. Saves 5.6 s.
"""
import os

CUT = [(25.75, 31.35)]
_here = os.path.dirname(os.path.abspath(__file__))
exec(compile(open(os.path.join(_here, "edit_v6.py"), encoding="utf-8").read(), os.path.join(_here, "edit_v6.py"), "exec"))

# The pickup-point jingle now runs straight into the flag shot: make the second
# jingle cue continue the first one seamlessly (no jump in the music).
_m = list(MUSIC)
for _i, _e in enumerate(_m):
    if _e[2] == "jingle_commercial" and abs(_e[3] - JB * 6) < 1e-6:
        _first = _i
    if _e[2] == "jingle_commercial" and abs(_e[3] - JB * 8) < 1e-6:
        _second = _i
_gap = T(31.38) - T(22.05)
_e1, _e2 = list(_m[_first]), list(_m[_second])
_e1[7] = 0.0           # no fade-out at the join
_e2[3] = JB * 6 + _gap  # continue where the first cue is
_e2[6] = 0.0           # no fade-in at the join
_m[_first], _m[_second] = tuple(_e1), tuple(_e2)
MUSIC = _m
