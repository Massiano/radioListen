import os, threading
from flask import Flask, send_from_directory
from flask_sock import Sock
app=Flask(__name__,static_folder='static',static_url_path='/static'); sock=Sock(app)
rooms={}; lock=threading.Lock()
def room(r): return rooms.setdefault(r,{'header':None,'listeners':set(),'live':False})
@app.get('/')
def index(): return send_from_directory('static','relay.html')
@app.get('/listen')
def listen_page(): return send_from_directory('static','listen.html')
@sock.route('/ws/up/<r>')
def up(ws,r):
    with lock: R=room(r); R['header']=None; R['live']=True
    try:
        while True:
            data=ws.receive()
            if data is None: break
            with lock:
                if R['header'] is None: R['header']=data
                dead=[]
                for l in list(R['listeners']):
                    try: l.send(data)
                    except Exception: dead.append(l)
                for l in dead: R['listeners'].discard(l)
    finally:
        with lock: R['live']=False; R['header']=None
@sock.route('/ws/down/<r>')
def down(ws,r):
    with lock: R=room(r); R['listeners'].add(ws); h=R['header']
    try:
        if h: ws.send(h)
        while ws.receive() is not None: pass
    finally:
        with lock: R['listeners'].discard(ws)
@app.get('/api/status/<r>')
def status(r):
    with lock: R=room(r); return {'live':R['live'],'listeners':len(R['listeners'])}
if __name__=='__main__': app.run(port=int(os.environ.get('PORT',8000)),threaded=True)
