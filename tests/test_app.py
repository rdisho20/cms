import unittest
import shutil
import os
from app import app

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
        self.create_document("changes.txt")

        response = self.client.get("/changes.txt/edit")
        self.assertEqual(response.status_code, 200)
        self.assertIn("<textarea", response.get_data(as_text=True))
        self.assertIn('<button type="submit"', response.get_data(as_text=True))
    
    def test_updating_document(self):
        # Set up: Ensure the file exists before we try to update it.
        self.create_document("changes.txt")

        # Execute POST Request
        with (self.client.post('/changes.txt',
                             data={'content': 'Make changes test!'})
                             as response):
            self.assertEqual(response.status_code, 302)
        
        # Execute GET Request to test the flash message
        with self.client.get(response.headers['Location']) as response:
            self.assertEqual(response.status_code, 200)
            self.assertIn("CHANGES.TXT has been updated!", response.get_data(as_text=True))
        
        # Execute GET Request to test the file changes
        with self.client.get('/changes.txt') as response:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content_type, "text/plain; charset=utf-8")
            self.assertIn("Make changes test!", response.get_data(as_text=True))

    
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



