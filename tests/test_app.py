import unittest
import shutil
from flask import session
import os
from app import app
import yaml

class CMSTest(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        self.data_path = os.path.join(os.path.dirname(__file__), 'data')
        os.makedirs(self.data_path, exist_ok=True)
    
    def tearDown(self):
        shutil.rmtree(self.data_path, ignore_errors=True)
    
    def create_document(self, name, content=""):
        with open(os.path.join(self.data_path, name), 'w') as file:
            file.write(content)
    
    def admin_session(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess['username'] = 'admin'
            return c

    def test_index(self):
        self.create_document("about.txt")
        self.create_document("changes.txt")

        # returning response object (html) so don't need 'with'
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, "text/html; charset=utf-8")
        self.assertIn("about.txt", response.get_data(as_text=True))
        self.assertIn("changes.txt", response.get_data(as_text=True))

    def test_viewing_text_document(self):
        self.create_document("history.txt",
                             "Python 0.9.0 (initial release) is released.")

        with self.client.get("/history.txt") as response:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content_type, "text/plain; charset=utf-8")
            self.assertIn("Python 0.9.0 (initial release) is released.",
                          response.get_data(as_text=True))

    def test_document_not_found(self):
        # Attempt to access a nonexistent file and verify a redirect happens
        with self.client.get("/test.txt") as response:
            self.assertEqual(response.status_code, 302)

        # Verify redirect and message handling works
        with self.client.get(response.headers['Location']) as response:
            self.assertEqual(response.status_code, 200)
            self.assertIn("test.txt not found",
                          response.get_data(as_text=True))
        
        # Assert that a page reload removes the message
        with self.client.get("/") as response:
            self.assertNotIn("test.txt not found",
                             response.get_data(as_text=True))

    def test_markdown_file(self):
        self.create_document("python_is.md", "# Python is...")

        # returning response object (html) so don't need 'with'
        response = self.client.get("/python_is.md")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, "text/html; charset=utf-8")
        self.assertIn("<h1>Python is...</h1>",
                        response.get_data(as_text=True))

    def test_editing_document(self):
        client = self.admin_session()
        self.create_document("changes.txt")

        response = client.get("/changes.txt/edit")
        self.assertEqual(response.status_code, 200)
        self.assertIn("<textarea", response.get_data(as_text=True))
        self.assertIn('<button type="submit"', response.get_data(as_text=True))
    
    def test_editing_document_signed_out(self):
        self.create_document("changes.txt")

        response = self.client.get("/changes.txt/edit")
        self.assertEqual(response.status_code, 302)
        follow_response = self.client.get(response.headers['Location'])
        self.assertIn("You must be signed in to do that.",
                      follow_response.get_data(as_text=True))
    
    def test_updating_document(self):
        # Set up: Ensure the file exists before we try to update it.
        self.create_document("changes.txt")
        client = self.admin_session()

        # Execute POST Request
        with (client.post('/changes.txt',
                             data={'content': 'Make changes test!'})
                             as response):
            self.assertEqual(response.status_code, 302)
        
        # Execute GET Request to test the flash message
        with client.get(response.headers['Location']) as response:
            self.assertEqual(response.status_code, 200)
            self.assertIn("changes.txt has been updated!", response.get_data(as_text=True))
        
        # Execute GET Request to test the file changes
        with client.get('/changes.txt') as response:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content_type, "text/plain; charset=utf-8")
            self.assertIn("Make changes test!", response.get_data(as_text=True))
    
    def test_updating_document_signed_out(self):
        self.create_document("changes.txt")

        with (self.client.post('/changes.txt',
                             data={'content': 'Make changes test!'})
                             as response):
            self.assertEqual(response.status_code, 302)

        with self.client.get(response.headers['Location']) as response:
            self.assertEqual(response.status_code, 200)
            self.assertIn("You must be signed in to do that.",
                          response.get_data(as_text=True))
    
    def test_viewing_new_document_page(self):
        client = self.admin_session()
        response = client.get("/new")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, "text/html; charset=utf-8")
        self.assertIn("<input", response.get_data(as_text=True))
        self.assertIn('<button type="submit"', response.get_data(as_text=True))

    def test_viewing_new_document_page_signed_out(self):
        response = self.client.get("/new")
        self.assertEqual(response.status_code, 302)
        follow_response = self.client.get(response.headers['Location'])
        self.assertIn("You must be signed in to do that.",
                      follow_response.get_data(as_text=True))
    
    def test_creating_new_document(self):
        client = self.admin_session()
        # Execute POST request to create new file, follow redirects to check flash mssg
        response = client.post('/create',
                                    data={'filename': 'test.txt'},
                                    follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("test.txt has been created.",
                      response.get_data(as_text=True))
        
        # Execute GET to see if new file appears on index page
        response = client.get('/')
        self.assertIn('test.txt', response.get_data(as_text=True))
        
        # Execute POST request to create new file w/ 'test.txt' file (already exists)
        with client.post('/create', data={'filename': 'test.txt'}) as response:
            self.assertEqual(response.status_code, 422)
            self.assertIn("test.txt already exists.",
                          response.get_data(as_text=True))
    
    def test_creating_new_document_without_filename(self):
        client = self.admin_session()
        response = client.post('/create', data={'filename': ''})
        self.assertEqual(response.status_code, 422)
        self.assertIn("A name is required.", response.get_data(as_text=True))
    
    def test_creating_new_document_with_unsupported_filetype(self):
        client = self.admin_session()
        response = client.post('/create', data={'filename': 'test.mpg'})
        self.assertEqual(response.status_code, 422)
        self.assertIn("That file extension is not supported.",
                      response.get_data(as_text=True))
    
    def test_creating_new_document_signed_out(self):
        response = self.client.post('/create',
                                    data={'filename': 'test.txt'})
        self.assertEqual(response.status_code, 302)
        follow_response = self.client.get(response.headers['Location'])
        self.assertIn("You must be signed in to do that.",
                      follow_response.get_data(as_text=True))
    
    def test_deleting_document(self):
        client = self.admin_session()
        self.create_document("test.txt")

        response = client.post('/delete/test.txt', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("test.txt has been deleted!",
                      response.get_data(as_text=True))
        
        response = client.get('/')
        self.assertNotIn("test.txt", response.get_data(as_text=True))
    
    def test_deleting_document_signed_out(self):
        self.create_document("test.txt")

        response = self.client.post('/delete/test.txt')
        self.assertEqual(response.status_code, 302)
        follow_response = self.client.get(response.headers['Location'])
        self.assertIn("You must be signed in to do that.",
                      follow_response.get_data(as_text=True))
    
    def test_sign_in_page(self):
        response = self.client.get('/users/signin')
        self.assertIn("Username:", response.get_data(as_text=True))
        self.assertIn('<button type="submit', response.get_data(as_text=True))
    
    def test_sign_in_invalid_credentials(self):
        response = self.client.post('/users/signin',
                                    data={
                                        'username': 'yoyo',
                                        'password': '1234',
                                    },
                                    follow_redirects=True)
        self.assertEqual(response.status_code, 422)
        self.assertIn("Invalid credentials", response.get_data(as_text=True))

    def test_sign_in_admin_then_sign_out_admin(self):
        response = self.client.post('/users/signin',
                                    data={
                                        'username': 'admin',
                                        'password': 'secret',
                                    },
                                    follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Welcome!", response.get_data(as_text=True))
        self.assertIn("Signed in as admin.", response.get_data(as_text=True))

        response = self.client.post('/users/signout', follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("You have been signed out.",
                      response.get_data(as_text=True))
        self.assertIn("Sign In", response.get_data(as_text=True))

    def test_require_sign_in(self):
        response = self.client.post('/delete/history.txt', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("You must be signed in to do that.",
                      response.get_data(as_text=True))

        

'''LS test
    def test_updating_document(self):
        response = self.client.post("/changes.txt",
                                    data={'content': "new content"})
        self.assertEqual(response.status_code, 302)

        follow_response = self.client.get(response.headers['Location'])
        self.assertIn("changes.txt has been updated",
                      follow_response.get_data(as_text=True))

        with self.client.get("/changes.txt") as content_response:
            self.assertEqual(content_response.status_code, 200)
            self.assertIn("new content",
                          content_response.get_data(as_text=True))
'''



