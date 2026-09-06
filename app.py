import os, hmac, hashlib, time
from flask import Flask, request, jsonify, send_from_directory, abort
SECRET=os.environ.get('SECRET','dev-secret').encode(); JITSI_DOMAIN=os.environ.get('JITSI_DOMAIN','meet.jit.si')
JAAS_APP_ID=os.environ.get('JAAS_APP_ID'); JAAS_KID=os.environ.get('JAAS_KID'); JAAS_KEY=os.environ.get('JAAS_KEY','').replace('\\n','\n')
app=Flask(__name__,static_folder='static',static_url_path='/static')
def token(room): return hmac.new(SECRET,room.encode(),hashlib.sha256).hexdigest()[:24]
def jitsi_room(room): return 'callroom-'+hmac.new(SECRET,('jitsi:'+room).encode(),hashlib.sha256).hexdigest()[:16]
def jaas_jwt(name):
    import jwt
    now=int(time.time()); payload={'aud':'jitsi','iss':'chat','sub':JAAS_APP_ID,'room':'*','exp':now+7200,'nbf':now-10,'context':{'user':{'name':name,'moderator':'true'},'features':{'livestreaming':'false','recording':'false','transcription':'false','outbound-call':'false'}}}
    return jwt.encode(payload,JAAS_KEY,algorithm='RS256',headers={'kid':JAAS_KID,'typ':'JWT'})
@app.get('/')
def index(): return send_from_directory('static','index.html')
@app.get('/api/newroom')
def newroom(): r=hashlib.sha256(os.urandom(16)).hexdigest()[:8]; return jsonify(room=r,token=token(r))
@app.get('/api/jitsi/<room>')
def jitsi(room):
    if not hmac.compare_digest(request.args.get('token',''),token(room)): abort(403)
    name=request.args.get('name','guest')[:32]
    if JAAS_APP_ID and JAAS_KID and JAAS_KEY: return jsonify(domain='8x8.vc',roomName=JAAS_APP_ID+'/'+jitsi_room(room),jwt=jaas_jwt(name),mode='jaas')
    return jsonify(domain=JITSI_DOMAIN,roomName=jitsi_room(room),jwt=None,mode='public')
if __name__=='__main__': app.run(port=int(os.environ.get('PORT',8000)),threaded=True)