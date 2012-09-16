import os
import webapp2
import urllib2
from xml.dom import minidom

import jinja2 

from google.appengine.ext import db 

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

class Handler(webapp2.RequestHandler):
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)

	def render_str(self, template, **params):
		t = jinja_env.get_template(template)
		return t.render(params)

	def render(self, template, **kw):
		self.write(self.render_str(template, **kw))

class Art(db.Model):
	title = db.StringProperty(required = True)
	art = db.TextProperty(required = True)
	created = db.DateTimeProperty(auto_now_add = True)
	coords = db.GeoPtProperty()

IP_URL = "http://api.hostip.info/?ip="

def get_coords(ip):
	s = IP_URL + ip
	content = None
	try:
		content = urllib2.urlopen(s).read()
	except:
		return
	if content:
		#parse xml and find url co-ordinates
		x = minidom.parseString(content)
		k = x.getElementsByTagName("gml:coordinates")
		if k:
			d = k[0].childNodes[0].nodeValue
			lon,lat = d.split(',')
			return db.GeoPt(float(lat), float(lon))

GMAPS_URL = "http://maps.googleapis.com/maps/api/staticmap?size=500x263&sensor=false&"

def gmaps_img(points):
    markers = "&".join("markers=%s,%s" %(p.lat, p.lon) for p in points)
    return GMAPS_URL + markers

class MainPage(Handler):
	def render_front(self, title="", art="", error=""):
		arts = db.GqlQuery("SELECT * FROM Art ORDER BY created DESC LIMIT 10")

		arts = list(arts) # doing this to avoid querying in iterable
			#find which arts have coordinates
		points = []
		for a in arts:
			if a.coords:
				points.append(a.coords)
		img_url = None
		if points:
			img_url = gmaps_img(points)
		self.render("front.html", title=title, art=art, error=error, arts=arts, img_url=img_url)

	def get(self):
			#self.write(self.request.remote_addr)
			#self.write(repr(get_coords(self.request.remote_addr)))
		self.render_front()

	def post(self):
		title = self.request.get("title")
		art = self.request.get("art")
		if title and art:
			a = Art(title=title, art=art)
			#get coordinates
			coords = get_coords(self.request.remote_addr)
			if coords:
				a.coords = coords
			a.put()
			self.redirect("/")
		else:
			error = "Please enter both the variables."
			self.render_front(error=error, title=title, art=art)

app = webapp2.WSGIApplication([('/', MainPage)], debug=True)