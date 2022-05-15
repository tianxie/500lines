import http.server
import os


class ServerException(Exception):
    pass


class RequestHandler(http.server.BaseHTTPRequestHandler):
    '''Handle HTTP requests by returning a fixed 'page'.'''

    Error_Page = """\
            <html>
            <body>
            <h1>Error accessing {path}</h1>
            <p>{msg}</p>
            </body>
            </html>
            """

    # Handle a GET request.
    def do_GET(self):
        full_path = os.getcwd() + os.path.normpath(self.path)
        try:
            if not os.path.exists(full_path):
                raise ServerException('{0} not found'.format(self.path))
            elif os.path.isfile(full_path):
                self.handle_file(full_path)
            else:
                raise ServerException("Unknown object '{0}'".format(self.path))
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


# -------------------------------------------------------------------------------

if __name__ == '__main__':
    server_address = ('', 8080)
    server = http.server.HTTPServer(server_address, RequestHandler)
    server.serve_forever()
