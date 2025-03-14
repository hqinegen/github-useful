#login handle
from flask import Flask, redirect, url_for, render_template, jsonify, request, make_response, session
from flask_mysqldb import MySQL
import yaml

from functools import wraps
from ldap3 import Server, Connection, SIMPLE, SYNC, ALL
import logging
import os
import pdb

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
log = logging.getLogger('app.authenticator')

def authenticate(domain, user, password):
    authenticated = False
    try:
        server = Server(domain, get_info=ALL)
        connection = Connection(server, authentication=SIMPLE, user=user, password=password,auto_bind=True)
        connection.open()
        connection.bind()
        log.debug("LDAP Result => %s", connection.result)
        authenticated = connection.result['result'] == 0
    except Exception:
        log.exception("Failed to authenticate user", exc_info=True)
    return authenticated


@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        form = request.form
        name = form['name']
        password = form['password']
        result = authenticate('hdspoole.local', name, password)
        session['username'] = name
        if result:
            return '<h1>You login fine</h1>'
        else:
            return render_template('loginfailed.html', uname=name)

    else:
        return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True, host='172.22.33.5', port=2000)
