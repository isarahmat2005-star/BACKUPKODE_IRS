FROM python:3.9

USER root

RUN apt-get update && apt-get install -y ffmpeg libsm6 libxext6 libxrender-dev

COPY ./requirements.txt /requirements.txt
RUN pip install --no-cache-dir --upgrade -r /requirements.txt

RUN playwright install chromium
RUN playwright install-deps chromium

RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app
COPY --chown=user . $HOME/app

EXPOSE 7860
CMD ["python", "app.py"]
