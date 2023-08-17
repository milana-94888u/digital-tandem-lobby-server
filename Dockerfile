FROM python:3.11

WORKDIR /usr/src

COPY requirements.txt .

RUN python3.11 -m pip install --upgrade pip
RUN python3.11 -m pip install --no-cache-dir -r requirements.txt

COPY src .

CMD uvicorn main:app --reload --host 0.0.0.0 --port 8000
