FROM python:3.10-slim

# Instal Ghostscript untuk merender EPS dan alat sistem pendukung
RUN apt-get update && apt-get install -y \
    ghostscript \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY . .

# Port standar yang diwajibkan oleh Hugging Face Spaces
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
