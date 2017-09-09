#!/usr/bin/python

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import cgi
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem

engine = create_engine('sqlite:///restaurantmenu.db')

Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


class webServerHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        try:

            return

            # if self.path.endswith("/restaurants"):

            #     self.getSuccess()

            #     restaurants = session.query(Restaurant).all()
            #     response = ""

            #     for restaurant in restaurants:

            #         response += "<h2>%s</h2>" % restaurant.name
            #         response += "<p><a href='/restaurant/%s/edit'>Edit</a> | <a href='/restaurant/delete'>Delete</a></p>" % restaurant.id

            #     self.createOutput(response)

            #     return

            # if self.path.endswith("/new"):

            #     self.getSuccess()

            #     response = "<form action='/restaurants'></form>"

            # if self.path.endswith("/edit"):

            #     self.getSuccess()

            #     response = "<form action='/restaurants'></form>"

        except IOError:
            self.send_error(404, 'File Not Found: %s' % self.path)

    def do_POST(self):
        try:
            self.send_response(301)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

        except:
            pass

    def getSuccess(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def createOutput(self, content):
        template = """
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <title>Document</title>
            </head>
            <body>
            %s
            </body>
            </html>
            """ % content

        self.wfile.write(template)


def main():
    try:
        port = 8080
        server = HTTPServer(('', port), webServerHandler)
        print "Web Server running on port %s" % port
        server.serve_forever()
    except KeyboardInterrupt:
        print " ^C entered, stopping web server...."
        server.socket.close()

if __name__ == '__main__':
    main()
