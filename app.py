from calendar import timegm
from datetime import datetime, timedelta
import json
import os
from flask import Flask, request, redirect, url_for
from redis import Redis
from wsgi_body_copy import WSGICopyBody

app = Flask(__name__)
app.wsgi_app = WSGICopyBody(app.wsgi_app)

REDIS_URL = os.environ.get('REDISTOGO_URL', 'redis://localhost:6379/')
con = Redis.from_url(REDIS_URL)

WEBHOOKS_KEY = 'webhooks'
MAX_AGE = int(os.environ.get('WEBHOOK_LISTENER_MAX_AGE', 5))


@app.route('/webhook', methods=['POST'])
def log_webhook():
    print request.headers
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')

    now = datetime.now()
    score = timegm(now.utctimetuple())

    max_age = now - timedelta(days=MAX_AGE)
    max_age_score = timegm(max_age.utctimetuple())

    data = request.environ['body_copy']
    print data

    con.zadd(WEBHOOKS_KEY, **{"%s: %s" % (ts, data): score})
    con.zremrangebyscore(WEBHOOKS_KEY, '-inf', '(%s' % max_age_score)

    return 'thanks!'


@app.route('/', methods=['GET'])
def base():
    return redirect(url_for('recent-webhooks'))


@app.route('/recent', methods=['GET'], endpoint="recent-webhooks")
def display_recent_webhooks():
    print request.headers
    fired_webhooks = con.zrevrangebyscore(WEBHOOKS_KEY, '+inf', '-inf', 0, 200)
    return "<pre>%s</pre>" % "\n".join(fired_webhooks)


@app.route('/clear', methods=['POST'])
def clear_webhook_list():
    print request.headers
    return json.dumps(con.delete(WEBHOOKS_KEY))

if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
