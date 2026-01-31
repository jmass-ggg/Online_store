
FROM python:3.12-slim


WORKDIR /app

COPY requirements.txt .

EXPOSE 8080

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD ["uvicorn","backend.main:app","--host","0.0.0.0","--port","8080","--reload"]

