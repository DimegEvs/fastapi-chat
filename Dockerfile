FROM python:3.11

COPY requirements.txt requirements.txt

RUN pip install -r /requirements.txt

COPY . /app-chat
WORKDIR /app-chat


CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8001"]