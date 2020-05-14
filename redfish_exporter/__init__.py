import json
import logging
import traceback

from flask import Flask, request, Response
from time import strftime
from werkzeug.middleware.dispatcher import DispatcherMiddleware

from .simple_exporter import metricHandler

config_file = "./config.yaml"

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

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Add prometheus wsgi middleware to route /metrics requests
app_dispatch = DispatcherMiddleware(app, {
    '/metrics': app
})
