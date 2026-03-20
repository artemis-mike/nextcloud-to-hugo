FROM python:3.14-alpine

RUN apk add --no-cache pandoc git git-lfs bash imagemagick imagemagick-gif imagemagick-jpeg

RUN ["mkdir", "/nextcloud-to-hugo"]
WORKDIR /nextcloud-to-hugo
COPY ./source .
RUN ["python3", "-m", "pip", "install", "-r", "requirements.txt"]

ENTRYPOINT ["./entrypoint.sh"]