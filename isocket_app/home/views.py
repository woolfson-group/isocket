from flask import render_template
from isocket_app.home import home


@home.route('/')
@home.route('/index')
def index():
    return render_template('index.html', title='iSOCKET')


@home.route('/contact')
def contact():
    return render_template('contact.html', title='contact')


@home.route('/about')
def about():
    return render_template('about.html', title='about')


@home.route('/reference')
def reference():
    return render_template('reference.html', title='reference')
