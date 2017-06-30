from flask import render_template

from isocket.home import home_bp


@home_bp.route('/')
@home_bp.route('/index')
def index():
    return render_template('index.html', title='iSOCKET')


@home_bp.route('/contact')
def contact():
    return render_template('contact.html', title='contact')


@home_bp.route('/about')
def about():
    return render_template('about.html', title='about')


@home_bp.route('/reference')
def reference():
    return render_template('reference.html', title='reference')
