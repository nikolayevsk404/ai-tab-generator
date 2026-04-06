from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from app.agent.audio_to_tab_agent import AudioToTabAgent

app = FastAPI(title="AI Tab Generator Service", version="0.1.0")
agent = AudioToTabAgent()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/process-audio")
async def process_audio(
    audio: UploadFile = File(...),
    job_id: str | None = Form(default=None),
    filename: str | None = Form(default=None),
) -> dict:
    try:
        contents = await audio.read()
        result = agent.run(
            audio_bytes=contents,
            filename=filename or audio.filename or "upload.wav",
            job_id=job_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"Audio processing failed: {exc}") from exc

    return result
