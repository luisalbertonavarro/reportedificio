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

class AdminPage(webapp2.RequestHandler):
  def get(self):
    user = users.get_current_user()
    login_url = users.create_login_url(self.request.path)
    logout_url = users.create_logout_url(self.request.path)

    uploads = None
    q = db.Query()
    q.ancestor(db.Key.from_path('UserUpload', 'UserUploadGroup'))
    uploads = q.fetch(100)

    upload_url = blobstore.create_upload_url('/admin/upload')
    template = template_env.get_template('templates/admin.htm')
    context = {
        'user': user,
        'login_url': login_url,
        'logout_url': logout_url,
        'uploads': uploads,
        'upload_url': upload_url,
    }

    self.response.write(template.render(context))

class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
  def post(self):
    user = users.get_current_user()
    emission_date = self.request.params['emission_date']
    name = self.request.params['name']
    description = self.request.params['description']
    amount = self.request.params['amount']
    payment_date = self.request.params['payment_date']

    upload = None
    if self.get_uploads('upload'):
      for blob_info in self.get_uploads('upload'):
        upload = UserUpload(parent=db.Key.from_path('UserUpload', 'UserUploadGroup'),
                            user=user,
                            emission_date=emission_date,
                            name=name,
                            description=description,
                            amount=amount,
                            payment_date=payment_date,
                            blob=blob_info.key())
    else:
       upload = UserUpload(parent=db.Key.from_path('UserUpload', 'UserUploadGroup'),
                           user=user,
                           emission_date=emission_date,
                           name=name,
                           description=description,
                           amount=amount,
                           payment_date=payment_date)

    upload.put()
    self.redirect('/admin/main')

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

class DeleteHandler(webapp2.RequestHandler):
  def post(self):
    user = users.get_current_user()
    entities_to_delete = []
    for delete_key in self.request.params.getall('delete'):
      upload = db.get(delete_key)
      entities_to_delete.append(upload.key())
      entities_to_delete.append(db.Key.from_path('UserUpload',
                                'UserUploadGroup'))
      db.delete(entities_to_delete)
    self.redirect('/admin/main')

app = webapp2.WSGIApplication([
  ('/admin/main', AdminPage),
  ('/admin/upload', UploadHandler),
  ('/admin/view', ViewHandler),
  ('/admin/delete', DeleteHandler)
], debug=True)
