"""

Copyright (c) 2009 Sidney Fong

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

"""

### TODO:
# add modification time etc cache friendly headers

###### BEGIN CONFIGURATION ######

# These are the URLS that your app responds to.
# A corresponding app.yaml config is this:
# - url: /filestor/.*
#   script: filestor.py
config_urls = {
    'MainPage':             '/filestor/',
    'Upload':               '/filestor/upload',
    'Download':             '/filestor/download',
    'ViewFlv':             '/filestor/view_flv',
    'Delete':               '/filestor/delete',
    'UpdateAllowedUsers':   '/filestor/update_allowed_users',
 }

# Size of a chunk stored in an entity.
# By default Google App Engine allows 1 megabyte, but we'll use 512Kb to account for overhead etc.
CHUNKSIZE=512*1024

# The allowed user by default. For @gmail.com users the full email address is not required.
DEFAULT_ALLOWED_USER = 'someusername'
# To add more allowed users, add more AllowedUsers entities on the server. You
# may need to call the URL /filestor/update_allowed_users.

####### END CONFIGURATION #######

import cgi

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db

import mimetypes
import urllib

class UserFile(db.Model):
    owner = db.UserProperty( auto_current_user = True )
    content = db.BlobProperty()
    filename = db.StringProperty( required = True, default = 'NoName' )
    mtime = db.DateTimeProperty( required = True, auto_now = True )
    is_private = db.BooleanProperty( required = True, default = False )
    size = db.IntegerProperty( required = True, default = 0 )

class Chunk(db.Model):
    file = db.ReferenceProperty( UserFile, required = True )
    sequence = db.IntegerProperty( required = True )
    content = db.BlobProperty()

class AllowedUsers(db.Model):
    nickname = db.StringProperty()

allowed_users = []

def update_allowed_users():
    try:
        while True: allowed_users.pop()
    except:
        pass

    try:
        AllowedUsers.all().get().nickname
    except:
        x = AllowedUsers()
        x.nickname = DEFAULT_ALLOWED_USER
        x.put()

    for x in AllowedUsers.all():
        allowed_users.append(x.nickname)

update_allowed_users()

class MainPage(webapp.RequestHandler):
    def get(self):
        self.response.out.write("<html><head><title>FileStor</title></head><body>")
        user = users.get_current_user()
        if user and user.nickname() in allowed_users:
            self.response.out.write("""
 <div style="float: right; width: 300px; font-size: 12px;">
  <div>Precautions: #1 - if there are multiple files with the same name (even under different owners), only ONE file, chosen arbitrarily, will be displayed. (There is no checking because implementing it is super hard with GAE DataStore.)</div>
  <div>#2 - You cannot store/download files > 10MB. This is a limitation imposed by GAE.</div>
  <div>#3 - Bandwidth is not unlimited, unless you're willing to pay Google&reg; when quota is exceeded.</div>
  <div>#4 - It is alleged that you have 30 seconds to download/upload your files - or maybe 30 seconds is just CPU time.</div>
 </div>

 <div>Hello! You are currently user: '%s' ( <a href="%s">logout</a> )</div>
 <br>
 <br>
 <form action="upload" method="post" enctype="multipart/form-data">
  File: <input type="file" name="filedata"><br>
  Filename: <input type="text" name="filename"> (required, case sensitive)<br>
  Is private: <input type="checkbox" name="private" value="yes"><br>
  <input type="submit">
 </form>
 <hr>
            """ % ( user.nickname(), users.create_logout_url(self.request.uri) ) )
        elif user:
            self.response.out.write("<div align='right'>You are not allowed to upload files here. Contact site owner to add files, or <a href='%s'>login</a> as another user.</div>" % users.create_login_url(self.request.uri) )
        else:
            self.response.out.write("<div align='right'><a href='%s'>Login</a></div>" % users.create_login_url(self.request.uri))

        self.response.out.write("<br><h3>- Uploaded Files -</h3><table>\n")
        self.response.out.write("<tr><th>&nbsp;</th><th>Filename</th><th>Size (kb)</th><th>Owner</th><th>Modified</th><th>Actions</th></tr>")
        for f in UserFile.all().order("owner").order("filename"):
            if (not f.is_private)  or  ( user and user.nickname() == f.owner.nickname() ) :
                self.response.out.write( "<tr>" )

                if f.is_private: self.response.out.write("<td>*</td>")
                else: self.response.out.write("<td>&nbsp;</td>")

                self.response.out.write( "<td><a href=\"download?filename=%s\">%s</a></td>" % ( urllib.quote(f.filename.encode('utf-8'), safe = ''), cgi.escape(f.filename) ) )

                self.response.out.write( "<td>%d</td>" % ( f.size / 1024 ) )

                self.response.out.write( "<td>" )
                if user and f.owner.nickname() == user.nickname(): self.response.out.write("<b>")
                self.response.out.write( "%s" % f.owner.nickname() )
                if user and f.owner.nickname() == user.nickname(): self.response.out.write("</b>")
                self.response.out.write( "</td>" )

                self.response.out.write( "<td>%s</td>" % f.mtime.strftime("%Y%m%d %H:%M") )
                self.response.out.write( "<td>" )
                if ( user and user.nickname() == f.owner.nickname() ): self.response.out.write("<a href=\"delete?filename=%s\">delete</a>" % f.filename )
                if f.filename[-4:].upper() == '.FLV': self.response.out.write(" <a href=\"view_flv?filename=%s\">View in browser</a>" % f.filename )
                self.response.out.write( "</td>" )
                self.response.out.write( "</tr>\n" )
        self.response.out.write("</table>")
        self.response.out.write("</body></html>")

def yesno(q,a,b):
    if q: return a
    return b

class Upload(webapp.RequestHandler):
    def post(self):
        user = users.get_current_user()
        if not user:
            self.response.out.write("Need login")
            return

        if user.nickname() not in allowed_users:
            self.response.out.write("Unauthorized")
            return

        d = self.request.get('filedata')
        if not d:
            self.response.out.write("Need to choose a file")
            return

        f = UserFile()
        f.owner = user
        f.size = len(d)
        f.content = db.Blob(d[0:CHUNKSIZE])
        f.filename = self.request.get('filename')
        f.is_private = yesno( self.request.get('private') == 'yes', True, False )
        f.put()

        p = CHUNKSIZE
        z = 1
        while f.size > p:
            Chunk( file = f, sequence = z, content = d[p:p+CHUNKSIZE] ).put()
            z = z + 1
            p = p + CHUNKSIZE

        self.redirect('./')

class Delete(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if not user:
            self.response.out.write("Need login")
            return

        filename = self.request.get('filename')

        q = UserFile.all()
        q.filter('filename =', filename )
        q.filter('owner =', user ) # must be deleting user's own things

        # 1000 limit?
        for f in q.fetch(1000):
            # say goodbye to atomicity!!
            for chunk in f.chunk_set: chunk.delete()
            f.delete()
            self.response.out.write("<div>one file deleted</div>")
            self.response.out.write("<a href='./'>Continue</a>")

class Download(webapp.RequestHandler):
    def get(self):
        f = UserFile.all().filter('filename =', self.request.get('filename')).get()
        if not f:
            self.response.out.write("Not found")
            return
        if f.is_private:
            user = users.get_current_user()
            if not user:
                self.response.out.write("Need login")
                return
            if user.nickname() != f.owner.nickname():
                self.response.out.write("Unauthorized")
                return

        t, z = mimetypes.guess_type(f.filename)

        if not t: t = 'application/x-download'

        self.response.headers['Content-Type'] = t
        if z: self.response.headers['Content-Encoding'] = z
        self.response.headers['Content-Disposition'] = "inline; filename=%s" % urllib.quote( f.filename.encode('utf-8') )
        self.response.headers['Content-Length'] = f.size
        self.response.out.write(f.content)
        for chunk in f.chunk_set.order('sequence'):
            self.response.out.write(chunk.content)

class ViewFlv(webapp.RequestHandler):
    def get(self):
        filename = self.request.get('filename')
        s = """
<object type="application/x-shockwave-flash" data="/player_flv.swf" width="320" height="240">
    <param name="movie" value="/player_flv.swf" />
    <param name="allowFullScreen" value="false" />
    <param name="FlashVars" value="flv=/filestor/download%%3Ffilename%%3D%s&amp;title=View FLV&amp;startimage=/filestor/download%%3Ffilename%%3D%s.jpg&amp;autoplay=1" />
</object>
        """ % ( filename, filename )
        
        self.response.out.write("<html><body>")
        self.response.out.write( s )
        self.response.out.write("</body></html>")


class UpdateAllowedUsers(webapp.RequestHandler):
    def get(self):
        update_allowed_users()
        self.response.out.write("ok")


application = webapp.WSGIApplication( [
    (config_urls['MainPage'], MainPage),
    (config_urls['Upload'], Upload),
    (config_urls['Download'], Download),
    (config_urls['ViewFlv'], ViewFlv),
    (config_urls['Delete'], Delete),
    (config_urls['UpdateAllowedUsers'], UpdateAllowedUsers),
    ] , debug = True )

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

