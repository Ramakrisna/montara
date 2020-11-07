FROM python:3.8

WORKDIR /app

COPY requirements.txt requirements.txt
RUN python -m venv venv
RUN venv/bin/pip install -r requirements.txt
RUN venv/bin/pip install gunicorn pymysql

COPY app app
COPY migrations migrations
COPY montara.py config.py boot.sh ./
RUN chmod +x boot.sh

ENV FLASK_APP montara.py
ENV FLASK_DEBUG 1

EXPOSE 5000

ENTRYPOINT ["./boot.sh"]