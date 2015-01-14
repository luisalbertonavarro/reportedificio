import jinja2
import os
import webapp2
from google.appengine.api import users
from google.appengine.ext import blobstore
from google.appengine.ext import db
from google.appengine.ext.webapp import blobstore_handlers

template_env = jinja2.Environment( loader=jinja2.FileSystemLoader(os.getcwd()))

class UserUpload(db.Model):
  user = db.UserProperty()
  emission_date = db.StringProperty()
  name = db.StringProperty()
  description = db.StringProperty()
  amount = db.StringProperty()
  payment_date = db.StringProperty()
  blob = blobstore.BlobReferenceProperty()

class MainPage(webapp2.RequestHandler):
  def get(self):
    user = users.get_current_user()
    login_url = users.create_login_url(self.request.path)
    logout_url = users.create_logout_url(self.request.path)

    uploads = None
    q = db.Query()
    q.ancestor(db.Key.from_path('UserUpload', 'UserUploadGroup'))
    uploads = q.fetch(100)

    upload_url = blobstore.create_upload_url('/upload')
    template = template_env.get_template('templates/home.htm')
    context = {
      'user': user,
      'login_url': login_url,
      'logout_url': logout_url,
      'uploads': uploads,
      'upload_url': upload_url,
    }

    self.response.write(template.render(context))

class ViewHandler(blobstore_handlers.BlobstoreDownloadHandler):
  def get(self):
    user = users.get_current_user()
    upload_key_str = self.request.params.get('key')
    upload = None
    if upload_key_str:
        upload = db.get(upload_key_str)

    if (not user or not upload or upload.user != user):
        self.error(404)
        return

    self.send_blob(upload.blob)

app = webapp2.WSGIApplication([
  ('/', MainPage),
  ('/view', ViewHandler),
], debug=True)
