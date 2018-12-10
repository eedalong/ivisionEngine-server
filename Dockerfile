FROM python:3.6.5

ENV HOME=/app

WORKDIR $HOME

COPY requirements.txt $HOME
RUN pip install --trusted-host mirrors.cloud.tencent.com \
    -i http://mirrors.cloud.tencent.com/pypi/simple/ -r requirements.txt

COPY . $HOME

EXPOSE 80

ENV PYTHONUNBUFFERED=true
CMD ["gunicorn", "app.wsgi", "-b", "0.0.0.0:80", "--access-logfile", "-", "--log-level", "info"]
