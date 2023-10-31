# !/usr/bin/env python

# pylint: disable=invalid-name

"""
CherryPy-based webservice daemon with background threads
CherryPy-based webservice daemon with background threads
"""

from __future__ import print_function

import threading
import cherrypy
from cherrypy.process import plugins
import cherrypy_cors
from marshmallow import Schema, fields

from walrus import *


class NodeSchema(Schema):
    """
    Marshmallow schema for nodes object
    """
    name = fields.String(required=True)


def worker():
    """Background Timer that runs the hello() function every 5 seconds
    TODO: this needs to be fixed/optimized. I don't like creating the thread
    repeatedly.
    """

    # while True:
    #     t = threading.Timer(5.0, hello)
    #     t.start()
    #     t.join()


class MyBackgroundThread(plugins.SimplePlugin):
    """CherryPy plugin to create a background worker thread"""

    def __init__(self, bus):
        super(MyBackgroundThread, self).__init__(bus)

        self.t = None

    def start(self):
        """Plugin entrypoint"""

        self.t = threading.Thread(target=worker)
        self.t.daemon = True
        self.t.start()

    # Start at a higher priority that "Daemonize" (which we're not using
    # yet but may in the future)
    start.priority = 85


class NodesController(object):
    """Controller for  webservice APIs"""

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def login(self):
        method_type = "login"
        try:
            order_data = cherrypy.request.json
            print(order_data)
        except KeyError as e:
            return {"status": 401, "tracking_code": None, "method_type": method_type,
                    "error": "key %s is not passed" % str(e)}

        except:
            return {"status": 500, "tracking_code": None, "method_type": None, "error": "General Error"}

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def logout(self):
        method_type = "logout"
        try:
            order_data = cherrypy.request.json
            print(order_data)
        except KeyError as e:
            return {"status": 401, "tracking_code": None, "method_type": method_type,
                    "error": "key %s is not passed" % str(e)}

        except:
            return {"status": 500, "tracking_code": None, "method_type": None, "error": "General Error"}

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def index_insert(self):
        method_type = "insert"
        try:
            order_data = cherrypy.request.json
            print(order_data)
        except KeyError as e:
            return {"status": 401, "tracking_code": None, "method_type": method_type,
                    "error": "key %s is not passed" % str(e)}

        except:
            return {"status": 500, "tracking_code": None, "method_type": None, "error": "General Error"}

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def index_delete(self):
        method_type = "delete"
        try:
            order_data = cherrypy.request.json
            print(order_data)
        except KeyError as e:
            return {"status": 401, "tracking_code": None, "method_type": method_type,
                    "error": "key %s is not passed" % str(e)}

        except:
            return {"status": 500, "tracking_code": None, "method_type": None, "error": "General Error"}

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def index_update(self):
        method_type = "update"
        try:
            order_data = cherrypy.request.json
            print(order_data)
        except KeyError as e:
            return {"status": 401, "tracking_code": None, "method_type": method_type,
                    "error": "key %s is not passed" % str(e)}

        except:
            return {"status": 500, "tracking_code": None, "method_type": None, "error": "General Error"}

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def index_select(self):
        method_type = "select"
        try:
            order_data = cherrypy.request.json
            print(order_data)
        except KeyError as e:
            return {"status": 401, "tracking_code": None, "method_type": method_type,
                    "error": "key %s is not passed" % str(e)}

        except:
            return {"status": 500, "tracking_code": None, "method_type": None, "error": "General Error"}


####################################### bad request response
def jsonify_error(status, message): \
        # pylint: disable=unused-argument

    """JSONify all CherryPy error responses (created by raising the
    cherrypy.HTTPError exception)
    """

    cherrypy.response.headers['Content-Type'] = 'application/json'
    response_body = message

    cherrypy.response.status = status

    return response_body


def cors():
    if cherrypy.request.method == 'OPTIONS':
        # preflign request
        # see http://www.w3.org/TR/cors/#cross-origin-request-with-preflight-0
        cherrypy.response.headers['Access-Control-Allow-Methods'] = 'POST'
        cherrypy.response.headers['Access-Control-Allow-Headers'] = 'content-type'
        cherrypy.response.headers['Access-Control-Allow-Origin'] = '*'
        # tell CherryPy no avoid normal handler
        return True
    else:
        cherrypy.response.headers['Access-Control-Allow-Origin'] = '*'


if __name__ == '__main__':
    ports = list(sys.argv)
    # ports=[80,5000]

    cherrypy_cors.install()

    MyBackgroundThread(cherrypy.engine).subscribe()

    dispatcher = cherrypy.dispatch.RoutesDispatcher()

    dispatcher.connect(name='auth',
                       route='/StudentScientificSociety/insert_request',
                       action='index_insert',
                       controller=NodesController(),
                       conditions={'method': ['POST']})

    dispatcher.connect(name='auth',
                       route='/StudentScientificSociety/select_request',
                       action='index_select',
                       controller=NodesController(),
                       conditions={'method': ['POST']})

    dispatcher.connect(name='auth',
                       route='/StudentScientificSociety/delete_request',
                       action='index_delete',
                       controller=NodesController(),
                       conditions={'method': ['POST']})

    dispatcher.connect(name='auth',
                       route='/StudentScientificSociety/update_request',
                       action='index_update',
                       controller=NodesController(),
                       conditions={'method': ['POST']})

    dispatcher.connect(name='auth',
                       route='/StudentScientificSociety/login',
                       action='login',
                       controller=NodesController(),
                       conditions={'method': ['POST']})

    dispatcher.connect(name='auth',
                       route='/StudentScientificSociety/logout',
                       action='logout',
                       controller=NodesController(),
                       conditions={'method': ['POST']})

    config = {

        '/': {
            'request.dispatch': dispatcher,
            'error_page.default': jsonify_error,
            'cors.expose.on': True,
            # 'tools.auth_basic.on': True,
            # 'tools.auth_basic.realm': 'localhost',
            # 'tools.auth_basic.checkpassword': validate_password,
        },
    }

    cherrypy.tree.mount(root=None, config=config)

    cherrypy.config.update({
        'server.socket_host': '0.0.0.0',
        'server.socket_port': int(ports[1]),
        'server.socket_queue_size': 3000,
        'server.thread_pool': 30,
        'log.screen': False,
        'log.access_file': '',
        'engine.autoreload.on': False,
    })
    cherrypy.log.error_log.propagate = False
    cherrypy.log.access_log.propagate = False
    cherrypy.engine.start()
    cherrypy.engine.block()
