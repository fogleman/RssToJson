from flask import Flask, request, jsonify, abort, current_app
from functools import wraps
from lxml.html.clean import clean_html
import datetime
import feedparser
import hashlib
import time

app = Flask(__name__)

USER_AGENT = 'RssToJson/1.0'

def create_entry_id(entry):
    keys = ['id', 'link', 'title']
    value = '\n'.join(entry.get(key, '') for key in keys)
    return hashlib.md5(value.encode('utf-8')).hexdigest()

def parse(url, etag=None, modified=None):
    print etag, modified
    data = feedparser.parse(url,
        etag=etag, modified=modified, agent=USER_AGENT)
    entries = []
    feed = data.get('feed', {})
    for entry in data.get('entries', []):
        description = entry.get('description')
        description = description and clean_html(description)
        timestamp = entry.get('date_parsed')
        timestamp = timestamp and datetime.datetime(*timestamp[:6]).isoformat()
        entry = {
            'id': create_entry_id(entry),
            'author': entry.get('author'),
            'link': entry.get('link'),
            'title': entry.get('title'),
            'description': description,
            'timestamp': timestamp,
        }
        entries.append(entry)
    return {
        'url': url,
        'entries': entries,
        'feed': {
            'title': feed.get('title'),
            'link': feed.get('link'),
        },
        'etag': data.get('etag'),
        'modified': data.get('modified'),
    }

def jsonp(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        callback = request.args.get('callback')
        if callback:
            content = func(*args, **kwargs).data
            content = '%s(%s);' % (callback, content)
            return current_app.response_class(content,
                mimetype='application/javascript')
        else:
            return func(*args, **kwargs)
    return decorated_function

@app.route('/')
@jsonp
def index():
    if 'url' not in request.args:
        abort(404)
    url = request.args['url']
    etag = request.args.get('etag') or None
    modified = request.args.get('modified') or None
    return jsonify(parse(url, etag, modified))

if __name__ == '__main__':
    app.run(debug=True)
