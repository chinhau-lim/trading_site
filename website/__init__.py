'''
	Package Initializer.
'''

import flask

app = flask.Flask(__name__)
app.config.from_object('website.config')
app.config.from_envvar('WEBSITE_SETTINGS', silent=True)

#import website.api   
import website.views
import website.model