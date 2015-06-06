from flask import Flask, jsonify, request, Response, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
import bcrypt

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)

class User(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(80), unique=True)
	email = db.Column(db.String(120), unique=True)
	password = db.Column(db.String(240))

	def __init__(self, username, email, password):
		self.username = username
		self.email = email
		self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

	def __repr__(self):
		print '<User %r>' % (self.username)

	def checkPassword(self, userPassword):
		return bcrypt.hashpw(userPassword, self.password.encode('utf-8')) == self.password

app.secret_key = 'atestsecretkey'

def authenticate():
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def check_auth(username, password):
	u = User.query.filter_by(username=username).first()

	return u.checkPassword(password)

def requires_auth(f):
	@wraps(f)
	def decorated(*args, **kwargs):
		auth = request.authorization
		if not auth or not check_auth(auth.username, auth.password):
			return authenticate()
		return f(*args, **kwargs)
	return decorated

@app.route('/')
def home():
	return 'homepage'

@app.route('/feedback/<id>')
def get_feedback(id):
	return jsonify({'id': id})

@app.route('/publisher/register', methods=['GET'])
def publisher_register():
	return render_template('register.html')

@app.route('/publisher/register', methods=['POST'])
def publisher_register_act():
	username = request.form['username']
	password = request.form['password']
	email = request.form['email']

	u = User(username, email, password)

	db.session.add(u)
	db.session.commit()

	return redirect(url_for('publisher_home'))

@app.route('/publisher/home')
@requires_auth
def publisher_home():
	return request.authorization.username

if __name__ == '__main__':
	app.run(host='0.0.0.0', debug=True)
