FROM python:3.14-alpine

RUN apk add pandoc git git-lfs

RUN ["mkdir", "/nextcloud-to-hugo"]
WORKDIR /nextcloud-to-hugo
COPY ./source .
RUN ["python3", "-m", "pip", "install", "-r", "requirements.txt"]

ENTRYPOINT ["./entrypoint.sh"]