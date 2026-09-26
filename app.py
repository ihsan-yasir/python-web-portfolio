"""Three local portfolio demos. Python 3.10+, standard library only."""
import argparse
from contextlib import contextmanager
import datetime as dt
import html
import os
from pathlib import Path
import secrets
import sqlite3
from http.cookies import SimpleCookie
from urllib.parse import parse_qs, urlencode
from wsgiref.simple_server import make_server

ROOT = Path(__file__).resolve().parent
PRODUCTS = {1: ('Riva ceramic vase', 'Hand-finished stoneware · Sand', 9800, '◒'),
            2: ('Lume table lamp', 'Soft light · Brushed brass', 16500, '◠'),
            3: ('Campo lounge chair', 'A quiet place to pause · Terracotta', 78000, '▰'),
            4: ('Linea serving tray', 'Natural oak · Everyday essentials', 4500, '▱')}
CSS = '''
:root{--ink:#173c3a;--paper:#f6f4ee;--muted:#687672;--line:#dce2db;--accent:#205e56}*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.6 system-ui,sans-serif}a{color:inherit;text-decoration:none}header{border-bottom:1px solid var(--line);background:#ffffffb8}nav,.wrap{max-width:1160px;margin:auto;padding:24px 32px}nav{display:flex;align-items:center;gap:28px;flex-wrap:wrap}.brand{font:bold 28px Georgia,serif;margin-right:auto}.navlink{font-size:14px}.navlink:hover{text-decoration:underline}.badge,.eyebrow{font-size:11px;letter-spacing:2px;text-transform:uppercase}.badge{border:1px solid var(--line);padding:6px 10px;border-radius:20px}.hero{display:grid;grid-template-columns:1.2fr 1fr;gap:50px;align-items:center;padding:65px 0}h1{font:clamp(38px,6vw,72px)/1.06 Georgia,serif;letter-spacing:-2px;margin:20px 0}h2{font:34px/1.2 Georgia,serif}h3{font-size:19px;margin:10px 0}p{color:var(--muted)}.lead{font-size:19px;max-width:560px}.button,button{display:inline-block;border:0;border-radius:5px;background:var(--accent);color:white;padding:13px 20px;font:600 14px system-ui;cursor:pointer}.button:hover,button:hover{filter:brightness(.88)}.secondary{background:white;color:var(--ink);border:1px solid var(--line)}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:22px}.card{background:white;border:1px solid var(--line);padding:26px;border-radius:12px}.art{min-height:350px;background:linear-gradient(140deg,#d5ded2,#7f9e92);border-radius:140px 140px 8px 8px;display:grid;place-items:center;overflow:hidden}.arch{width:55%;height:280px;border:35px solid #f3f0e5;border-bottom:0;border-radius:140px 140px 0 0;transform:translateY(65px);box-shadow:35px 5px 0 #587b6c}.section{padding:30px 0 55px}.split{display:grid;grid-template-columns:1fr 1fr;gap:40px}.field{display:block;margin:15px 0}input,textarea,select{display:block;width:100%;padding:12px;border:1px solid #acbbb2;border-radius:5px;background:white;color:#173c3a;font:inherit;margin-top:5px}textarea{min-height:120px}.notice{padding:14px 20px;background:#e2eee3;border:1px solid #acc4b3;border-radius:7px;margin:20px 0}.error{background:#fff0ec;border-color:#dc9f90}.small{font-size:13px;color:var(--muted)}footer{max-width:1160px;margin:40px auto 0;padding:25px 32px;border-top:1px solid var(--line);font-size:12px;color:var(--muted)}.store{--accent:#ad4b20;--ink:#34281f;--paper:#faf6ef}.store .grid{grid-template-columns:repeat(4,1fr)}.product-art{height:185px;background:#eee6d8;display:grid;place-items:center;font-size:115px;color:#a96c42;border-radius:8px}.price{font-size:23px;color:var(--ink)}.row{display:flex;gap:15px;align-items:center;justify-content:space-between;flex-wrap:wrap}.dashboard{--paper:#f0f4f7;--ink:#192c42;--accent:#277b79}.dashboard h1{font:700 38px/1.2 system-ui;letter-spacing:-1px}.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:18px;margin:28px 0}.stat strong{font-size:35px;display:block}.stat{background:#fff;border:1px solid var(--line);border-radius:10px;padding:20px}.table{overflow-x:auto}table{width:100%;border-collapse:collapse;text-align:left}td,th{padding:15px 12px;border-bottom:1px solid var(--line);font-size:14px}th{color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:1px}.pill{display:inline-block;background:#dff0eb;padding:4px 10px;border-radius:20px;font-size:12px;white-space:nowrap}.inline{display:flex;gap:8px;align-items:center}.inline select{min-width:125px;margin:0}.inline button{padding:10px}.danger{background:#934139}.empty{text-align:center;padding:50px}.bar{height:10px;background:#e1e8e7;border-radius:10px;overflow:hidden}.bar span{height:100%;display:block;background:#3d9d8f}.filters{display:flex;gap:10px;align-items:end;flex-wrap:wrap}.filters .field{flex:1;min-width:150px}.subnav{padding:10px 0;border-bottom:1px solid var(--line);display:flex;gap:25px;flex-wrap:wrap}.subnav a{font-size:12px;color:var(--muted)}:focus-visible{outline:3px solid #c98733;outline-offset:3px}@media(max-width:800px){.hero,.split{grid-template-columns:1fr}.hero{padding:30px 0;gap:25px}.grid,.store .grid,.stats{grid-template-columns:repeat(2,1fr)}nav,.wrap{padding:20px}.art{min-height:260px}.arch{height:240px}nav{gap:15px}h1{letter-spacing:-1px}}@media(max-width:480px){.grid,.store .grid{grid-template-columns:1fr}.stats{gap:10px}.stat{padding:12px}.brand{width:100%}.card{padding:20px}}
'''

def esc(value):
    return html.escape(str(value), quote=True)

def money(cents):
    return f'${cents / 100:,.2f}'

class Portfolio:
    def __init__(self, database=None, project='all'):
        self.database = str(database or ROOT / 'data' / 'portfolio.db')
        Path(self.database).parent.mkdir(parents=True, exist_ok=True)
        self.project = project
        self.sessions = {}
        with self.db() as con:
            con.executescript('''
            CREATE TABLE IF NOT EXISTS enquiries(id INTEGER PRIMARY KEY, name TEXT, email TEXT, message TEXT, created TEXT);
            CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY, session TEXT, total INTEGER, created TEXT);
            CREATE TABLE IF NOT EXISTS order_items(order_id INTEGER, product INTEGER, quantity INTEGER, unit_price INTEGER);
            CREATE TABLE IF NOT EXISTS tasks(id INTEGER PRIMARY KEY, title TEXT, project TEXT, status TEXT, due TEXT);
            CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT);
            ''')
            if not con.execute("SELECT 1 FROM settings WHERE key='seeded'").fetchone():
                today = dt.date.today()
                con.executemany('INSERT INTO tasks(title,project,status,due) VALUES(?,?,?,?)', [
                    ('Design landing page', 'Northline', 'In progress', str(today + dt.timedelta(days=3))),
                    ('Build product catalogue', 'Forma', 'To do', str(today + dt.timedelta(days=6))),
                    ('Review mobile layout', 'Northline', 'Done', str(today)),
                    ('Prepare project handover', 'Taskboard', 'To do', str(today + dt.timedelta(days=10)))])
                con.execute("INSERT INTO settings VALUES('seeded','yes')")

    @contextmanager
    def db(self):
        con = sqlite3.connect(self.database)
        con.row_factory = sqlite3.Row
        try:
            with con:
                yield con
        finally:
            con.close()

    def __call__(self, env, start_response):
        cookie = SimpleCookie()
        try:
            cookie.load(env.get('HTTP_COOKIE', ''))
        except Exception:
            pass
        sid = cookie['portfolio'].value if 'portfolio' in cookie else ''
        if sid not in self.sessions:
            sid = secrets.token_urlsafe(24)
            self.sessions[sid] = {'csrf': secrets.token_urlsafe(24), 'cart': {}}
        session = self.sessions[sid]
        status = '200 OK'
        extra = []
        path = env.get('PATH_INFO', '/')
        method = env.get('REQUEST_METHOD', 'GET')
        params = {k: v[0] for k, v in parse_qs(env.get('QUERY_STRING', '')).items()}
        home = {'all': '/business', 'business': '/business', 'store': '/store', 'dashboard': '/dashboard'}[self.project]
        try:
            if path == '/':
                status, extra, body = '303 See Other', [('Location', home)], ''
            elif self.project != 'all' and not (path == home or path.startswith(home + '/')):
                status, body = '404 Not Found', self.page('Not found', '<h1>Page not found</h1>', session)
            elif method == 'POST':
                length = int(env.get('CONTENT_LENGTH') or 0)
                if length > 16000 or length < 0:
                    raise ValueError('This submission is too large.')
                form = {k: v[0] for k, v in parse_qs(env['wsgi.input'].read(length).decode('utf-8')).items()}
                if not secrets.compare_digest(form.get('csrf', ''), session['csrf']):
                    status, body = '403 Forbidden', self.page('Expired form', '<h1>Please reload the page and try again.</h1>', session)
                else:
                    location = self.post(path, form, session, sid)
                    status, extra, body = '303 See Other', [('Location', location)], ''
            elif method != 'GET':
                status, body = '405 Method Not Allowed', 'Method not allowed'
                extra.append(('Allow', 'GET, POST'))
            elif path == '/business':
                body = self.business(session, params)
            elif path == '/store':
                body = self.store(session, params)
            elif path == '/store/cart':
                body = self.cart(session, params, sid)
            elif path == '/dashboard':
                body = self.dashboard(session, params)
            else:
                status, body = '404 Not Found', self.page('Not found', '<h1>Page not found</h1><a href="/">Return home</a>', session)
        except (ValueError, UnicodeDecodeError) as error:
            status = '400 Bad Request'
            body = self.page('Check your submission', f'<h1>Check your submission</h1><p>{esc(error)}</p><a class="button" href="{home}">Return to project</a>', session)
        encoded = body.encode('utf-8')
        start_response(status, [('Content-Type', 'text/html; charset=utf-8'), ('Content-Length', str(len(encoded))),
            ('Set-Cookie', f'portfolio={sid}; Path=/; HttpOnly; SameSite=Lax'),
            ('Cache-Control', 'no-store'), ('X-Content-Type-Options', 'nosniff'),
            ('Content-Security-Policy', "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'")] + extra)
        return [encoded]

    def token(self, session):
        return f'<input type="hidden" name="csrf" value="{session["csrf"]}">'

    def page(self, title, content, session, theme='business'):
        brand = {'business': 'Northline<span class="small"> / consulting</span>', 'store': 'Forma<span class="small"> / objects for living</span>', 'dashboard': '◈ Taskboard'}[theme]
        links = {'business': '<a class="navlink" href="#services">Services</a><a class="button" href="#contact">Get in touch ↗</a>',
                 'store': f'<a class="navlink" href="/store">Collection</a><a class="button" href="/store/cart">Bag ({sum(session["cart"].values())})</a>',
                 'dashboard': '<a class="navlink" href="/dashboard">Overview</a><a class="button" href="#new-task">+ New task</a>'}[theme]
        switcher = '<div class="subnav"><a href="/business">01 / Business website</a><a href="/store">02 / Online store</a><a href="/dashboard">03 / Management dashboard</a></div>' if self.project == 'all' else ''
        return f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title><style>{CSS}</style></head><body class="{theme}"><header><nav><a class="brand" href="/{theme}">{brand}</a><span class="badge">Portfolio demo</span>{links}</nav></header><main class="wrap">{switcher}{content}</main><footer>Independent sample project · Python + SQLite · Fictional brands and sample data. Local demonstration; no live payments or email delivery.</footer></body></html>'

    def business(self, session, params):
        notice = '<div class="notice" role="status">Thank you. Your demo enquiry was saved locally. No email was sent.</div>' if params.get('sent') == '1' else ''
        cards = ''.join(f'<article class="card"><span class="eyebrow">0{i}</span><h3>{title}</h3><p>{desc}</p></article>' for i, (title, desc) in enumerate([
            ('Strategy', 'Clear priorities and practical plans for your next stage of growth.'), ('People', 'Thoughtful processes that help teams work better together.'), ('Transformation', 'Turn ambitious ideas into a focused, achievable roadmap.')], 1))
        content = f'''{notice}<section class="hero"><div><span class="eyebrow">Independent thinking. Practical progress.</span><h1>Clarity for your<br>next chapter.</h1><p class="lead">Thoughtful consulting for organisations ready to move forward with purpose.</p><a class="button" href="#contact">Let’s start a conversation ↗</a></div><div class="art" aria-label="Abstract architectural arch"><div class="arch"></div></div></section>
        <section class="section" id="services"><div class="row"><h2>Practical expertise.<br>Lasting impact.</h2><p>Three ways to move your business forward.</p></div><div class="grid">{cards}</div></section>
        <section class="section split" id="contact"><div><span class="eyebrow">A brighter tomorrow starts here</span><h2>Tell us what’s next.</h2><p>Share your goals and the challenge you would like to solve.</p><p class="small">Demo form: entries are stored on this computer. Use fictional contact details.</p></div><form class="card" method="post" action="/business/contact">{self.token(session)}<label class="field">Your name<input name="name" maxlength="100" required autocomplete="name"></label><label class="field">Email address<input name="email" type="email" maxlength="200" required autocomplete="email"></label><label class="field">How can we help?<textarea name="message" minlength="10" maxlength="3000" required></textarea></label><button>Send demo enquiry ↗</button></form></section>'''
        return self.page('Northline | Business website demo', content, session)

    def store(self, session, params):
        query = params.get('q', '').strip()
        cards = ''
        for pid, (name, desc, price, icon) in PRODUCTS.items():
            if query.casefold() not in (name + desc).casefold():
                continue
            cards += f'<article class="card"><div class="product-art" aria-hidden="true">{icon}</div><h3>{name}</h3><p class="small">{desc}</p><p class="price">{money(price)}</p><form method="post" action="/store/add">{self.token(session)}<input type="hidden" name="product" value="{pid}"><button>Add to bag +</button></form></article>'
        notice = '<div class="notice" role="status">Added to your bag. <a href="/store/cart"><u>View bag →</u></a></div>' if params.get('added') else ''
        content = f'''{notice}<section class="hero"><div><span class="eyebrow">Considered design / Everyday living</span><h1>Everyday objects.<br>Thoughtfully chosen.</h1><p class="lead">Quiet forms, honest materials, and useful pieces for the spaces you call home.</p><a href="#collection" class="button">Explore the collection ↓</a></div><div class="art" style="background:linear-gradient(140deg,#eee2cc,#c49b79)"><span style="font:220px Georgia;color:#f7efdc" aria-hidden="true">◒</span></div></section>
        <section id="collection" class="section"><div class="row"><h2>Featured pieces</h2><span class="small">Illustrated products · Demo catalogue</span></div><form class="filters" method="get" action="/store"><label class="field">Search collection<input name="q" value="{esc(query)}" placeholder="Try vase or oak"></label><button>Search</button><a class="button secondary" href="/store#collection">Clear</a></form><div class="grid">{cards or '<p>No products match your search.</p>'}</div></section>'''
        return self.page('Forma | Online store demo', content, session, 'store')

    def cart(self, session, params, sid):
        if params.get('order'):
            with self.db() as con:
                order = con.execute('SELECT * FROM orders WHERE id=? AND session=?', (params['order'], sid)).fetchone()
            if order:
                return self.page('Demo order saved', f'<section class="empty"><span class="eyebrow">Demo checkout complete</span><h1>Thank you.</h1><p>Order #{order["id"]} · {money(order["total"])}</p><p>Your demo order was saved locally. No payment was taken and no goods will ship.</p><a class="button" href="/store">Continue browsing</a></section>', session, 'store')
        rows, total = '', 0
        for pid, qty in session['cart'].items():
            name, _, price, _ = PRODUCTS[pid]
            total += price * qty
            rows += f'<tr><td>{name}</td><td>{money(price)}</td><td><form class="inline" method="post" action="/store/update">{self.token(session)}<input type="hidden" name="product" value="{pid}"><input aria-label="Quantity for {name}" name="quantity" type="number" min="0" max="20" value="{qty}" style="width:75px"><button>Update</button></form></td><td>{money(price * qty)}</td></tr>'
        content = '<h1>Your bag.</h1><p>Set quantity to zero to remove an item.</p>'
        if rows:
            content += f'<div class="card table"><table><thead><tr><th>Product</th><th>Price</th><th>Quantity</th><th>Total</th></tr></thead><tbody>{rows}</tbody></table><div class="row"><h2>Total {money(total)}</h2><form method="post" action="/store/checkout">{self.token(session)}<button>Place demo order →</button></form></div><p class="small">Demo only. No card details, payment, tax calculation, shipping or inventory integration.</p></div>'
        else:
            content += '<div class="card empty"><h2>A little room for something lovely.</h2><p>Your bag is empty.</p><a class="button" href="/store">Browse the collection</a></div>'
        return self.page('Your bag | Forma', content, session, 'store')

    def dashboard(self, session, params):
        query, status = params.get('q', ''), params.get('status', '')
        with self.db() as con:
            all_tasks = con.execute('SELECT * FROM tasks ORDER BY due,id').fetchall()
        tasks = [t for t in all_tasks if query.casefold() in (t['title'] + t['project']).casefold() and (not status or t['status'] == status)]
        done = sum(t['status'] == 'Done' for t in all_tasks)
        overdue = sum(t['status'] != 'Done' and t['due'] < str(dt.date.today()) for t in all_tasks)
        stats = ''.join(f'<div class="stat"><span class="small">{label}</span><strong>{value}</strong></div>' for label, value in [('Total tasks',len(all_tasks)), ('In progress',sum(t['status'] == 'In progress' for t in all_tasks)), ('Completed',done), ('Overdue',overdue)])
        rows = ''
        for t in tasks:
            options = ''.join(f'<option{ " selected" if s == t["status"] else ""}>{s}</option>' for s in ['To do','In progress','Done'])
            rows += f'<tr><td>{esc(t["title"])}</td><td>{esc(t["project"])}</td><td>{esc(t["due"])}</td><td><form class="inline" method="post" action="/dashboard/status">{self.token(session)}<input type="hidden" name="id" value="{t["id"]}"><select name="status" aria-label="Status for {esc(t["title"])}">{options}</select><button>Save</button></form></td><td><form method="post" action="/dashboard/delete">{self.token(session)}<input type="hidden" name="id" value="{t["id"]}"><button class="danger" aria-label="Delete {esc(t["title"])}">Delete</button></form></td></tr>'
        options = '<option value="">All statuses</option>' + ''.join(f'<option{ " selected" if s == status else ""}>{s}</option>' for s in ['To do','In progress','Done'])
        notice = '<div class="notice" role="status">Your changes have been saved.</div>' if params.get('saved') else ''
        percent = round(done / len(all_tasks) * 100) if all_tasks else 0
        content = f'''{notice}<section class="section"><span class="eyebrow">Your workspace / Overview</span><h1>A little clarity.<br>A lot of progress.</h1><p>Plan your work, keep track of the details, and move things forward.</p><div class="stats">{stats}</div><div class="card"><div class="row"><h3>Overall completion</h3><span>{percent}%</span></div><div class="bar" role="progressbar" aria-label="Task completion" aria-valuenow="{percent}" aria-valuemin="0" aria-valuemax="100"><span style="width:{percent}%"></span></div></div></section>
        <section class="section"><div class="row"><h2>Your tasks</h2><span class="small">{len(tasks)} shown</span></div><form class="filters" method="get"><label class="field">Search<input name="q" value="{esc(query)}" placeholder="Task or project name"></label><label class="field">Status<select name="status">{options}</select></label><button>Apply</button><a class="button secondary" href="/dashboard">Clear</a></form><div class="card table"><table><thead><tr><th>Task</th><th>Project</th><th>Due date</th><th>Status</th><th>Action</th></tr></thead><tbody>{rows or '<tr><td colspan="5">No tasks found. Add a task below or clear your filters.</td></tr>'}</tbody></table></div></section>
        <section class="split section" id="new-task"><div><span class="eyebrow">Make space for what’s next</span><h2>Add a new task.</h2><p>Give it a clear name, choose a project, and set a date.</p><p class="small">Shared local demo workspace. Changes persist in SQLite.</p></div><form class="card" method="post" action="/dashboard/create">{self.token(session)}<label class="field">Task title<input name="title" maxlength="150" required></label><label class="field">Project<input name="project" maxlength="80" required></label><label class="field">Due date<input name="due" type="date" required value="{dt.date.today()}"></label><button>Create task +</button></form></section>'''
        return self.page('Taskboard | Management dashboard demo', content, session, 'dashboard')

    def post(self, path, form, session, sid):
        def required(key, limit):
            value = form.get(key, '').strip()
            if not value or len(value) > limit:
                raise ValueError(f'Please provide a valid {key} (maximum {limit} characters).')
            return value
        if path == '/business/contact':
            name, email, message = required('name',100), required('email',200), required('message',3000)
            if '@' not in email or '.' not in email.rsplit('@',1)[-1] or len(message) < 10:
                raise ValueError('Enter a valid email and a message of at least 10 characters.')
            with self.db() as con:
                con.execute('INSERT INTO enquiries(name,email,message,created) VALUES(?,?,?,?)', (name,email,message,dt.datetime.now().isoformat()))
            return '/business?sent=1#contact'
        if path in ['/store/add','/store/update']:
            pid = int(form.get('product', '0'))
            if pid not in PRODUCTS:
                raise ValueError('Unknown product.')
            qty = session['cart'].get(pid,0) + 1 if path.endswith('/add') else int(form.get('quantity','0'))
            if not 0 <= qty <= 20:
                raise ValueError('Quantity must be between 0 and 20.')
            if qty:
                session['cart'][pid] = qty
            else:
                session['cart'].pop(pid,None)
            return '/store?added=1#collection' if path.endswith('/add') else '/store/cart'
        if path == '/store/checkout':
            if not session['cart']:
                raise ValueError('Your bag is empty.')
            total = sum(PRODUCTS[pid][2] * qty for pid,qty in session['cart'].items())
            with self.db() as con:
                order_id = con.execute('INSERT INTO orders(session,total,created) VALUES(?,?,?)', (sid,total,dt.datetime.now().isoformat())).lastrowid
                con.executemany('INSERT INTO order_items VALUES(?,?,?,?)', [(order_id,pid,qty,PRODUCTS[pid][2]) for pid,qty in session['cart'].items()])
            session['cart'].clear()
            return '/store/cart?' + urlencode({'order':order_id})
        if path == '/dashboard/create':
            title, project, due = required('title',150), required('project',80), required('due',10)
            due = str(dt.date.fromisoformat(due))
            with self.db() as con:
                con.execute('INSERT INTO tasks(title,project,status,due) VALUES(?,?,?,?)',(title,project,'To do',due))
            return '/dashboard?saved=1'
        if path in ['/dashboard/status','/dashboard/delete']:
            task_id = int(form.get('id','0'))
            with self.db() as con:
                if not con.execute('SELECT 1 FROM tasks WHERE id=?',(task_id,)).fetchone():
                    raise ValueError('Task not found.')
                if path.endswith('/delete'):
                    con.execute('DELETE FROM tasks WHERE id=?',(task_id,))
                else:
                    status = form.get('status','')
                    if status not in ['To do','In progress','Done']:
                        raise ValueError('Invalid task status.')
                    con.execute('UPDATE tasks SET status=? WHERE id=?',(status,task_id))
            return '/dashboard?saved=1'
        raise ValueError('Unknown form action.')

def main(project='all', port=8000):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=port)
    parser.add_argument('--database', default=None)
    args = parser.parse_args()
    app = Portfolio(args.database, project)
    print(f'Portfolio running at http://127.0.0.1:{args.port} — press Ctrl+C to stop.', flush=True)
    with make_server('127.0.0.1', args.port, app) as server:
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print('\nStopped.')

if __name__ == '__main__':
    main()
