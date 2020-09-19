from flask import Flask, render_template, request, session, jsonify, send_file
from flask_socketio import SocketIO, send, emit, join_room, leave_room, rooms

import uuid

import os
from shutil import copyfile
import xml.etree.ElementTree as et
from xml.dom import minidom

import lxml.etree

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)


@socketio.on('join')
def on_join(data):
    username = data['username']
    room = data['room']
    join_room(room)
    send(username + ' has entered the room ' + room, room=room)
    session['username'] = username
    emit("setRoom", room)
    emit("setUser", username)

@socketio.on('leave')
def on_leave(data):
    username = data['username']
    room = data['room']
    leave_room(room)
    send(username + ' has left the room '+ room, room=room)
    emit("remRoom", room)
    session.pop('username', None)
    

@socketio.on('message')
def handle_message(message):
    mainroom = rooms()[1]

    reqfeed = "./feeds/" + mainroom + ".xml"
    msgid = str(uuid.uuid1().hex)
    if os.path.isfile(reqfeed):
        tree = et.parse(reqfeed)
        root = tree.getroot()

        et.SubElement(root[0], 'item')
        
        et.SubElement(root[0][-1], 'title')
        root[0][-1][-1].text = "message"
        et.SubElement(root[0][-1], 'username')
        root[0][-1][-1].text = session['username']
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
        root[0][-1][-1].text = "message"
        et.SubElement(root[0][-1], 'username')
        root[0][-1][-1].text = session['username']
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




if __name__ == '__main__':
    socketio.run(app)