import cgi

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.ext import db

import sys

def mirror( s ):
    return s
def yes_if_on( s ):
    if s == 'on': return True
    return False

class CrudItem(db.Model):
    owner = db.UserProperty ( auto_current_user = True )
    title = db.StringProperty ()
    mtime = db.DateTimeProperty( required = True, auto_now = True )
    ctime = db.DateTimeProperty( required = True, auto_now_add = True )
    is_public = db.BooleanProperty( required = True, default = False )

    def real_update_kwargs_from_post_data( self, post_data, transform ):
        d = {}
        for k in transform:
            if k in post_data:
                d.update( { k: transform[k]( post_data[k] ) } )

        return d

    def update_kwargs_from_post_data( self, post_data, transform = {} ):
        transform.update ({
            'title': mirror,
            'is_public': yes_if_on,
        })
        return self.real_update_kwargs_from_post_data( post_data, transform )

    def update_from_post_data ( self, post_data ):
        d = self.update_kwargs_from_post_data( post_data )
        for k in d:
            self.__setattr__(k, d[k])

    def __init__(self, post_data = None, **kwargs):
        if post_data:
            kwargs.update( self.update_kwargs_from_post_data( post_data ) )
        db.Model.__init__(self, **kwargs)

SubjectClass = CrudItem

def have_perm( user, level, object ):
    if level == 'admin':
        if user: return users.is_current_user_admin()
        return False

    if level == 'owner':
        if not user: return False
        if not object: return False
        if object.owner == user: return True
        return False

    if level == 'all':
        return True

    raise "No such level"


def have_access( user, perm_set, object ):
    for k in perm_set:
        if have_perm(user, k, object) and perm_set[k] == True:
            return True

    return False


# TODO: catch the exceptions better
def assert_permissions ( user, perm_set, object ):
    if not have_access( user, perm_set, object ): raise Exception("Permission Denied")

PERM_INDEX = {
    'admin': True,
    'all' : True,
}
PERM_CREATE = {
    'admin': True,
    'all': False,
}
PERM_READ = {
    'admin': True,
    'owner': True,
    'all': True,
}
PERM_UPDATE = {
    'admin': True,
    'owner': True,
    'all': False,
}
PERM_DELETE = {
    'admin': True,
    'owner': True,
    'all': False,
}

def request_list_to_map( r ):
    post_data = dict()
    for k in r.arguments():
        if (k[0:5] == 'crud_'): post_data.update( { k[5:]: r.get(k) } )

    return post_data

def default_dict( r, user, item = None ):
    return {
        'clz' : SubjectClass,
        'request' : r,
        'user' : user,
        'login_url' : users.create_login_url(r.uri),
        'logout_url' : users.create_logout_url(r.uri),
        'item' : item,
    }

class CrudIndex(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        assert_permissions( user, PERM_INDEX, None )
        self.response.out.write( template.render( "index.html", default_dict( self.request, user ) ) )

class CrudCreate(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        assert_permissions( user, PERM_CREATE, None )
        self.response.out.write( template.render( "edit.html", default_dict( self.request, user) ) )

    def post(self):
        user = users.get_current_user()
        assert_permissions( user, PERM_CREATE, None )
        post_data = request_list_to_map( self.request )
        SubjectClass( post_data ).put()
        self.redirect('./')

class CrudRead(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        item = SubjectClass.all().filter("__key__ = ", db.Key(self.request.get('crud_key'))).get()
        assert_permissions( user, PERM_READ, item )
        self.response.out.write( template.render( "read.html", default_dict( self.request, user, item ) ) )

class CrudUpdate(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        item = SubjectClass.all().filter("__key__ = ", db.Key(self.request.get('crud_key'))).get()
        assert_permissions( user, PERM_UPDATE, item )
        self.response.out.write( template.render( "edit.html", default_dict( self.request, user, item ) ) )

    def post(self):
        user = users.get_current_user()
        item = SubjectClass.all().filter("__key__ = ", db.Key(self.request.get('crud_key'))).get()
        assert_permissions( user, PERM_UPDATE, item )
        post_data = request_list_to_map( self.request )
        item.update_from_post_data( post_data )
        item.put()
        self.redirect('./')

class CrudDelete(webapp.RequestHandler):
    def post(self):
        user = users.get_current_user()
        item = SubjectClass.all().filter("__key__ = ", db.Key(self.request.get('crud_key'))).get()
        assert_permissions( user, PERM_DELETE, item )
        item.delete()
        self.redirect('./')

application = webapp.WSGIApplication( [
    ( '/crud/', CrudIndex ),
    ( '/crud/create', CrudCreate ),
    ( '/crud/read', CrudRead ),
    ( '/crud/update', CrudUpdate ),
    ( '/crud/delete', CrudDelete ),
    ] , debug = True )

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

