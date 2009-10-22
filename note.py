import cgi

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db

import urllib
import hashlib
import random

whitespace = (' ','\t','\n')

def render_text( s ):
    s = s.rstrip()
    a = s.split('\n')
    ret = []
    for l in a:
        if len(l) > 0 and l[-1] == '\r': l = l[0:-1]
        la = []
        prev = ' '
        for c in l:
            if c in whitespace:
                if c == ' ' and prev in whitespace: la.append('&nbsp;')
                elif c == '\t':
                    la.append('&nbsp;')
                    while len(la) % 8 != 0: la.append('&nbsp;')
                else: la.append(c)
            else:
                la.append(cgi.escape(c))
            prev = c

        outline = "".join(la)
        ret.append( outline )

    return '<br>\n'.join( ret )

class Note(db.Model):
    title = db.StringProperty()
    content = db.TextProperty()
    mtime = db.DateTimeProperty( required = True, auto_now_add = True  )
    is_public = db.BooleanProperty( required = True, default = False )
    sha1 = db.StringProperty( required = True )

class MainPage(webapp.RequestHandler):
    def get(self):
        self.response.out.write("<html><head><title>Note</title><style>.deletefrm { float: right; height: 20px; width: 200px; } .itemcommon {border-style: solid; border-width: 0 0 1px 0; border-color: #AAA; padding: 1px 1em;} .frmcls { width: 400px; float: right; padding: 0.5em; background-color: #CCC; } .enternote { font-family: Verdana; font-size: 12px; font-weight: bold } .item0 { background-color: #EEE; } .item1{ background-color: #DFE } .stdwidth { width: 100%; } td { font-size: 12px; } body { font-size: 12px; } input { font-size: 12px; } textarea { font-size: 12px } pre { font-size: 12px; padding: 0px; margin: 0px } div { font-size: 12px }</style>")
        if (self.request.headers['User-Agent'].find('MIDP')>=0 or self.request.headers['User-Agent'].find('CLDC')>=0):
            self.response.out.write("<style>.hideifmobile { display: none; }</style>")
        self.response.out.write("</head>")

        # hack to make my mobile not display ads -- Si
        if not (self.request.headers['User-Agent'].find('MIDP')>=0 or self.request.headers['User-Agent'].find('CLDC')>=0):
            self.response.out.write("<body onload='document.getElementById(\"txtbox\").focus()'>")

        # the "name" field is reverse-anti-spam. Most spam bots would fill that in, while normal users wouldn't.
        frm = """
        <div align='center' class='enternote'>Enter Note:</div>
<form method="post" action="">
<input class="stdwidth" type="text" name="title"><br>
<input id="txtbox" type="text" style="display: none" name="name" value="">
<textarea class="stdwidth hideifmobile" rows="10" name="content"></textarea><br>
<input type="submit">
</form>
<a href="%s">Logout</a> | <a href="/qwe.py">qwe.py</a>
        """ % users.create_logout_url(self.request.uri)

        self.response.out.write("<div class='frmcls'>")
        self.response.out.write(frm)
        self.response.out.write("</div>")

        q = Note.all()
        if not users.is_current_user_admin():
            q = q.filter('is_public = ', True)
            self.response.out.write("<div>Anybody can post! But only moderated messages are public. (<a href='%s'>Admin Login</a>)</div><br>" % users.create_login_url(self.request.uri))

        z = 0
        for obj in q.order("-mtime").fetch(100):
            self.response.out.write("<div class='item%d itemcommon'>" % z)
            if users.is_current_user_admin():
                self.response.out.write("<div class='deletefrm'><form method='post' action=''><input type='hidden' name='sha1' value='%s'><input type='submit' name='delete' value='delete'>" % obj.sha1)
                if obj.is_public:
                    self.response.out.write("<input type='submit' name='private' value='make private' style='background-color: #AA0'>")
                else:
                    self.response.out.write("<input type='submit' name='public' value='make public'>")

                self.response.out.write("</form></div>" )

            self.response.out.write("<div>%s - <b>%s</b></div>" % ( obj.mtime.strftime("%Y-%m-%d %H:%M") ,  cgi.escape(obj.title.strip()) ) )
            if obj.content: self.response.out.write("<div style='font-family: courier new;  margin-left: 1em'>%s</div>" % render_text(obj.content)  )
            self.response.out.write("</div>\n")
            z = (z + 1) % 2



        self.response.out.write("</body></html>")

    def post(self):
        if users.is_current_user_admin() and self.request.get('sha1'):
            sha1 = self.request.get('sha1')
            obj = Note.all().filter('sha1 = ', sha1).get()
            if self.request.get('delete'):
                obj.delete()
            elif self.request.get('public'):
                obj.is_public = True
                obj.put()
            elif self.request.get('private'):
                obj.is_public = False
                obj.put()

            self.redirect('./')
            return

        if self.request.get('name'): return

        t = self.request.get('title')
        c = self.request.get('content')
        if len(c) > 1024*1024: return

        Note(
            title = t,
            content = db.Text( c ),
            sha1 = hashlib.sha1(str(random.random())+t.encode('utf-8')+c.encode('utf-8')).hexdigest()
        ).put()

        self.redirect('./')

application = webapp.WSGIApplication( [
    ( '/note/', MainPage )
    ] , debug = True )

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

