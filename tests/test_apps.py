import io
import re
import sys
import tempfile
import uuid
import unittest
from pathlib import Path
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import Portfolio


class Browser:
    def __init__(self, app):
        self.app = app
        self.cookie = ''
        self.csrf = ''

    def request(self, path, form=None, token=True):
        route, _, query = path.partition('?')
        if form is not None:
            form = dict(form)
            if token:
                form['csrf'] = self.csrf
        data = urlencode(form or {}).encode()
        env = {'PATH_INFO': route, 'QUERY_STRING': query,
               'REQUEST_METHOD': 'POST' if form is not None else 'GET',
               'CONTENT_LENGTH': str(len(data)), 'wsgi.input': io.BytesIO(data),
               'HTTP_COOKIE': self.cookie}
        result = {}
        def respond(status, headers):
            result.update(status=status, headers=dict(headers))
        result['body'] = b''.join(self.app(env, respond)).decode()
        self.cookie = result['headers']['Set-Cookie'].split(';')[0]
        match = re.search('name="csrf" value="([^"]+)"', result['body'])
        if match:
            self.csrf = match[1]
        return result


class PortfolioTests(unittest.TestCase):
    def setUp(self):
        self.database = Path(tempfile.gettempdir()) / ('portfolio-test-' + uuid.uuid4().hex + '.db')
        self.app = Portfolio(self.database)
        self.browser = Browser(self.app)
        self.browser.request('/business')

    def tearDown(self):
        self.database.unlink(missing_ok=True)

    def test_pages_and_not_found(self):
        for page in ['/business', '/store', '/store/cart', '/dashboard']:
            self.assertEqual(self.browser.request(page)['status'], '200 OK')
        self.assertEqual(self.browser.request('/missing')['status'], '404 Not Found')

    def test_contact_persists_and_validates(self):
        form = {'name':'Demo Visitor','email':'demo@example.com','message':'Please discuss this sample project.'}
        self.assertEqual(self.browser.request('/business/contact', form)['status'], '303 See Other')
        with self.app.db() as con:
            self.assertEqual(con.execute('SELECT count(*) FROM enquiries').fetchone()[0],1)
        form['email'] = 'invalid'
        self.assertEqual(self.browser.request('/business/contact', form)['status'], '400 Bad Request')

    def test_csrf_blocks_mutation(self):
        self.assertEqual(self.browser.request('/dashboard/create', {'title':'Bad'}, token=False)['status'], '403 Forbidden')
        with self.app.db() as con:
            self.assertEqual(con.execute('SELECT count(*) FROM tasks').fetchone()[0],4)

    def test_cart_checkout_totals_and_isolation(self):
        self.browser.request('/store/add', {'product':1})
        self.browser.request('/store/update', {'product':1,'quantity':2})
        self.browser.request('/store/add', {'product':2})
        self.assertIn('$361.00',self.browser.request('/store/cart')['body'])
        other = Browser(self.app)
        self.assertIn('Your bag is empty',other.request('/store/cart')['body'])
        checkout = self.browser.request('/store/checkout', {})
        with self.app.db() as con:
            self.assertEqual(con.execute('SELECT total FROM orders').fetchone()[0],36100)
            self.assertEqual(con.execute('SELECT sum(quantity) FROM order_items').fetchone()[0],3)
        self.assertIn('No payment was taken',self.browser.request(checkout['headers']['Location'])['body'])
        self.assertNotIn('No payment was taken',other.request(checkout['headers']['Location'])['body'])
        self.assertEqual(self.browser.request('/store/checkout', {})['status'],'400 Bad Request')

    def test_cart_validation_removal_and_search(self):
        self.assertEqual(self.browser.request('/store/add', {'product':999})['status'],'400 Bad Request')
        self.assertEqual(self.browser.request('/store/update', {'product':1,'quantity':-1})['status'],'400 Bad Request')
        self.assertEqual(self.browser.request('/store/update', {'product':1,'quantity':21})['status'],'400 Bad Request')
        self.browser.request('/store/add', {'product':1})
        self.browser.request('/store/update', {'product':1,'quantity':0})
        self.assertIn('Your bag is empty',self.browser.request('/store/cart')['body'])
        search = self.browser.request('/store?q=oak')['body']
        self.assertIn('Linea serving tray',search)
        self.assertNotIn('Riva ceramic vase',search)

    def test_task_lifecycle_escaping_and_persistence(self):
        result = self.browser.request('/dashboard/create', {'title':'<script>alert(1)</script>','project':'Demo','due':'2030-01-02'})
        self.assertEqual(result['status'],'303 See Other')
        page = self.browser.request('/dashboard?q=alert')['body']
        self.assertIn('&lt;script&gt;',page)
        self.assertNotIn('<script>',page)
        with self.app.db() as con:
            task_id = con.execute('SELECT max(id) FROM tasks').fetchone()[0]
        self.browser.request('/dashboard/status', {'id':task_id,'status':'Done'})
        restored = Portfolio(self.database)
        with restored.db() as con:
            self.assertEqual(con.execute('SELECT status FROM tasks WHERE id=?',(task_id,)).fetchone()[0],'Done')
        self.browser.request('/dashboard/delete', {'id':task_id})
        with self.app.db() as con:
            self.assertEqual(con.execute('SELECT count(*) FROM tasks').fetchone()[0],4)

    def test_invalid_task_inputs(self):
        self.assertEqual(self.browser.request('/dashboard/create', {'title':'Task','project':'Demo','due':'bad'})['status'],'400 Bad Request')
        self.assertEqual(self.browser.request('/dashboard/status', {'id':1,'status':'Unknown'})['status'],'400 Bad Request')
        self.assertEqual(self.browser.request('/dashboard/delete', {'id':999})['status'],'400 Bad Request')

    def test_individual_project_isolation(self):
        browser = Browser(Portfolio(self.database,'store'))
        self.assertEqual(browser.request('/')['headers']['Location'],'/store')
        self.assertEqual(browser.request('/dashboard')['status'],'404 Not Found')
        self.assertEqual(browser.request('/business/contact', {})['status'],'404 Not Found')

    def test_empty_dashboard_is_not_reseeded(self):
        with self.app.db() as con:
            con.execute('DELETE FROM tasks')
        restored = Portfolio(self.database)
        browser = Browser(restored)
        self.assertIn('No tasks found',browser.request('/dashboard')['body'])
        with restored.db() as con:
            self.assertEqual(con.execute('SELECT count(*) FROM tasks').fetchone()[0],0)

if __name__ == '__main__':
    unittest.main()
