
# FROM python:3.11-slim


# ENV PYTHONDONTWRITEBYTECODE=1
# ENV PYTHONUNBUFFERED=1

# WORKDIR /app

# COPY requirements.txt .

# RUN pip install --upgrade pip
# RUN pip install -r requirements.txt

# COPY . .

# EXPOSE 8000

# CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

FROM python:12.3

WORKDIR /app

COPY requirements.txt .

EXPOSE 8080

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD ["uvicorn","backend.main:app","--host","0.0.0.0","--port","8080","--reload"]

