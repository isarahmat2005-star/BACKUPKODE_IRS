import os
import subprocess
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/convert")
async def convert_vector_to_jpg(file: UploadFile = File(...)):
    ext = file.filename.split(".")[-1].lower()
    if ext not in ["eps", "ai"]:
        raise HTTPException(status_code=400, detail="Hanya menerima file EPS atau AI!")

    # BIKIN NAMA FILE UNIK UNTUK MENCEGAH BENTROK ANTAR USER
    unique_id = uuid.uuid4().hex
    input_path = f"temp_input_{unique_id}.{ext}"
    output_path = f"temp_output_{unique_id}.jpg"

    try:
        content = await file.read()
        with open(input_path, "wb") as f:
            f.write(content)

        gs_cmd = [
            "gs",
            "-q",
            "-dNOPAUSE",
            "-dBATCH",
            "-sDEVICE=jpeg",
            "-dJPEGQ=90",
            "-r150",
            "-dEPSCrop", 
            f"-sOutputFile={output_path}",
            input_path
        ]
        
        result = subprocess.run(gs_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Gagal konversi: {result.stderr.decode()}")

        with open(output_path, "rb") as f:
            jpg_data = f.read()

        return Response(content=jpg_data, media_type="image/jpeg")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        # File tetap dihapus secara otomatis dan aman
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)
