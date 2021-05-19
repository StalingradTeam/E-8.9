FROM python:3.7
WORKDIR /app
COPY ./work/work.py /app
COPY ./server/app.py /app
COPY ./server/db.py /app
COPY ./server/templates/show_tasks.html /app/templates/
COPY ./server/requirements.txt /app/
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000
RUN pip install -r requirements.txt
CMD ["flask", "run"]