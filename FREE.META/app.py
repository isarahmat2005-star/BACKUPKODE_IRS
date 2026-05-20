import os
import subprocess
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Izinkan FREE META dari browser mana pun untuk mengakses server ini (Anti-CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/convert")
async def convert_vector_to_jpg(file: UploadFile = File(...)):
    # Ambil ekstensi file
    ext = file.filename.split(".")[-1].lower()
    if ext not in ["eps", "ai"]:
        raise HTTPException(status_code=400, detail="Hanya menerima file EPS atau AI!")

    input_path = f"temp_input.{ext}"
    output_path = "temp_output.jpg"

    try:
        # 1. Simpan file kiriman dari FREE META ke penyimpanan sementara server
        content = await file.read()
        with open(input_path, "wb") as f:
            f.write(content)

        # 2. Perintah sakti Ghostscript untuk mengonversi EPS/AI menjadi JPEG kualitas tinggi
        gs_cmd = [
            "gs",
            "-q",
            "-dNOPAUSE",
            "-dBATCH",
            "-sDEVICE=jpeg",
            "-dJPEGQ=90",
            "-r150",
            # OBAT SAKTI: Potong gambar pas sesuai bounding box (hilangkan putih kosong)
            "-dEPSCrop", 
            f"-sOutputFile={output_path}",
            input_path
        ]
        
        # Jalankan mesin Ghostscript di dalam sistem Linux
        result = subprocess.run(gs_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Gagal konversi: {result.stderr.decode()}")

        # 3. Baca hasil gambar JPEG yang sudah jadi
        with open(output_path, "rb") as f:
            jpg_data = f.read()

        # 4. Kirimkan balik gambar bersihnya ke FREE META
        return Response(content=jpg_data, media_type="image/jpeg")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        # Bersihkan file sampah di server agar penyimpanan tidak penuh
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)
