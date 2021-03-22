FROM python:3.6

COPY requirements.txt /

RUN pip install -r /requirements.txt

COPY assets/ /assets
COPY static/ /static
COPY *.py /

CMD [ "python3", "./app.py" ]
