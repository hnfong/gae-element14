# encoding: utf-8
import cgi

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import hashlib
import random
import math

import ccconv

hashfunctions = {
    'md5' : hashlib.md5,
    'sha1' : hashlib.sha1,
    'sha256' : hashlib.sha256,
    'sha512' : hashlib.sha512,
}

mathfunctions = { }
for x in dir(math):
    if x[0] != '_': mathfunctions.update( { x : getattr(math, x) } )

def rot13(s):
    d = dict ( zip( "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ", "nopqrstuvwxyzabcdefghijklmNOPQRSTUVWXYZABCDEFGHIJKLM" ) )
    def f(c):
        if c in d: return d[c]
        else: return c
    return "".join(map(f, s))

#ajax-able
class ConvPage(webapp.RequestHandler):
    def post(self):
        f = lambda x: x
        if self.request.get("direction") == "simp2trad":
            f = ccconv.simp2trad
        if self.request.get("direction") == "trad2simp":
            f = ccconv.trad2simp

        self.response.out.write( cgi.escape( f( self.request.get('text') ).encode('utf-8') ) )

class HashPage(webapp.RequestHandler):
    def post(self):
        f = hashfunctions[self.request.get('function').split(' ')[0]]
        self.response.out.write( f(self.request.get('plaintext')).hexdigest() )

class ExprPage(webapp.RequestHandler):
    def post(self):
        s = self.request.get('expr')
        try:
            self.response.out.write( cgi.escape( str( eval( s , mathfunctions ) ) ) )
        except Exception, e:
            self.response.out.write( cgi.escape ( "Error: %s" % str( e ) ) )

class EncrPage(webapp.RequestHandler):
    def post(self):
        s = self.request.get('plaintext')
        if self.request.get('function') == 'rot13':
            self.response.out.write( cgi.escape( rot13(s) ) )

class MainPage(webapp.RequestHandler):
    def get(self):
        self.response.out.write("""
<html>
 <head>
  <title>Element14 Utils</title>
  <style type="text/css">
   .ajax_result { font-family: courier new ; }
  </style>
  <script type="text/javascript" src="/ajax.js"></script>
  <script type="text/javascript" src="/utilpage.js"></script>
 </head>
 <body>
  <h3>Chinese Character Conversion</h3>
  <form action="./ccconv" method="post" enctype="multipart/form-data">
   <textarea name="text" rows="10" cols="60"></textarea><br>
   <select name="direction">
    <option value="trad2simp">繁=>简</option>
    <option value="simp2trad">简=>繁</option>
   </select>
   <input type="submit" value="轉換">
   <div class="ajax_result"></div>
   <textarea class="ajax_result" rows="10" cols="60"></textarea><br>
  </form>

  <h3>Hash</h3>
  <form action="./hash" method="post" enctype="multipart/form-data">
   Plain text: <input type="text" name="plaintext"><br />
   <div class="ajax_result"></div>
   <input type="submit" name="function" value="md5 digest">
   <input type="submit" name="function" value="sha1 digest">
   <input type="submit" name="function" value="sha256 digest">
   <input type="submit" name="function" value="sha512 digest">
  </form>

  <h3>Encryption</h3>
  <form action="./encr" method="post" enctype="multipart/form-data">
   Plain text: <input type="text" name="plaintext"><br />
   <div class="ajax_result"></div>
   <input type="submit" name="function" value="rot13">
  </form>

  <h3>Math Expression Evaluator</h3>
  <form action="./expr" method="post">
   Expression: <input type="text" name="expr"><br /><div class="ajax_result"></div>
   <input type="submit" name="function" value="Evaluate"><br />
    Available functions (from python's <code>math</code> module): <code>acos asin atan atan2 ceil cos cosh degrees e exp fabs floor fmod frexp hypot ldexp log log10 modf pi pow radians sin sinh sqrt tan tanh</code><br />
    For integer "power", as in a<sup>b</sup>, use <code>a**b</code>.
  </form>
 </body>
</html>
        """)
        self.response.out.write("")

application = webapp.WSGIApplication( [
    ( '/util/', MainPage ),
    ( '/util/ccconv', ConvPage ),
    ( '/util/hash', HashPage ),
    ( '/util/expr', ExprPage ),
    ( '/util/encr', EncrPage ),
    ] , debug = True )

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

