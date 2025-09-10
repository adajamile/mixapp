from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
from uuid import uuid4
import subprocess
from utils import normalize_loudness

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

app = FastAPI(title="LUFS Normalizer API", version="1.0.0")

# Durante testes, CORS liberado. Depois, restrinja para seu domínio.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_headers=["*"],
    allow_methods=["*"],
)

@app.get("/")
async def root():
    return {"ok": True, "service": "LUFS Normalizer API"}

@app.post("/normalize")
async def normalize(
    target_lufs: float = Form(...),
    file: UploadFile = File(None),
    url: str = Form(None),
    out_ext: str = Form("mp3")
):
    if not file and not url:
        raise HTTPException(400, "Forneça 'file' OU 'url'.")

    if file:
        in_path = DATA_DIR / f"in_{uuid4().hex}_{file.filename}"
        with in_path.open("wb") as f:
            f.write(await file.read())
        in_source = str(in_path)
    else:
        in_source = url  # URL direta (com direitos)

    out_name = f"norm_{uuid4().hex}.{out_ext.lower()}"
    out_path = DATA_DIR / out_name

    try:
        info = normalize_loudness(in_source, float(target_lufs), str(out_path))
    except subprocess.CalledProcessError as e:
        raise HTTPException(500, (e.stderr or e.stdout).decode("utf-8", "ignore")[:400])

    return JSONResponse({
        "ok": True,
        "target_lufs": target_lufs,
        "output_file": out_name,
        "public_url": f"/static/{out_name}",
        "ffmpeg_info": info,
    })

@app.get("/static/{fname}")
async def static_file(fname: str):
    fpath = DATA_DIR / fname
    if not fpath.exists():
        raise HTTPException(404, "Arquivo não encontrado.")
    return FileResponse(fpath)
