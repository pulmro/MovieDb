from flask import Flask

app = Flask(__name__)
app.debug = True


from moviecase.www import views
from moviecase.www import fAPI
