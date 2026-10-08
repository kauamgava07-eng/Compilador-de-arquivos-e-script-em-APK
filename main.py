from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile, BadZipFile
import os, shutil, subprocess, uuid

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

app = FastAPI(title="Script2APK API", version="0.1.0")

# Development-only CORS. Restrict this to your actual domain in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

MAX_UPLOAD = 50 * 1024 * 1024
WORK_ROOT = Path(os.environ.get("SCRIPT2APK_WORKDIR", "/tmp/script2apk"))
WORK_ROOT.mkdir(parents=True, exist_ok=True)
TEMPLATE = Path(__file__).resolve().parents[1] / "android-template"

@app.get("/health")
def health():
    return {"ok": True, "service": "Script2APK API", "version": "0.1.0"}

def safe_extract(zip_path: Path, destination: Path):
    total = 0
    with ZipFile(zip_path) as z:
        for info in z.infolist():
            name = info.filename.replace("\\", "/")
            p = Path(name)
            if p.is_absolute() or ".." in p.parts:
                raise HTTPException(400, "O ZIP contém caminho inseguro.")
            total += info.file_size
            if total > 200 * 1024 * 1024:
                raise HTTPException(413, "O conteúdo descompactado excede 200 MB.")
        z.extractall(destination)

def find_web_root(folder: Path):
    matches = list(folder.rglob("index.html"))
    # Ignore common hidden/build folders.
    matches = [p for p in matches if not any(part.startswith(".") for part in p.relative_to(folder).parts)]
    if not matches:
        return None
    # Prefer root index.html, otherwise the shallowest index.html.
    return sorted(matches, key=lambda p: (len(p.relative_to(folder).parts), str(p)))[0].parent

@app.post("/api/build")
async def build(file: UploadFile = File(...)):
    filename = file.filename or "project.zip"
    if not filename.lower().endswith(".zip"):
        raise HTTPException(400, "Envie um projeto compactado em .zip.")
    job = WORK_ROOT / str(uuid.uuid4())
    job.mkdir(parents=True, exist_ok=False)
    zip_path = job / "upload.zip"
    try:
        data = await file.read(MAX_UPLOAD + 1)
        if len(data) > MAX_UPLOAD:
            raise HTTPException(413, "O ZIP deve ter no máximo 50 MB.")
        zip_path.write_bytes(data)
        source = job / "source"
        source.mkdir()
        try:
            safe_extract(zip_path, source)
        except BadZipFile:
            raise HTTPException(400, "O arquivo ZIP está inválido.")

        web_root = find_web_root(source)
        if web_root:
            project = job / "android-project"
            shutil.copytree(TEMPLATE, project)
            assets = project / "app" / "src" / "main" / "assets" / "www"
            assets.mkdir(parents=True, exist_ok=True)
            shutil.copytree(web_root, assets, dirs_exist_ok=True)
            # Build only when Gradle and Android SDK are installed.
            gradle = shutil.which("gradle")
            sdk = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
            if not gradle or not sdk:
                return {
                    "status": "prepared",
                    "message": "Projeto HTML reconhecido e preparado. Para gerar o APK, configure JDK 17, Gradle e Android SDK no servidor.",
                    "project_type": "web",
                    "job_id": job.name,
                }
            env = os.environ.copy()
            env["ANDROID_HOME"] = sdk
            env["ANDROID_SDK_ROOT"] = sdk
            proc = subprocess.run(
                [gradle, "--no-daemon", "assembleDebug"],
                cwd=project, env=env, capture_output=True, text=True, timeout=900
            )
            apk = project / "app" / "build" / "outputs" / "apk" / "debug" / "app-debug.apk"
            if proc.returncode != 0 or not apk.exists():
                detail = (proc.stderr or proc.stdout)[-5000:]
                return {"status": "error", "message": "A compilação falhou.", "details": detail}
            out = job / "Script2APK-debug.apk"
            shutil.copy2(apk, out)
            return FileResponse(out, media_type="application/vnd.android.package-archive",
                                filename="Script2APK-debug.apk")
        # Detect Android Gradle projects for a helpful response; do not execute arbitrary builds by default.
        gradle_files = list(source.rglob("settings.gradle")) + list(source.rglob("settings.gradle.kts"))
        if gradle_files:
            return {
                "status": "recognized",
                "project_type": "android-gradle",
                "message": "Projeto Android Gradle reconhecido. A compilação arbitrária está desativada neste protótipo por segurança. Use um runner isolado com Gradle/SDK configurados.",
                "next_step": "Importe o projeto num ambiente de build Android confiável e compile com assembleDebug."
            }
        if list(source.rglob("project.godot")):
            return {"status": "unsupported", "project_type": "godot",
                    "message": "Projeto Godot detectado. É necessário exportar com a versão correta do Godot, Android build template e SDK."}
        if list(source.rglob("*.py")):
            return {"status": "unsupported", "project_type": "python",
                    "message": "Scripts Python detectados. Python não vira APK diretamente; é necessário escolher uma abordagem, como Kivy/Buildozer ou Chaquopy."}
        return {"status": "unknown", "message": "Não encontrei index.html, settings.gradle ou project.godot no ZIP."}
    except HTTPException:
        shutil.rmtree(job, ignore_errors=True)
        raise
    except subprocess.TimeoutExpired:
        return {"status": "error", "message": "Tempo limite de compilação excedido."}
    except Exception as exc:
        return {"status": "error", "message": f"Erro ao processar projeto: {type(exc).__name__}"}
    finally:
        await file.close()
