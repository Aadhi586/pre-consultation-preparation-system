"""Minimal standard-library HTTP/SQLite backend for the pre-consultation app."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse
import base64, hashlib, hmac, json, os, secrets, smtplib, sqlite3, time
from email.message import EmailMessage

ROOT = Path(__file__).resolve().parent
DB = Path(os.environ.get('APP_DB', str(ROOT / 'data' / 'preconsultation.sqlite3')))
SECRET = os.environ.get('APP_SECRET', 'development-only-change-this-secret')
COOKIE = 'prep_session'
PUBLIC_URL = os.environ.get('APP_PUBLIC_URL', 'http://127.0.0.1:8000').rstrip('/')

def connect():
    DB.parent.mkdir(exist_ok=True)
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
    c.execute('PRAGMA foreign_keys=ON'); return c

def init_db():
    with connect() as c:
        c.executescript('''CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,email TEXT UNIQUE NOT NULL,name TEXT NOT NULL,password TEXT NOT NULL,created REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY,user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,expires REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS resets(token_hash TEXT PRIMARY KEY,user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,expires REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS consultations(id TEXT PRIMARY KEY,user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,created REAL NOT NULL,payload TEXT NOT NULL);''')

def pw_hash(pw, salt=None):
    salt = salt or secrets.token_bytes(16)
    return base64.b64encode(salt + hashlib.pbkdf2_hmac('sha256', pw.encode(), salt, 240000)).decode()
def pw_ok(pw, encoded):
    try:
        raw=base64.b64decode(encoded); return hmac.compare_digest(raw[16:],hashlib.pbkdf2_hmac('sha256',pw.encode(),raw[:16],240000))
    except Exception: return False
def sign(token):
    sig=hmac.new(SECRET.encode(),token.encode(),hashlib.sha256).digest()
    return token+'.'+base64.urlsafe_b64encode(sig).decode().rstrip('=')

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*a,**kw): super().__init__(*a,directory=str(ROOT),**kw)
    def log_message(self, fmt, *args): pass
    def body(self):
        n=int(self.headers.get('Content-Length','0'))
        if n>200000: raise ValueError('Request is too large')
        return json.loads(self.rfile.read(n) or b'{}')
    def send_json(self,status,obj):
        b=json.dumps(obj,ensure_ascii=False).encode(); self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Content-Length',str(len(b))); self.send_header('Cache-Control','no-store'); self.end_headers(); self.wfile.write(b)
    def session_user(self):
        raw=self.headers.get('Cookie',''); value=next((x.split('=',1)[1] for x in raw.split('; ') if x.startswith(COOKIE+'=')), '')
        try:
            token,sig=value.rsplit('.',1); expected=sign(token).rsplit('.',1)[1]
            if not hmac.compare_digest(sig,expected): return None
        except ValueError: return None
        with connect() as c:
            digest=hashlib.sha256(token.encode()).hexdigest()
            row=c.execute('SELECT u.id,u.email,u.name FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token=? AND s.expires>?',(digest,time.time())).fetchone()
            return dict(row) if row else None
    def set_session(self,uid):
        token=secrets.token_urlsafe(32)
        digest=hashlib.sha256(token.encode()).hexdigest()
        with connect() as c: c.execute('INSERT INTO sessions VALUES(?,?,?)',(digest,uid,time.time()+60*60*24*14))
        self.send_header('Set-Cookie',f'{COOKIE}={sign(token)}; HttpOnly; SameSite=Strict; Path=/; Max-Age=1209600')
    def do_GET(self):
        path=urlparse(self.path).path
        if path.startswith('/api/'):
            u=self.session_user()
            if path=='/api/me': return self.send_json(200,{'user':u})
            if not u: return self.send_json(401,{'error':'Please sign in to continue.'})
            if path=='/api/consultations':
                with connect() as c: rows=c.execute('SELECT id,created,payload FROM consultations WHERE user_id=? ORDER BY created DESC',(u['id'],)).fetchall()
                return self.send_json(200,{'consultations':[{'id':r['id'],'created':r['created'],'data':json.loads(r['payload'])} for r in rows]})
            if path.startswith('/api/consultations/'):
                cid=path.rsplit('/',1)[-1]
                with connect() as c: r=c.execute('SELECT id,created,payload FROM consultations WHERE id=? AND user_id=?',(cid,u['id'])).fetchone()
                return self.send_json(200,{'consultation':{'id':r['id'],'created':r['created'],'data':json.loads(r['payload'])}}) if r else self.send_json(404,{'error':'Consultation not found.'})
            return self.send_json(404,{'error':'Not found.'})
        if path=='/': self.path='/index.html'
        return super().do_GET()
    def do_POST(self):
        path=urlparse(self.path).path
        try: d=self.body()
        except Exception as e: return self.send_json(400,{'error':'Please check the information and try again.'})
        if path=='/api/register':
            name=str(d.get('name','')).strip(); email=str(d.get('email','')).strip().lower(); pw=str(d.get('password',''))
            if len(name)<2 or len(name)>80 or '@' not in email or len(email)>254 or len(pw)<10: return self.send_json(400,{'error':'Enter your name, a valid email, and a password with at least 10 characters.'})
            try:
                with connect() as c: cur=c.execute('INSERT INTO users(email,name,password,created) VALUES(?,?,?,?)',(email,name,pw_hash(pw),time.time())); uid=cur.lastrowid
                self.send_response(201); self.set_session(uid); self.send_header('Content-Type','application/json'); self.end_headers(); self.wfile.write(json.dumps({'user':{'id':uid,'email':email,'name':name}}).encode())
            except sqlite3.IntegrityError: self.send_json(409,{'error':'An account with that email already exists.'})
            return
        if path=='/api/login':
            email=str(d.get('email','')).strip().lower(); pw=str(d.get('password',''))
            with connect() as c: u=c.execute('SELECT * FROM users WHERE email=?',(email,)).fetchone()
            if not u or not pw_ok(pw,u['password']): return self.send_json(401,{'error':'Email or password was not recognised.'})
            self.send_response(200); self.set_session(u['id']); self.send_header('Content-Type','application/json'); self.end_headers(); self.wfile.write(json.dumps({'user':{'id':u['id'],'email':u['email'],'name':u['name']}}).encode()); return
        if path=='/api/logout':
            cookie=self.headers.get('Cookie',''); value=next((x.split('=',1)[1] for x in cookie.split('; ') if x.startswith(COOKIE+'=')), '')
            try:
                token=value.rsplit('.',1)[0]; digest=hashlib.sha256(token.encode()).hexdigest()
                with connect() as c: c.execute('DELETE FROM sessions WHERE token=?',(digest,))
            except Exception: pass
            self.send_response(200); self.send_header('Set-Cookie',f'{COOKIE}=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0'); self.send_header('Content-Type','application/json'); self.end_headers(); self.wfile.write(b'{"ok":true}'); return
        if path=='/api/forgot':
            email=str(d.get('email','')).strip().lower(); token=secrets.token_urlsafe(32)
            with connect() as c:
                u=c.execute('SELECT id FROM users WHERE email=?',(email,)).fetchone()
                if u:
                    digest=hashlib.sha256(token.encode()).hexdigest(); c.execute('INSERT INTO resets VALUES(?,?,?)',(digest,u['id'],time.time()+1800))
                    host=os.environ.get('SMTP_HOST')
                    if host:
                        msg=EmailMessage(); msg['Subject']='Reset your preparation system password'; msg['From']=os.environ.get('SMTP_FROM',os.environ.get('SMTP_USER','')); msg['To']=email; msg.set_content('Use this link within 30 minutes to reset your password: '+PUBLIC_URL+'/?reset='+token)
                        with smtplib.SMTP(host,int(os.environ.get('SMTP_PORT','587'))) as s:
                            s.starttls(); s.login(os.environ.get('SMTP_USER',''),os.environ.get('SMTP_PASSWORD','')); s.send_message(msg)
                    elif os.environ.get('APP_ENV')=='development': return self.send_json(200,{'message':'If that account exists, a reset link is available in the server log.','development_token':token})
            return self.send_json(200,{'message':'If an account exists for that email, a reset link will be sent.'})
        if path=='/api/reset':
            token=str(d.get('token','')); pw=str(d.get('password',''))
            if len(pw)<10: return self.send_json(400,{'error':'Use a password with at least 10 characters.'})
            digest=hashlib.sha256(token.encode()).hexdigest()
            with connect() as c:
                r=c.execute('SELECT user_id FROM resets WHERE token_hash=? AND expires>?',(digest,time.time())).fetchone()
                if not r: return self.send_json(400,{'error':'This reset link has expired or was already used.'})
                c.execute('UPDATE users SET password=? WHERE id=?',(pw_hash(pw),r['user_id'])); c.execute('DELETE FROM resets WHERE user_id=?',(r['user_id'],)); c.execute('DELETE FROM sessions WHERE user_id=?',(r['user_id'],))
            return self.send_json(200,{'message':'Password updated. Please sign in.'})
        u=self.session_user()
        if not u: return self.send_json(401,{'error':'Please sign in to continue.'})
        if path=='/api/consultations':
            d.pop('id',None); d.pop('created',None)
            if not str(d.get('complaint','')).strip() or not str(d.get('description','')).strip() or not str(d.get('duration','')).strip() or not str(d.get('severity','')).strip(): return self.send_json(400,{'error':'Complete the required concern, description, duration and severity fields.'})
            try:
                weight=d.get('weight')
                if weight not in (None,'') and not 1<=float(weight)<=500: return self.send_json(400,{'error':'Weight must be between 1 and 500 kg.'})
            except (TypeError,ValueError): return self.send_json(400,{'error':'Enter a valid weight in kilograms.'})
            cid=secrets.token_urlsafe(12); created=time.time()
            with connect() as c: c.execute('INSERT INTO consultations VALUES(?,?,?,?)',(cid,u['id'],created,json.dumps(d,ensure_ascii=False)))
            return self.send_json(201,{'id':cid,'created':created})
        return self.send_json(404,{'error':'Not found.'})

if __name__=='__main__':
    init_db(); print('Pre-consultation app: http://127.0.0.1:8000')
    ThreadingHTTPServer(('127.0.0.1',8000),Handler).serve_forever()
