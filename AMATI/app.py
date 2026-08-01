import os
import subprocess
import glob
import shutil
import tempfile
import asyncio

# Memaksa Gradio menginstal mesin Browser Chromium
print("Mengunduh mesin Chromium...")
subprocess.run(["playwright", "install", "chromium"])
print("Selesai mengunduh Chromium!")

import gradio as gr
from playwright.async_api import async_playwright
import imageio.v3 as iio
import imageio

# --- FITUR TUKANG SAPU OTOMATIS (VERSI PER USER) ---
def bersihkan_file_user(safe_task_id):
    try:
        print(f"Membersihkan sisa file render sebelumnya milik ID: {safe_task_id}...")
        temp_base = tempfile.gettempdir()
        # HANYA mencari dan menghapus folder milik user (task_id) yang sedang request
        tmp_folders = glob.glob(os.path.join(temp_base, f'gradio_render_{safe_task_id}*'))
        for folder in tmp_folders:
            if os.path.isdir(folder):
                shutil.rmtree(folder, ignore_errors=True)
    except Exception as e:
        print("Gagal membersihkan memori:", e)

async def render_video(js_code, resolution, duration, fps, task_id, bitrate):
    try:
        width, height = map(int, resolution.split("x"))
        duration = float(duration)
        fps = int(fps)
        total_frames = int(duration * fps)
        
        # Konversi Bitrate dari Mbps (megabit) ke bps (bit per second) untuk mesin FFMPEG
        target_bitrate = int(float(bitrate) * 1000000)
        
        # 1. Membuat ID Unik agar file tidak tertukar
        safe_task_id = "".join([c for c in str(task_id) if c.isalnum()])
        if not safe_task_id:
            safe_task_id = "default"
            
        # 2. Panggil fitur tukang sapu HANYA untuk ID user ini sebelum membuat folder baru
        bersihkan_file_user(safe_task_id)
            
        temp_dir_name = f"gradio_render_{safe_task_id}"
        temp_dir = tempfile.mkdtemp(prefix=temp_dir_name)
        mp4_path = os.path.join(temp_dir, f"output_{safe_task_id}.mp4")
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ margin: 0; padding: 0; background: transparent; overflow: hidden; }}
                svg {{ width: {width}px; height: {height}px; display: block; }}
            </style>
        </head>
        <body>
            <svg id="canvas" viewBox="0 0 {width} {height}" preserveAspectRatio="xMidYMid slice"></svg>
            <script>
                {js_code}
                const svgEl = document.getElementById('canvas');
                if (typeof create === 'function') {{ create(svgEl, {width}, {height}); }}
                window.renderFrameAtTime = function(time) {{
                    if (typeof update === 'function') {{ update(time, svgEl, {width}, {height}); }}
                }};
            </script>
        </body>
        </html>
        """
        html_path = os.path.join(temp_dir, "index.html")
        with open(html_path, "w") as f:
            f.write(html_content)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(viewport={"width": width, "height": height})
            await page.goto(f"file://{html_path}")
            await asyncio.sleep(1) 
            
            # PERUBAHAN KRUSIAL: Buka file MP4 untuk ditulis secara langsung (Streaming)
            writer = imageio.get_writer(mp4_path, fps=fps, codec='libx264', bitrate=target_bitrate)
            
            for i in range(total_frames):
                current_time = i / fps
                await page.evaluate(f"window.renderFrameAtTime({current_time})")
                screenshot_path = os.path.join(temp_dir, f"frame_{i:04d}.png")
                await page.screenshot(path=screenshot_path)
                
                # Baca frame, suntikkan ke MP4, lalu langsung hapus dari memori & hardisk
                frame_data = iio.imread(screenshot_path)
                writer.append_data(frame_data)
                os.remove(screenshot_path)
            
            # Tutup file MP4 setelah selesai dijahit
            writer.close()
            await browser.close()
            
            # --- PERUBAHAN KRUSIAL BASE64 ---
            # Kita baca file MP4 yang barusan jadi, lalu ubah jadi teks Base64
            import base64
            with open(mp4_path, "rb") as video_file:
                video_data = video_file.read()
                b64_string = base64.b64encode(video_data).decode("utf-8")
            
            # Hapus file MP4 fisik dari server Hugging Face (Langsung disapu!)
            os.remove(mp4_path)
            
            # Balikkan string Base64 yang diawali dengan header tipe datanya
            return f"data:video/mp4;base64,{b64_string}"
        
    except Exception as e:
        return f"Error saat render: {str(e)}"

# === ANTARMUKA GRADIO (API) ===
iface = gr.Interface(
    fn=render_video,
    inputs=[
        gr.Textbox(label="Kode Javascript (Fungsi create & update)", lines=10),
        gr.Textbox(value="1920x1080", label="Resolusi (contoh: 1920x1080)"),
        gr.Number(value=10, label="Durasi (detik)"),
        gr.Number(value=30, label="FPS (Kecepatan Frame)"),
        gr.Textbox(value="id_rahasia_1", label="Task ID (ID Unik Rendering)"),
        gr.Number(value=20, label="Bitrate (Mbps)") # TAMBAHAN: Input ke-6 untuk Bitrate
    ],
    # KITA UBAH OUTPUT-NYA JADI TEXTBOX KARENA MAU NGIRIM BASE64 STRING
    outputs=gr.Textbox(label="Base64 Output String"),
    title="Render MP4 AMATI"
)

if __name__ == "__main__":
    iface.launch(server_name="0.0.0.0", server_port=7860)
