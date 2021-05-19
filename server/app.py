import os
import sys
import gnsq
import signal
import multiprocessing
import json
import logging
from flask import flash, request, render_template, Flask
from db import init_db, add_task, get_tasks, task_pending, add_result
from work import count_words

SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///test.db')
NSQ_HTTP_HOST=os.getenv('NSQ_HTTP_HOST', 'localhost')
NSQ_HTTP_PORT=os.getenv('NSQ_HTTP_PORT', 4150)
NSQ_TOPIC=os.getenv('NSQ_TOPIC', 'counter')

app = Flask(__name__)
app.logger.setLevel(logging.INFO)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'super secret key')
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

consumer = gnsq.Consumer(NSQ_TOPIC, 'channel', f'{NSQ_HTTP_HOST}:{NSQ_HTTP_PORT}')


@app.route('/tasks', methods = ['GET', 'POST'])
def tasks():
    if request.method == 'POST':
        if not request.form['address']:
            flash('Enter site:')
        else:
            err, new_task = add_task(request.form['address'])
            if err:
                flash(str(err))
            else:
                task_dict = {
                        'id': new_task.id,
                        'address': new_task.address
                }
                try:
                    count_words.delay(task_dict)
                except Exception as e:
                    task_dict['error'] = str(e)
                    flash(task_dict['error'])
                    err = add_result(task_dict, do_finished=False)
                    if err:
                        flash(str(err))
                else:
                    err = task_pending(new_task)
                    if err:
                        flash(str(err))
    err, tasks = get_tasks()
    if err:
        flash(str(err))
        tasks = []
    return render_template('show_tasks.html', tasks = tasks)


@consumer.on_message.connect
def handler(consumer, message):
    try:
        task_dict = json.loads(message.body)
        app.logger.info(f'NSQ: {task_dict}')
    except (TypeError, json.JSONDecodeError) as e:
        app.logger.error(f'NSQ: {e}')
    else:
        with app.app_context():
            err = add_result(task_dict)
            if err:
                app.logger.error(f'NSQ: {err}')

def start_consumer():
    app.logger.info('start NSQ consumer')
    consumer.start()


@app.before_first_request
def startup():
    err = init_db(app)
    if err:
        app.logger.error(f'DB: {err}')
        sys.exit(1)
    app.logger.info('DB connect')
    proc.start()


def signal_handler(sig, frame):
    app.logger.warning('exit Ctrl+C')
    if proc.is_alive():
        proc.terminate()
    sys.exit(0)


proc = multiprocessing.Process(target=start_consumer)
signal.signal(signal.SIGINT, signal_handler)


if __name__ == '__main__':
    app.run()