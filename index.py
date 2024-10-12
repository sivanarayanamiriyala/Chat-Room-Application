from flask import Flask,render_template,session,request,redirect,url_for
from flask_socketio import SocketIO,join_room,leave_room,send
import random
from string import ascii_uppercase


app=Flask(__name__)
app.config['SECRET_KEY']='chatroom'
socketio = SocketIO(app)

rooms={}

@app.route('/')
def home():
	return render_template('home.html')

def generate_roomcode(length):
	code=""
	while True:
		for _ in range(length):
			code+=random.choice(ascii_uppercase)
		if code not in rooms:
			break
	return code

@app.route('/chatroom')
def chatroom():
	if 'code' not in session or 'name' not in session:
		return redirect(url_for('home'))  

	name=session['name']
	code=session['code']
    
	if code and code in rooms:
		return render_template('room.html',name=name,code=code,messages=rooms[code]["messages"] )
	return render_template('home.html')

@socketio.on("connect")
def connect(auth):
    code= session.get("code")
    name = session.get("name")
    if not code or not name:
        return
    if code not in rooms:
        leave_room(code)
        return
    join_room(code)
    send({"name": name, "message": "has entered the room"}, to=code)
    rooms[code]["members"] += 1

@socketio.on("message")
def message(data):
    code = session.get("code")
    if code not in rooms:
        return 
    
    content = {
        "name": session.get("name"),
        "message": data["message"]
    }
    send(content, to=code)
    rooms[code]["messages"].append(content)
    print(f"{session.get('name')} said: {data['message']}")

@socketio.on("disconnect")
def disconnect():
    code = session.get("code")
    name = session.get("name")
    leave_room(code)

    if code in rooms:
        rooms[code]["members"] -= 1
        if rooms[code]["members"] <= 0:
            del rooms[code]
    
    send({"name": name, "message": "has left the room"}, to=code)
    print(f"{name} has left the room {code}")	
    session.clear()
	


@app.route('/verify',methods=["POST"])
def verify():
	if request.method=="POST":
		creatername=request.form.get('creatername')
		create=request.form.get('create',False)
		joincode=request.form.get('joincode')
		join=request.form.get('join',False)
		if not creatername:
			return render_template('home.html',error="Enter Name to Create Room or join in the room")					
		if create:
			if creatername:
				room=generate_roomcode(4)
				rooms[room]={'members':0,'messages':[]}
				session['code']=room
				session['name']=creatername
				return redirect(url_for('chatroom'))
		if join:
			session['name']=creatername
			session['code']=joincode
			if not joincode or joincode not in rooms:
				return render_template('home.html',error="Enter a valid Join Code")					
			return redirect(url_for('chatroom'))

	return render_template('home.html')

if __name__=="__main__":
	socketio.run(app,debug=True)