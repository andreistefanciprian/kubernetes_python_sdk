FROM python:3.7-slim

RUN mkdir /app
WORKDIR /app
ADD main.py /app/
ADD requirements.txt /app/
RUN pip install -r requirements.txt

CMD ["python", "/app/main.py"]