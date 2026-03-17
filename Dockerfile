FROM python:3.13-rc-alpine3.18

RUN apk add pandoc

RUN ["mkdir", "/nextcloud-to-hugo"]
RUN ["python3", "-m", "pip", "install", "-r", "requirements.txt"]
WORKDIR /nextcloud-to-hugo
COPY ./source .

ENTRYPOINT ["./entrypoint.sh"]