import os
from celery import Celery
from celery.utils.log import get_task_logger
import json
import requests

REDIS_HOST=os.getenv('REDIS_HOST', 'localhost')

NSQ_HTTP_HOST=os.getenv('NSQ_HTTP_HOST', 'localhost')
NSQ_HTTP_PORT=os.getenv('NSQ_HTTP_PORT', 4151)
NSQ_TOPIC=os.getenv('NSQ_TOPIC', 'counter')
NSQ_TIMEOUT=os.getenv('NSQ_TIMEOUT', 3)

EXPIRES=os.getenv('RESULT_EXPIRES', 300)

WORD = os.getenv('COUNT_WORD', 'python')
TIMEOUT = os.getenv('COUNT_TIMEOUT', 10)

app = Celery('counter',
        broker=f'redis://{REDIS_HOST}', backend=f'redis://{REDIS_HOST}')
logger = get_task_logger(__name__)


app.conf.update(
    result_expires=EXPIRES,
)

@app.task
def count_words(task):
    try:
        site = task.get('address', '')
    except (KeyError, TypeError, AttributeError) as e:
        logger.error(task)
        logger.error(e)
        return False

    if not site.startswith("http://") and not site.startswith("https://"):
        site = f'http://{site}'
    try:
        resp = requests.get(site, timeout=TIMEOUT)
    except Exception as e:
        task['error'] = str(e)
    else:
        task['http_status_code'] = resp.status_code
        task['words_count'] = resp.text.count(WORD)
    try:
        nsq_resp = requests.post(f'http://{NSQ_HTTP_HOST}:{NSQ_HTTP_PORT}/pub?topic={NSQ_TOPIC}',
                json.dumps(task), timeout=NSQ_TIMEOUT)
    except Exception as e:
        logger.error(e)
        return False
    return task