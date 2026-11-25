import sys, subprocess, numpy as np, sherpa_onnx, json
M, prefix, audio, tests = sys.argv[1], sys.argv[2], sys.argv[3], json.loads(sys.argv[4])
rec = sherpa_onnx.OfflineRecognizer.from_whisper(
    encoder=f'{M}/{prefix}-encoder.int8.onnx', decoder=f'{M}/{prefix}-decoder.int8.onnx',
    tokens=f'{M}/{prefix}-tokens.txt', language='he', task='transcribe', num_threads=4)
raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', audio, '-ac', '1', '-ar', '16000', '-f', 'f32le', '-'], capture_output=True).stdout
x = np.frombuffer(raw, np.float32)
for label, a, ends in tests:
    print('--', label)
    for b in ends:
        s = rec.create_stream(); s.set_option('max_tokens_per_second', '40')
        pad = np.zeros(4000, np.float32)
        s.accept_waveform(16000, np.concatenate([pad, x[int(a * 16000):int(b * 16000)], pad]))
        rec.decode_stream(s)
        print(f'   {a:5.2f}->{b:5.2f}  {s.result.text.strip()}', flush=True)
