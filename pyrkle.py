import os
import time
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash

app = Flask(__name__)
app.config.from_object(__name__)

app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'pyrkle.db'),
    SECRET_KEY='devkey',
    USERNAME='admin',
    PASSWORD='password',
    ))

app.config.from_envvar('PYRKLE_SETTINGS', silent=True)

def connect_db():
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

@app.cli.command('initdb')
def initdb_command():
    init_db()


@app.route('/')
def show_exercise():
    db = get_db()
    cur = db.execute('select name, reps, whendo from exercise order by id desc')
    entries = cur.fetchall()
    return render_template('show_exercise.html', entries=entries)

@app.route('/exercise', methods=['POST'])
def add_exercise():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    db.execute('insert into exercise (name, reps, whendo) values (?, ?, ?);',
               [request.form['title'], request.form['text'],0])
    db.commit()
    flash('did it')
    return redirect(url_for('show_exercise'))

@app.route('/login',methods=['GET','POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        if request.form['password'] != app.config['PASSWORD']:
            error = 'invalid password'
        else:
            session['logged_in'] = True
            flash('you got logged in')
            return redirect(url_for('show_exercise'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('you got logged out')
    return redirect(url_for('show_entries'))

#app.run(debug=True)
app.run()
