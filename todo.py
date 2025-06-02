"""
app.py — Comprehensive Flask To-Do App v2.0 (full unabridged source, ~550 lines)

Dependencies (install via pip):
    Flask
    Flask-SQLAlchemy
    Flask-Migrate
    Flask-Login
    Flask-Mail
    Flask-SocketIO
    python-dateutil
"""

import os
import io
import csv
import threading
import time
from datetime import datetime
from dateutil import rrule
from flask import (
    Flask, render_template_string, request, redirect, url_for,
    jsonify, abort, flash, send_file
)
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import (
    LoginManager, UserMixin,
    login_user, logout_user,
    login_required, current_user
)
from flask_mail import Mail, Message
from flask_socketio import SocketIO, emit, join_room

# ─── App & Config ─────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config.update(
    DEBUG=True,
    SECRET_KEY=os.getenv('SECRET_KEY', 'super-secret-key'),
    SQLALCHEMY_DATABASE_URI='sqlite:///todo.db',
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME='stanlleylocke@gmail.com',
    MAIL_PASSWORD='frkapidnttktojxa',
    MAIL_DEFAULT_SENDER=('Flask ToDo', 'stanlleywasonga@gmail.com')
)

db       = SQLAlchemy(app)
migrate  = Migrate(app, db)

login    = LoginManager(app)
login.login_view    = 'login'                   # ← Redirects unauthorized to /login
login.login_message = "Please log in to access this page."

mail     = Mail(app)
socketio = SocketIO(app)

# ─── Models & Relations ───────────────────────────────────────────────────────
task_tags = db.Table('task_tags',
    db.Column('task_id', db.Integer, db.ForeignKey('task.id'), primary_key=True),
    db.Column('tag_id',  db.Integer, db.ForeignKey('tag.id'),  primary_key=True)
)

class User(db.Model, UserMixin):
    id       = db.Column(db.Integer, primary_key=True)
    email    = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    tasks    = db.relationship('Task', backref='owner', lazy=True)

@login.user_loader
def load_user(uid):
    return User.query.get(int(uid))

class Tag(db.Model):
    id   = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True, nullable=False)

class Task(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text,    nullable=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    due_time    = db.Column(db.DateTime, nullable=False)
    priority    = db.Column(db.Enum('Low','Med','High','Critical', name='priority'), default='Med')
    recur_rule  = db.Column(db.String(10), nullable=True)   # 'DAILY','WEEKLY','MONTHLY'
    category    = db.Column(db.String(50), nullable=True)
    alarm_on    = db.Column(db.Boolean, default=False)
    completed   = db.Column(db.Boolean, default=False)
    user_id     = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tags        = db.relationship('Tag', secondary=task_tags, lazy='subquery',
                      backref=db.backref('tasks', lazy=True))

    def as_dict(self):
        return {
            'id':          self.id,
            'title':       self.title,
            'description': self.description,
            'created_at':  self.created_at.isoformat(),
            'due_time':    self.due_time.isoformat(),
            'priority':    self.priority,
            'recur_rule':  self.recur_rule,
            'category':    self.category,
            'alarm_on':    self.alarm_on,
            'completed':   self.completed,
            'tags':        [t.name for t in self.tags]
        }

with app.app_context():
    db.create_all()

# ─── Background Alarm & Recurrence Processor ─────────────────────────────────
def alarm_and_recur():
    while True:
        with app.app_context():
            now = datetime.now()
            due_tasks = Task.query.filter_by(alarm_on=True, completed=False).all()
            for t in due_tasks:
                if t.due_time <= now:
                    # Email notification
                    try:
                        msg = Message(f"Task Due: {t.title}",
                                      recipients=[t.owner.email])
                        msg.body = f"Your task “{t.title}” is due now ({t.due_time})."
                        mail.send(msg)
                    except Exception as e:
                        print("Email send failed:", e)
                    # Recurrence logic
                    if t.recur_rule in ('DAILY','WEEKLY','MONTHLY'):
                        rule = getattr(rrule, t.recur_rule)
                        next_dt = list(rule(dtstart=t.due_time, count=2))[-1]
                        t.due_time = next_dt
                        t.alarm_on = True
                    else:
                        t.alarm_on = False
            db.session.commit()
        time.sleep(30)

threading.Thread(target=alarm_and_recur, daemon=True).start()

# ─── Real-Time Broadcast ──────────────────────────────────────────────────────
def broadcast_tasks():
    tasks = [t.as_dict() for t in Task.query
             .filter_by(user_id=current_user.id)
             .order_by(Task.due_time)
             .all()]
    socketio.emit('tasks', {'tasks': tasks}, to=f'user_{current_user.id}')

@socketio.on('join')
def handle_join(data):
    room = f'user_{current_user.id}'
    join_room(room)
    emit('joined', {'room': room})

# ─── Authentication Routes ────────────────────────────────────────────────────
LOGIN_HTML = """
<!doctype html>
<title>Login</title>
<h2>Login</h2>
<form method="post">
  <input name="email" type="email" placeholder="Email" required><br>
  <input name="password" type="password" placeholder="Password" required><br>
  <button type="submit">Log In</button>
</form>
<p>Or <a href="{{ url_for('register') }}">Register</a></p>
{% with msg = get_flashed_messages() %}
  {% if msg %}<p style="color:red">{{ msg[0] }}</p>{% endif %}
{% endwith %}
"""

REGISTER_HTML = """
<!doctype html>
<title>Register</title>
<h2>Register</h2>
<form method="post">
  <input name="email" type="email" placeholder="Email" required><br>
  <input name="password" type="password" placeholder="Password" required><br>
  <button type="submit">Register</button>
</form>
<p>Or <a href="{{ url_for('login') }}">Login</a></p>
{% with msg = get_flashed_messages() %}
  {% if msg %}<p style="color:red">{{ msg[0] }}</p>{% endif %}
{% endwith %}
"""

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        if User.query.filter_by(email=request.form['email']).first():
            flash('Email already registered')
        else:
            u = User(email=request.form['email'], password=request.form['password'])
            db.session.add(u)
            db.session.commit()
            login_user(u)
            return redirect(url_for('index'))
    return render_template_string(REGISTER_HTML)

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        u = User.query.filter_by(email=request.form['email']).first()
        if u and u.password == request.form['password']:
            login_user(u)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        flash('Invalid credentials')
    return render_template_string(LOGIN_HTML)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ─── CSV Export ───────────────────────────────────────────────────────────────
@app.route('/export')
@login_required
def export():
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(['ID','Title','Due','Priority','Category','Completed','Tags'])
    for t in Task.query.filter_by(user_id=current_user.id):
        writer.writerow([
            t.id,
            t.title,
            t.due_time,
            t.priority,
            t.category,
            t.completed,
            ";".join([tg.name for tg in t.tags])
        ])
    buf.seek(0)
    return send_file(
        io.BytesIO(buf.read().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name='tasks.csv'
    )

# ─── Notifications API ────────────────────────────────────────────────────────
@app.route('/api/notifications')
@login_required
def notifications():
    now = datetime.now()
    due = Task.query.filter_by(
        user_id=current_user.id,
        alarm_on=True,
        completed=False
    ).filter(Task.due_time <= now).all()
    for t in due:
        t.alarm_on = False
    db.session.commit()
    return jsonify([t.as_dict() for t in due])

# ─── REST API for Tasks ───────────────────────────────────────────────────────
@app.route('/api/tasks', methods=['GET','POST'])
@login_required
def api_tasks():
    if request.method == 'GET':
        return jsonify([
            t.as_dict()
            for t in Task.query
                         .filter_by(user_id=current_user.id)
                         .order_by(Task.due_time)
        ])
    data = request.get_json() or {}
    try:
        due = datetime.fromisoformat(data['due_time'])
    except:
        abort(400, 'Invalid due_time; use ISO format')
    t = Task(
        title       = data.get('title', ''),
        description = data.get('description', ''),
        due_time    = due,
        priority    = data.get('priority', 'Med'),
        recur_rule  = data.get('recur_rule'),
        category    = data.get('category'),
        alarm_on    = bool(data.get('alarm_on', False)),
        completed   = bool(data.get('completed', False)),
        owner       = current_user
    )
    # tags
    if 'tags' in data:
        t.tags = []
        for name in data['tags']:
            tg = Tag.query.filter_by(name=name).first() or Tag(name=name)
            t.tags.append(tg)
    db.session.add(t)
    db.session.commit()
    broadcast_tasks()
    return jsonify(t.as_dict()), 201

@app.route('/api/tasks/<int:id>', methods=['GET','PUT','DELETE'])
@login_required
def api_task_detail(id):
    t = Task.query.filter_by(user_id=current_user.id, id=id).first_or_404()
    if request.method == 'GET':
        return jsonify(t.as_dict())
    if request.method == 'PUT':
        data = request.get_json() or {}
        for fld in ('title','description','priority','category','recur_rule'):
            if fld in data: setattr(t, fld, data[fld])
        if 'due_time' in data:
            t.due_time = datetime.fromisoformat(data['due_time'])
        for bool_fld in ('alarm_on','completed'):
            if bool_fld in data: setattr(t, bool_fld, bool(data[bool_fld]))
        if 'tags' in data:
            t.tags = []
            for name in data['tags']:
                tg = Tag.query.filter_by(name=name).first() or Tag(name=name)
                t.tags.append(tg)
        db.session.commit()
        broadcast_tasks()
        return jsonify(t.as_dict())
    # DELETE
    db.session.delete(t)
    db.session.commit()
    broadcast_tasks()
    return '', 204

# ─── Web Views (Index, Add/Edit, Delete, Complete) ────────────────────────────
BASE_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <link rel="icon" href="{{ url_for('static', filename='favicon.ico') }}">
  <title>Flask To-Do</title>
  <link href="https://cdn.jsdelivr.net/npm/fullcalendar@6.1.8/main.min.css" rel="stylesheet">
  <style>
    body{font-family:Segoe UI,sans-serif;background:#f8f9fa;margin:0;padding:0}
    .dark body{background:#222;color:#ddd}
    .container{max-width:900px;margin:auto;padding:20px}
    h1{text-align:center}
    .btn{display:inline-block;padding:8px 12px;background:#007bff;color:#fff;text-decoration:none;border-radius:4px}
    ul.tasks{list-style:none;padding:0}
    ul.tasks li{background:#fff;margin:10px 0;padding:15px;border-left:5px solid #007bff;border-radius:6px}
    ul.tasks li.done{opacity:.6;text-decoration:line-through}
    .actions a{margin-right:8px;color:#007bff;text-decoration:none}
    form input, form textarea, form select{width:100%;margin-bottom:8px;padding:6px}
    .flex{display:flex;gap:10px;flex-wrap:wrap}
    /* mobile */
    @media(max-width:600px){.flex{flex-direction:column}}
  </style>
</head>
<body>
<div class="container">
  <h1>📝 Flask To-Do</h1>
  <div class="flex" style="margin-bottom:10px">
    <a class="btn" href="{{ url_for('add') }}">+ New Task</a>
    <a class="btn" href="{{ url_for('export') }}">Export CSV</a>
    <button id="darkToggle" class="btn">Toggle Dark</button>
    <a class="btn" href="{{ url_for('logout') }}">Logout</a>
  </div>
  <div style="margin-bottom:15px">
    <input id="search" placeholder="Search…" value="{{ q }}">
    <select id="filterPrio"><option value="">All Priorities</option>
      {% for p in ['Low','Med','High','Critical'] %}
        <option value="{{p}}" {% if prio==p %}selected{% endif %}>{{p}}</option>
      {% endfor %}
    </select>
    <select id="filterCat"><option value="">All Categories</option>
      {% for c in categories %}
        <option value="{{c}}" {% if cat==c %}selected{% endif %}>{{c}}</option>
      {% endfor %}
    </select>
    <button id="applyFilters" class="btn">Apply</button>
  </div>
  <div id="calendar"></div>
  <ul class="tasks" id="taskList">
    {% for t in tasks %}
      <li data-id="{{t.id}}" class="{{ 'done' if t.completed else '' }}">
        <h3>{{t.title}} <small>({{t.priority}})</small></h3>
        <p>{{t.description}}</p>
        <p><strong>Due:</strong> {{t.due_time.strftime('%Y-%m-%d %H:%M')}}</p>
        <p>
          <strong>Tags:</strong> {{ ", ".join(tg.name for tg in t.tags) }}
          | <strong>Cat:</strong> {{t.category or '–'}}
        </p>
        <div class="actions">
          <a href="{{ url_for('edit',id=t.id) }}">Edit</a>
          <a href="{{ url_for('delete',id=t.id) }}" onclick="return confirm('Delete?')">Delete</a>
          <a href="{{ url_for('complete',id=t.id) }}">
            {{'Unmark' if t.completed else 'Complete'}}
          </a>
        </div>
      </li>
    {% else %}
      <p>No tasks found.</p>
    {% endfor %}
  </ul>
</div>
<script src="https://cdn.jsdelivr.net/npm/fullcalendar@6.1.8/main.min.js"></script>
<script src="//cdnjs.cloudflare.com/ajax/libs/socket.io/4.5.4/socket.io.min.js"></script>
<script>
  // Dark mode
  const body = document.documentElement;
  if(localStorage.dark==='yes') body.classList.add('dark');
  document.getElementById('darkToggle').onclick = ()=>{
    body.classList.toggle('dark');
    localStorage.dark = body.classList.contains('dark')?'yes':'no';
  };
  // Filters & search
  document.getElementById('applyFilters').onclick = ()=>{
    const q = document.getElementById('search').value;
    const prio = document.getElementById('filterPrio').value;
    const cat = document.getElementById('filterCat').value;
    const params = new URLSearchParams();
    if(q) params.set('q',q);
    if(prio) params.set('priority',prio);
    if(cat) params.set('category',cat);
    window.location = `/?${params.toString()}`;
  };
  // FullCalendar
  document.addEventListener('DOMContentLoaded', function(){
    const calEl = document.getElementById('calendar');
    const calendar = new FullCalendar.Calendar(calEl,{initialView:'dayGridMonth'});
    calendar.render();
    // load events
    fetch('/api/tasks').then(r=>r.json()).then(data=>{
      data.forEach(t=>{
        calendar.addEvent({title:t.title,start:t.due_time});
      });
    });
  });
  // Socket.IO real-time
  const socket = io();
  socket.on('connect', ()=> socket.emit('join'));
  socket.on('tasks', msg=>{
    window.location.reload();
  });
  // Web notifications polling
  if('Notification' in window) Notification.requestPermission();
  setInterval(()=>{
    fetch('/api/notifications').then(r=>r.json()).then(d=>{
      d.forEach(t=>{
        if(Notification.permission==='granted'){
          new Notification('Task Due: '+t.title,{
            body:new Date(t.due_time).toLocaleString()
          });
        }
      });
    });
  },30000);
</script>
</body>
</html>
"""

ADD_EDIT_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{{ 'Edit' if task else 'New' }} Task</title>
  <style>
    body{font-family:Segoe UI,sans-serif;background:#f8f9fa;margin:0;padding:20px}
    .form{max-width:500px;margin:auto;background:#fff;padding:20px;border-radius:8px}
    .form input,.form textarea,.form select{width:100%;margin:8px 0;padding:6px}
    .form button{padding:8px 12px;background:#007bff;color:#fff;border:none;border-radius:4px;cursor:pointer}
  </style>
</head>
<body>
<div class="form">
  <h2>{{ 'Edit' if task else 'New' }} Task</h2>
  <form method="post">
    <input name="title" placeholder="Title" required value="{{ task.title if task else '' }}">
    <textarea name="description" placeholder="Description">{{ task.description if task else '' }}</textarea>
    <label>Due Time:</label>
    <input type="datetime-local" name="due_time" required
      value="{{ task.due_time.strftime('%Y-%m-%dT%H:%M') if task else '' }}">
    <label>Priority:</label>
    <select name="priority">
      {% for p in ['Low','Med','High','Critical'] %}
        <option value="{{p}}" {% if task and task.priority==p %}selected{% endif %}>{{p}}</option>
      {% endfor %}
    </select>
    <label>Recurrence:</label>
    <select name="recur_rule">
      <option value="">None</option>
      {% for r in ['DAILY','WEEKLY','MONTHLY'] %}
        <option value="{{r}}" {% if task and task.recur_rule==r %}selected{% endif %}>{{r}}</option>
      {% endfor %}
    </select>
    <input name="category" placeholder="Category" value="{{ task.category if task else '' }}">
    <label>Tags (comma-separated):</label>
    <input name="tags" value="{{ ','.join(tg.name for tg in task.tags) if task else '' }}">
    <label><input type="checkbox" name="alarm_on" {% if task and task.alarm_on %}checked{% endif %}> Enable Alarm</label>
    <label><input type="checkbox" name="completed" {% if task and task.completed %}checked{% endif %}> Completed</label>
    <button type="submit">{{ 'Update' if task else 'Add' }} Task</button>
  </form>
  <p><a href="{{ url_for('index') }}">← Back to List</a></p>
</div>
</body>
</html>
"""

@app.route('/')
@login_required
def index():
    q     = request.args.get('q', '')
    prio  = request.args.get('priority', '')
    cat   = request.args.get('category', '')
    tasks = Task.query.filter_by(user_id=current_user.id)
    if q:
        tasks = tasks.filter(Task.title.contains(q) | Task.description.contains(q))
    if prio:
        tasks = tasks.filter_by(priority=prio)
    if cat:
        tasks = tasks.filter_by(category=cat)
    tasks = tasks.order_by(Task.due_time).all()
    categories = [c[0] for c in db.session.query(Task.category).distinct()]
    return render_template_string(
        BASE_HTML, tasks=tasks, q=q, prio=prio, cat=cat, categories=categories
    )

@app.route('/add', methods=['GET','POST'])
@login_required
def add():
    if request.method == 'POST':
        data = request.form
        t = Task(
            title       = data['title'],
            description = data['description'],
            due_time    = datetime.fromisoformat(data['due_time']),
            priority    = data.get('priority', 'Med'),
            recur_rule  = data.get('recur_rule'),
            category    = data.get('category'),
            alarm_on    = 'alarm_on' in data,
            completed   = 'completed' in data,
            owner       = current_user
        )
        tags_in = [n.strip() for n in data.get('tags','').split(',') if n.strip()]
        for name in tags_in:
            tg = Tag.query.filter_by(name=name).first() or Tag(name=name)
            t.tags.append(tg)
        db.session.add(t)
        db.session.commit()
        broadcast_tasks()
        return redirect(url_for('index'))
    return render_template_string(ADD_EDIT_HTML, task=None)

@app.route('/edit/<int:id>', methods=['GET','POST'])
@login_required
def edit(id):
    t = Task.query.filter_by(user_id=current_user.id, id=id).first_or_404()
    if request.method == 'POST':
        data = request.form
        t.title, t.description = data['title'], data['description']
        t.due_time    = datetime.fromisoformat(data['due_time'])
        t.priority    = data.get('priority', 'Med')
        t.recur_rule  = data.get('recur_rule')
        t.category    = data.get('category')
        t.alarm_on    = 'alarm_on' in data
        t.completed   = 'completed' in data
        t.tags.clear()
        for name in [n.strip() for n in data.get('tags','').split(',') if n.strip()]:
            tg = Tag.query.filter_by(name=name).first() or Tag(name=name)
            t.tags.append(tg)
        db.session.commit()
        broadcast_tasks()
        return redirect(url_for('index'))
    return render_template_string(ADD_EDIT_HTML, task=t)

@app.route('/delete/<int:id>')
@login_required
def delete(id):
    t = Task.query.filter_by(user_id=current_user.id, id=id).first_or_404()
    db.session.delete(t)
    db.session.commit()
    broadcast_tasks()
    return redirect(url_for('index'))

@app.route('/complete/<int:id>')
@login_required
def complete(id):
    t = Task.query.filter_by(user_id=current_user.id, id=id).first_or_404()
    t.completed = not t.completed
    db.session.commit()
    broadcast_tasks()
    return redirect(url_for('index'))

# ─── Service Worker Stub ──────────────────────────────────────────────────────
@app.route('/sw.js')
def sw():
    js = """
self.addEventListener('install', e => self.skipWaiting());
self.addEventListener('activate', e => clients.claim());
self.addEventListener('fetch', e => {/* cache logic here */});
    """
    return js, 200, {'Content-Type': 'application/javascript'}

# ─── Run App ──────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    socketio.run(app, port=5001, debug=True)
