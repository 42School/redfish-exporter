import json
import logging
import traceback

from flask import Flask, request, Response
from time import strftime
from datetime import datetime, timezone
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from logging.handlers import RotatingFileHandler
from logging.config import dictConfig

from .simple_exporter import metricHandler

config_file = "./config.yaml"

""" Configure logging """
dictConfig({
    "version": 1,
    "formatters": {"default": {
        "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
    }},
    "handlers": {"wsgi": {
        "class": "logging.StreamHandler",
        "stream": "ext://flask.logging.wsgi_errors_stream",
        "formatter": "default"
    }},
    "root": {
        "level": "INFO",
        "handlers": ["wsgi"]
    }
})

# Create my app
app = Flask(__name__)
app.debug = 'DEBUG'

@app.route('/<string:target>', methods = ["GET"])
def metrics(target):
    exporter = metricHandler(config_file)
    return exporter.metrics(target) 

""" middleware exception """
@app.errorhandler(Exception)
def exceptions(e):
    """ Logging after every Exception. """
    ts = strftime("[%Y-%b-%d %H:%M]")
    tb = traceback.format_exc()
    logger.error("%s %s %s %s %s 5xx INTERNAL SERVER ERROR\n%s",
                  ts,
                  request.remote_addr,
                  request.method,
                  request.scheme,
                  request.full_path,
                  tb)

    message = "Internal Server Error"
    response = Response(message, 503)
    return response

""" Logging after every request. """
@app.after_request
def after_request(response):
    """ Add basic HTTP API header before executing requests """
    response.headers["Access-Control-Allow-Origin"] = "*";
    response.headers["Access-Control-Allow-Headers"] = "Origin, X-Requested-With, Content-Type, Accept";
    response.headers["Access-Control-Allow-Methods"] = "PUT,POST,GET,DELETE,OPTIONS";

    """ log every request """
    current_date = datetime.now(timezone.utc).astimezone().strftime('[%Y-%b-%d %H:%M]')

    #if '50' not in response.status:
    logger.info('%s %s %s %s %s',
                request.remote_addr,
                request.method,
                request.scheme,
                request.full_path,
                response.status)

    return response

""" maxBytes to small number, in order to demonstrate the generation of multiple log files (backupCount). """
handler = RotatingFileHandler("redfish-exporter.log", maxBytes=1024 * 1024 * 100, backupCount=3)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

""" uncomment this line to log requests in file """
logger.addHandler(handler)

# Add prometheus wsgi middleware to route /metrics requests
app_dispatch = DispatcherMiddleware(app, {
    '/metrics': app
})
