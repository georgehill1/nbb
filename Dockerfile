FROM ubuntu:16.04

MAINTAINER George Hill "nerdboardblog@gmail.com"

RUN apt-get update -y && apt-get install -y python-pip python-dev gunicorn3

COPY requirements.txt /app/requirements.txt

WORKDIR /app

RUN adduser -D myuser
USER myuser

RUN pip install -r requirements.txt

COPY . /app

CMD [ "gunicorn", "app:app" ]
