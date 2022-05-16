import http.server
import os


class ServerException(Exception):
    pass


class case_no_file:
    def test(self, handler):
        return not os.path.exists(handler.full_path)

    def act(self, handler):
        raise ServerException("'{0}' not found".format(handler.path))


class case_existing_file:
    '''File exists.'''

    def test(self, handler):
        return os.path.isfile(handler.full_path)

    def act(self, handler):
        handler.handle_file(handler.full_path)


class case_always_fail:
    '''Base case if nothing else worked.'''

    def test(self, handler):
        return True

    def act(self, handler):
        raise ServerException("Unknown object '{0}'".format(handler.path))


class case_directory_index_file:

    def index_path(self, handler):
        return os.path.join(handler.full_path, 'index.html')

    def test(self, handler):
        return os.path.isdir(handler.full_path) and \
               os.path.isfile(self.index_path(handler))

    def act(self, handler):
        handler.handle_file(self.index_path(handler))


class case_directory_no_index_file(object):
    '''Serve listing for a directory without an index.html page.'''

    def index_path(self, handler):
        return os.path.join(handler.full_path, 'index.html')

    def test(self, handler):
        return os.path.isdir(handler.full_path) and \
               not os.path.isfile(self.index_path(handler))

    def act(self, handler):
        handler.list_dir(handler.full_path)


class RequestHandler(http.server.BaseHTTPRequestHandler):
    Cases = [case_no_file(),
             case_existing_file(),
             case_directory_index_file(),
             case_directory_no_index_file(),
             case_always_fail()]

    Error_Page = """\
            <html>
            <body>
            <h1>Error accessing {path}</h1>
            <p>{msg}</p>
            </body>
            </html>
            """

    Listing_Page = '''\
            <html>
            <body>
            <ul>
            {0}
            </ul>
            </body>
            </html>
            '''

    # Handle a GET request.
    def do_GET(self):
        self.full_path = os.getcwd() + os.path.normpath(self.path)

        try:
            for case in self.Cases:
                if case.test(self):
                    case.act(self)
                    break
        except ServerException as e:
            self.handle_error(e)

    def send_content(self, content, status=200):
        self.send_response(status)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def handle_file(self, full_path):
        try:
            with open(full_path, 'rb') as f:
                content = f.read()
                self.send_content(content)
        except IOError as e:
            msg = "'{0}' cannot be read: {1}".format(self.path, e)
            self.handle_error(msg)

    def handle_error(self, e):
        content = self.Error_Page.format(path=self.path, msg=e)
        self.send_content(content.encode('utf-8'), 404)

    def list_dir(self, full_path):
        try:
            entries = os.listdir(full_path)
            bullets = ['<li>{0}</li>'.format(e) for e in entries if not e.startswith('.')]
            page = self.Listing_Page.format('\n'.join(bullets))
            self.send_content(page.encode('utf-8'))
        except OSError as e:
            msg = "'{0}' cannot be listed: {1}".format(self.path, e)
            self.handle_error(msg)


# -------------------------------------------------------------------------------

if __name__ == '__main__':
    server_address = ('', 8080)
    server = http.server.HTTPServer(server_address, RequestHandler)
    server.serve_forever()
