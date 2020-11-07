from app import app, db
from app.email import send_email
from app.forms import LoginForm, RegistrationForm
from app.models import User, Login
from datetime import datetime, timedelta
from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user
from werkzeug.urls import url_parse


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        user_login = Login(user_id=user.id)
        db.session.add(user_login)
        db.session.commit()
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    user_logout = Login.query.filter_by(user_id=current_user.get_id()).all()[-1]
    user_logout.logout_time = datetime.utcnow()
    db.session.commit()
    logout_user()
    if request.args.get('sick'):
        return redirect(url_for('sick'))
    return redirect(url_for('index'))


@app.route('/report', methods=['GET', 'POST'])
def report():
    update_user_status = User.query.filter_by(id=current_user.get_id()).first()
    update_user_status.is_sick = True
    db.session.commit()
    sick_in_office = Login.query.filter(Login.logout_time >= (datetime.utcnow() - timedelta(days=7)),
                                        Login.user_id == current_user.get_id())
    sick_times = [(day.login_time, day.logout_time) for day in sick_in_office]
    potential_exposed_times = Login.query.filter(Login.login_time >= (datetime.utcnow() - timedelta(days=7)),
                                       Login.user_id != current_user.get_id())
    exposed_users = []
    for exposed_user in potential_exposed_times:
        for sick_time in sick_times:
            if exposed_user.user_id not in exposed_users and sick_time[0] <= exposed_user.login_time <= sick_time[1]:
                exposed_users.append(exposed_user.user_id)
    exposed_users_data = User.query.filter(User.id.in_(exposed_users))
    emails = [user.email for user in exposed_users_data]
    if emails:
        send_email('You\'ve been in touch with an infected co-worker!!',
                   'hr@montara.io',
                   emails,
                   'One of you\'re co-workers has reported being sick, for the sake of everyone, we urge you to go test yourself',
                   '<p>One of you\'re co-workers has reported being sick, for the sake of everyone, we urge you to go test yourself</p>'
                   )
    return logout()


@app.route('/sick')
def sick():
    return render_template('sick.html')
