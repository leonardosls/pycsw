# -*- coding: iso-8859-15 -*-
# =================================================================
#
# Authors: Adam Hinz <hinz.adam@gmail.com>
#
# Copyright (c) 2015 Adam Hinz
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# =================================================================

# WSGI wrapper for pycsw
#
# Apache mod_wsgi configuration
#
# ServerName host1
# WSGIDaemonProcess host1 home=/var/www/pycsw processes=2
# WSGIProcessGroup host1
#
# WSGIScriptAlias /pycsw-wsgi /var/www/pycsw/wsgi.py
#
# <Directory /var/www/pycsw>
#  Order deny,allow
#  Allow from all
# </Directory>
#
# or invoke this script from the command line:
#
# $ python ./pycsw/wsgi.py
#
# which will publish pycsw to:
#
# http://localhost:8000/
#

import logging
import os
import sys
import urlparse
from StringIO import StringIO

from werkzeug.wrappers import Request
from werkzeug.wrappers import Response

from pycsw import oldserver

LOGGER = logging.getLogger(__name__)
PYCSW_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@Request.application
def application(request):
    # create PycswHttpRequest from werkzeug request
    # instantiate server and load config
    # dispatch request for processing
    # return a response


def application(environ, start_response):
    request = PycswHttpRequest(**environ)
    config = request.META.get(
        "HTTP_PYCSW_CONFIG",
        environ.get("PYCSW_CONFIG", None)
    )
    # instantiate server and reconfigure logging
    pycsw_server = oldserver.PycswServer(rtconfig=config,
                                         reconfigure_logging=True)

    #response, http_code, response_headers  = instance.dispatch(request)
    #response_string = "\n".join((http_code, response_headers, response))
    #return [response_string]
    LOGGER.debug("config: {}".format(config))
    LOGGER.info("this is an info message")
    LOGGER.warning("request: {}".format(request))

    start_response("200 OK", [])
    return [str(environ)]


def old_application(env, start_response):
    """WSGI wrapper"""
    config = 'default.cfg'

    if 'PYCSW_CONFIG' in env:
        config = env['PYCSW_CONFIG']

    if env['QUERY_STRING'].lower().find('config') != -1:
        for kvp in env['QUERY_STRING'].split('&'):
            if kvp.lower().find('config') != -1:
                config = urlparse.unquote(kvp.split('=')[1])

    if not os.path.isabs(config):
        config = os.path.join(PYCSW_ROOT, config)

    if 'HTTP_HOST' in env and ':' in env['HTTP_HOST']:
        env['HTTP_HOST'] = env['HTTP_HOST'].split(':')[0]

    env['local.app_root'] = PYCSW_ROOT

    csw = oldserver.Csw(config, env)

    gzip = False
    if ('HTTP_ACCEPT_ENCODING' in env and
            env['HTTP_ACCEPT_ENCODING'].find('gzip') != -1):
        # set for gzip compressed response
        gzip = True

    # set compression level
    if csw.config.has_option('server', 'gzip_compresslevel'):
        gzip_compresslevel = \
            int(csw.config.get('server', 'gzip_compresslevel'))
    else:
        gzip_compresslevel = 0

    status, contents = csw.dispatch_wsgi()

    headers = {}

    if gzip and gzip_compresslevel > 0:
        import gzip

        buf = StringIO()
        gzipfile = gzip.GzipFile(mode='wb', fileobj=buf,
                                 compresslevel=gzip_compresslevel)
        gzipfile.write(contents)
        gzipfile.close()

        contents = buf.getvalue()

        headers['Content-Encoding'] = 'gzip'

    headers['Content-Length'] = str(len(contents))
    headers['Content-Type'] = csw.contenttype

    start_response(status, headers.items())

    return [contents]

if __name__ == '__main__':  # run inline using WSGI reference implementation
    logging.basicConfig(level=logging.DEBUG)
    from wsgiref.simple_server import make_server
    port = 8000
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    httpd = make_server('', port, application)
    print('Serving on port %d...' % port)
    httpd.serve_forever()
