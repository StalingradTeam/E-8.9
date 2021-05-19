FROM python:3.7
WORKDIR /app
COPY work.py /app
COPY requirements.txt /app/
RUN pip install -r requirements.txt
CMD celery -A work work --loglevel=INFO