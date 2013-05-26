#!/usr/bin/env python3

from lesscss import lessc
import tornado.ioloop
import tornado.web
import operator
import os

import config
import db

class BaseHandler(tornado.web.RequestHandler):
	def render(self, *args, **kwargs):
		kwargs['host'] = config.web.host
		return super(BaseHandler, self).render(*args, **kwargs)

	def render_string(self, *args, **kwargs):
		s = super(BaseHandler, self).render_string(*args, **kwargs)
		return s.replace(b'\n', b'') # this is like Django's {% spaceless %}

	def get_current_user(self):
		user_id = self.get_secure_cookie('user_id')
		if user_id is not None:
			return int(user_id)

class MainHandler(BaseHandler):
	def get(self):
		self.render('home.html')

class LoginHandler(BaseHandler):
	def post(self):
		username = self.get_argument('username')
		password = self.get_argument('password')
		user_id = db.check_login(username, password)
		success = False
		if user_id is not None:
			self.set_secure_cookie('user_id', str(user_id), expires_days=90)
			success = True
		self.render('login.html', success=success)

class MapHandler(BaseHandler):
	@tornado.web.authenticated
	def get(self):
		self.render('map.html')

class MapAPIHandler(BaseHandler):
	@tornado.web.authenticated
	def get(self):
		r = db.query_one('SELECT json from maps')
		map_data = r.json
		self.set_header('Content-Type', 'application/json')
		self.write(map_data)

class CSSHandler(tornado.web.RequestHandler):
	def get(self, css_path):
		css_path = os.path.join(os.path.dirname(__file__), 'static', css_path) + '.less'
		with open(css_path, 'r') as f:
			self.set_header('Content-Type', 'text/css')
			css = lessc.compile(f.read())
			self.write(css)

if __name__ == '__main__':
	tornado.web.Application(
		handlers=[
			(r'/', MainHandler),
			(r'/login', LoginHandler),
			(r'/map', MapHandler),
			(r'/map.json', MapAPIHandler),
			(r'/(css/.+)\.css', CSSHandler),
		],
		template_path=os.path.join(os.path.dirname(__file__), 'templates'),
		static_path=os.path.join(os.path.dirname(__file__), 'static'),
		cookie_secret=config.web.cookie_secret,
		xsrf_cookies=True,
		login_url='/login',
		debug=True,
	).listen(config.web.port)
	print('Listening on :%d' % config.web.port)
	tornado.ioloop.IOLoop.instance().start()