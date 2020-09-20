import flask
from flask import Flask, render_template, request, session, jsonify, send_file, redirect
from flask_socketio import SocketIO, send, emit, join_room, leave_room, rooms, disconnect
import flask_login
from flask_login import current_user, login_required

import bcrypt, functools
from functools import wraps
import uuid
import json
import os
from shutil import copyfile
import xml.etree.ElementTree as et
from xml.dom import minidom

import lxml.etree

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

def getsetting(setting):
    settingfeed = "./settings.xml"
    tree = lxml.etree.parse(settingfeed)
    values = tree.xpath(".//title[text()='"+ setting + "']/..")

    return {
        'value' : str(values[0][3].text)
    }

def getuser(uname):
    userfeed = "./users.xml"
    tree = lxml.etree.parse(userfeed)

    if uname:
        users = tree.xpath(".//title[text()='"+ uname +"']/..")

        if users:
            username = str(users[0][0].text)
            usermail = str(users[0][1].text)
            userpass = str(users[0][2].text)
            userkey = str(users[0][3].text)
            thing = {
                username: {
                'usermail' : usermail,
                'userpass' : userpass,
                'userkey' : userkey}
            }
            return thing
        else:
            return False
    else:
        return  False

class User(flask_login.UserMixin):
    pass

login_manager = flask_login.LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.unauthorized_handler
def unauthorized_handler():
    return 'Unauthorized'

@login_manager.user_loader
def user_loader(email):
    users = getuser(email)
    if not users:
        return
    if email not in users:
        return
    user = User()
    user.id = email
    return user

@login_manager.request_loader
def request_loader(request):
    email = request.form.get('email')
    users = getuser(email)
    if not users:
        return
    if email not in users:
        return
    user = User()
    user.id = email
    user.is_authenticated =  bcrypt.checkpw(request.form['password'].encode('utf-8'),users[email]['userpass'].encode('utf-8'))
    return user

def authenticated_only(f):
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            disconnect()
        else:
            return f(*args, **kwargs)
    return wrapped

@socketio.on('join')
@authenticated_only
def on_join(data):
    if current_user.is_authenticated:
        username = flask_login.current_user.id
        room = data['room']
        join_room(room)
        send(username + ' has entered the room ' + room, room=room)
        emit("setRoom", room)
        emit("setUser", username)
    else:
        return False
@socketio.on('leave')
@authenticated_only
def on_leave(data):
    username = flask_login.current_user.id
    room = data['room']
    leave_room(room)
    send(username + ' has left the room '+ room, room=room)
    emit("remRoom", room)
    
@socketio.on('message')
@authenticated_only
def handle_message(message):
    if not current_user.is_authenticated:
        send("Not logged in")
        return False
    mainroom = rooms()[1]
    username = flask_login.current_user.id
    reqfeed = "./feeds/" + mainroom + ".xml"
    msgid = str(uuid.uuid1().hex)
    if os.path.isfile(reqfeed):
        tree = et.parse(reqfeed)
        root = tree.getroot()

        et.SubElement(root[0], 'item')
        
        et.SubElement(root[0][-1], 'title')
        root[0][-1][-1].text = msgid
        et.SubElement(root[0][-1], 'username')
        root[0][-1][-1].text = username
        et.SubElement(root[0][-1], 'description')
        root[0][-1][-1].text = message
        et.SubElement(root[0][-1], "msgid")
        root[0][-1][-1].text = msgid
        tree.write(reqfeed)

    else:
        copyfile("./template.xml", reqfeed)
        tree = et.parse(reqfeed)
        root = tree.getroot()

        et.SubElement(root[0], 'item')
       
        et.SubElement(root[0][-1], 'title')
        root[0][-1][-1].text = msgid
        et.SubElement(root[0][-1], 'username')
        root[0][-1][-1].text = username
        et.SubElement(root[0][-1], 'description')
        root[0][-1][-1].text = message
        
        et.SubElement(root[0][-1], "msgid")
        root[0][-1][-1].text = msgid
        tree.write(reqfeed)

    emit("getnewmsg",msgid, room=mainroom)

@app.route('/')
def index():
   return render_template('index.html')

@app.route('/feed/<feed>')
def getfeed(feed):
    reqfeed = "feeds/" + feed + ".xml"
    if os.path.isfile(reqfeed):
        return send_file(reqfeed)
    else:
        return "fail"

@app.route('/getmsg/<feed>/<id>')
def getmsg(feed, id):
    reqfeed = "feeds/" + feed + ".xml"
    if os.path.isfile(reqfeed):
        tree = lxml.etree.parse(reqfeed)
        parent = tree.xpath(".//msgid[text()='"+ id +"']/..")

        msguser = str(parent[0][1].text)
        msgcont = str(parent[0][2].text)

        return jsonify(
                msguser = msguser,
                msgcont = msgcont
        )
    else:
        return "fail"

@app.route('/login', methods=['POST'])
def login():
    email = flask.request.form['uname']
    users = getuser(email)
    if users:
        if bcrypt.checkpw(request.form['password'].encode('utf-8'),users[email]['userpass'].encode('utf-8')):
            user = User()
            user.id = email
            flask_login.login_user(user)
            return 'Logged in'
        else:
            return 'Bad login'
    else:
        return 'Unknown'

@app.route('/logout')
@authenticated_only
def logout():
    flask_login.logout_user()
    return 'Logged out'

@app.route('/signup', methods=['GET','POST'])
def signup():
    if not bool(getsetting("signup")['value'] == "True"):
        return "Signup Disabled"

    if flask.request.method == 'GET':
        return render_template('signup.html')
    passwd = flask.request.form.get('password')
    email = flask.request.form.get('uname')
    users = getuser(email)
    if users:
        return "USER ACCOUNT TAKEN"
    if not passwd:
        return "NO PASSWORD SUPPLIED"

    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(passwd.encode('utf-8'), salt)

    reqfeed = getsetting("userfeed")['value']
    tree = et.parse(reqfeed)
    root = tree.getroot()

    et.SubElement(root[0], 'item')
    
    et.SubElement(root[0][-1], 'title')
    root[0][-1][-1].text = email
    et.SubElement(root[0][-1], 'author')
    root[0][-1][-1].text = ""
    et.SubElement(root[0][-1], 'comments')
    root[0][-1][-1].text = hashed.decode('utf-8')
    et.SubElement(root[0][-1], "description")
    root[0][-1][-1].text = ""
    tree.write(reqfeed)
    return redirect("/")

@app.route('/protected')
@flask_login.login_required
def protected():
    return 'Logged in as: ' + flask_login.current_user.id

@app.route('/getuser/<uname>')
def getusers(uname):
    return getuser(uname)

if __name__ == '__main__':
    socketio.run(app, debug=bool(getsetting("debug")['value'] == "True"))