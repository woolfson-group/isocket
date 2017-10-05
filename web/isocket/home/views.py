from flask import render_template

from isocket.home import home_bp


@home_bp.route('/')
@home_bp.route('/index')
def index():
    return render_template('index.html', title='iSOCKET')

@home_bp.route('/isocket')
def isocket():
    return render_template('isocket.html', title='iSOCKET')

@home_bp.route('/contact')
def contact():
    return render_template('contact.html', title='Contact')


@home_bp.route('/about')
def about():
    return render_template('about.html', title='About')


@home_bp.route('/reference')
def reference():
    return render_template('reference.html', title='Reference')
