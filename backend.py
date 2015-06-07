from flask import Flask, jsonify, request, Response, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_debugtoolbar import DebugToolbarExtension
from functools import wraps
from json import dumps, loads
import bcrypt
import urllib
import requests

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root@127.0.0.1/globalhack'
app.config['SECRET_KEY'] = 'a test key'
app.debug = True
db = SQLAlchemy(app)
toolbar = DebugToolbarExtension(app)

class Publisher(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	email = db.Column(db.String(120), unique=True)
	password = db.Column(db.String(240))
	first_name = db.Column(db.String(50))
	last_name = db.Column(db.String(50))

	causes = db.relationship('Cause', backref='publisher', lazy='dynamic')

	def __init__(self, email, password, first_name, last_name):
		self.email = email
		self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
		self.first_name = first_name
		self.last_name = last_name

	def __repr__(self):
		return '<Publisher %r>' % (self.email)

	def checkPassword(self, userPassword):
		encoded = self.password.encode('utf-8')
		h = bcrypt.hashpw(userPassword, encoded)

		return h == self.password

class Cause(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	image = db.Column(db.Integer)

	email_required = db.Column(db.Boolean)
	questions_required = db.Column(db.Boolean)
	like_required = db.Column(db.Boolean)

	lockerdome_id = db.Column(db.Integer)

	feedback_goal_type = db.Column(db.String(15))
	goal_feedback_required = db.Column(db.Integer)
	goal_donation_amount = db.Column(db.Integer)
	goal_donation_charity = db.Column(db.String(255))
	single_donation_amount = db.Column(db.Numeric)

	url = db.Column(db.String(250))

	header_message = db.Column(db.String(255))

	publisher_id = db.Column(db.Integer, db.ForeignKey('publisher.id'))

	questions = db.relationship('Question', lazy='dynamic')

	def __init__(self, lockerdome_id, goal_type, email_required, questions_required, like_required, publisher_id):
		self.lockerdome_id = lockerdome_id
		self.feedback_goal_type = goal_type
		self.email_required = email_required
		self.questions_required = questions_required
		self.like_required = like_required
		self.publisher_id = publisher_id

	def __repr__(self):
		return '<Cause %r>' % (self.id)

class Question(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	cause_id = db.Column(db.Integer, db.ForeignKey('cause.id'))
	text = db.Column(db.Text(500))
	question_1 = db.Column(db.Text(250))
	question_2 = db.Column(db.Text(250))
	question_3 = db.Column(db.Text(250))
	question_4 = db.Column(db.Text(250))

	cause = db.relationship('Cause', backref='question')

	def __init__(self, cause_id, text, question_1, question_2, question_3, question_4):
		self.cause_id = cause_id
		self.text = text
		self.question_1 = question_1
		self.question_2 = question_2
		self.question_3 = question_3
		self.question_4 = question_4

	def __repr__(self):
		return '<Question %r>' % (self.text)

class UserResponse(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
	text = db.Column(db.Text(250))

	def __init__(self, user_id, question_id, text):
		self.user_id = user_id
		self.question_id = question_id
		self.text = text

	def __repr__(self):
		return '<UserResponse %r>' % (self.question_id)

class User(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	cause_id = db.Column(db.Integer, db.ForeignKey('cause.id'))
	name = db.Column(db.Text(50))
	email = db.Column(db.Text(150))

	def __init__(self, name, email, cause_id):
		self.name = name
		self.email = email
		self.cause_id = cause_id

	def __repr__(self):
		return '<User %r>' % (self.email)

def authenticate():
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def check_auth(email, password):
	u = Publisher.query.filter_by(email=email).first()

	if not u:
		return False

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
	first_name = request.form['first_name']
	last_name = request.form['last_name']
	email = request.form['email']
	password = request.form['password']

	u = Publisher(email, password, first_name, last_name)

	db.session.add(u)
	db.session.commit()

	return redirect(url_for('publisher_home'))

@app.route('/publisher/home')
@requires_auth
def publisher_home():
	u = Publisher.query.filter_by(email=request.authorization.username).first()
	i = Cause.query.all()

	return render_template('home.html', publisher=u, causes=i)

@app.route('/publisher/create', methods=['GET'])
@requires_auth
def publisher_create():
	return render_template('publish.html')

@app.route('/publisher/add', methods=['POST'])
@requires_auth
def publisher_add_act():
	data = dumps({
		'app_id': '7742364034531394',
		'app_secret': 'mG2QZ1f2o3oSsxpMznORrYAcG5pbhx7JTjC32eZom1domHhSolBPtBjmQ45y4Sxp4nHvaNUFvlEOw2l3F5SxqQ==',
		'app_data': {
			'cause_id': 1
		},
		'name': 'test content',
		'thumb_url': 'http://vignette1.wikia.nocookie.net/scratchpad/images/d/da/LARGEST_AWESOME_FACE_EVER!!!.png/revision/latest?cb=20121226043136',
		'text': 'test text'
	})

	query = urllib.quote(data)

	r = requests.get('http://api.globalhack4.test.lockerdome.com/app_create_content?' + query)

	j = r.json()

	cause = Cause(j['result']['id'], 'goal', False, True, False, 3)

	db.session.add(cause)
	db.session.commit()

	return str(cause.id)

@app.route('/display')
def display():
	data = loads(urllib.unquote(request.query_string))

	cause = Cause.query.filter_by(lockerdome_id=data['args']['id']).first()

	c = User.query.filter_by(cause_id=cause.id).count()

	return render_template('display.html', cause=cause, count=c)


@app.route('/donation', methods=['POST'])
def donate_act():
	u = None

	if request.form['responseType'] == 'anon':
		u = User(None, None, request.form['cause_id'])
		db.session.add(u)
		db.session.commit()

	elif request.form['responseType'] == 'name':
		u = User(request.form['name'], request.form['email'], request.form['cause_id'])
		db.session.add(u)
		db.session.commit()

	answers = {}
	for k, v in request.form.items():
		if 'question' in k:
			answers[int(k.replace('question', ''))] = v

	for question, answer in answers.items():
		resp = UserResponse(u.id, question, answer)
		db.session.add(resp)
	db.session.commit()

	return str(u.id)

@app.route('/email', methods=['POST'])
def email_act():
	u = User.query.filter_by(id=request.form['user_id']).first()

	u.email = request.form['anon_email']

	db.session.commit()

	return str(u.id)

@app.route('/publisher/create', methods=['POST'])
@requires_auth
def publisher_create_act():
	u = Publisher.query.filter_by(email=request.authorization.username).first()

	name_of_organization = request.form['supported_organization']
	rate_count = request.form['rate_count']
	rate_total = request.form['rate_total']
	question = request.form['question']
	answer1 = request.form['answer_1']
	answer2 = request.form['answer_2']
	answer3 = request.form['answer_3']
	answer4 = request.form['answer_4']
	required_fields = request.form.getlist('required_fields')

	print(required_fields)

	data = dumps({
		'app_id': '7742364034531394',
		'app_secret': 'mG2QZ1f2o3oSsxpMznORrYAcG5pbhx7JTjC32eZom1domHhSolBPtBjmQ45y4Sxp4nHvaNUFvlEOw2l3F5SxqQ==',
		'app_data': {
			'cause_id': 1
		},
		'name': 'Donation to %s' % (name_of_organization),
		'thumb_url': 'http://vignette1.wikia.nocookie.net/scratchpad/images/d/da/LARGEST_AWESOME_FACE_EVER!!!.png/revision/latest?cb=20121226043136',
		'text': 'Feedback donation drive to %s' % (name_of_organization)
	})

	query = urllib.quote(data)

	r = requests.get('http://api.globalhack4.test.lockerdome.com/app_create_content?' + query)

	j = r.json()

	cause = Cause(j['result']['id'], 'goal', 'email' in required_fields, 'feedback' in required_fields, False, u.id)

	cause.goal_feedback_required = rate_count
	cause.goal_donation_amount = rate_total
	cause.goal_donation_charity = name_of_organization

	db.session.add(cause)
	db.session.commit()

	q = Question(cause.id, question, answer1, answer2, answer3, answer4)

	db.session.add(q)
	db.session.commit()

	return redirect('http://globalhack4.test.lockerdome.com/7739974724091969/%s' % (cause.lockerdome_id))

if __name__ == '__main__':
	app.run(host='0.0.0.0')
