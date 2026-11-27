import subprocess, re, sys
p = subprocess.run(['ffmpeg','-nostats','-v','info','-i',sys.argv[1],'-af','ebur128=framelog=info','-f','null','-'],capture_output=True,text=True).stderr
rows = re.findall(r't: *([0-9.]+) .*?M: *(-?[0-9.]+)', p)
out = {}
for t, m in rows:
    t = float(t); k = round(t * 2) / 2
    if abs(t - k) < 0.051 and k not in out: out[k] = float(m)
print(' '.join(f"{k:.1f}:{v:.0f}" for k, v in sorted(out.items())))
