FROM python:3.14.4

WORKDIR /usr/local/src

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY alembic.ini alembic.ini
COPY app app
EXPOSE 8000

RUN useradd app
USER app

CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]

