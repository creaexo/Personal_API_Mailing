FROM python:3.9-alpine3.16

COPY requirements.txt /temp/requirements.txt
COPY mailing /mailing
WORKDIR /mailing
EXPOSE 8000

RUN apk add postgresql-client build-base postgresql-dev

RUN pip install --upgrade pip

RUN pip install -r /temp/requirements.txt

RUN adduser --disabled-password service-adduser

USER service-adduser

