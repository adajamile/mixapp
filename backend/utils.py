import subprocess, json, shlex

def _run(cmd: str):
    p = subprocess.run(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return p.stdout, p.stderr

def normalize_loudness(in_source: str, target_lufs: float, out_path: str):
    """
    Normaliza em one-pass com loudnorm (EBU R128).
    Exporta MP3 192k por padrao.
    """
    cmd = (
        f'ffmpeg -y -hide_banner -nostats -i "{in_source}" '
        f'-filter_complex "loudnorm=I={target_lufs}:TP=-1.0:LRA=11:print_format=json" '
        f'-c:a libmp3lame -b:a 192k "{out_path}"'
    )
    out, err = _run(cmd)
    meta = err.decode("utf-8", "ignore")
    start = meta.find("{"); end = meta.rfind("}")
    info = {}
    if 0 <= start < end:
        try:
            info = json.loads(meta[start:end+1])
        except:
            info = {"raw": meta[-800:]}
    return info
