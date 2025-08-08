import unittest
from app import app

class CMSTest(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_index(self):
        # returning response object (html) so don't need 'with'
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, "text/html; charset=utf-8")
        self.assertIn("about.txt", response.get_data(as_text=True))
        self.assertIn("changes.txt", response.get_data(as_text=True))
        self.assertIn("history.txt", response.get_data(as_text=True))

    def test_viewing_text_document(self):
        with self.client.get("/about.txt") as response:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content_type, "text/plain; charset=utf-8")
            self.assertIn("This is my app.", response.get_data(as_text=True))

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
        # returning response object (html) so don't need 'with'
        response = self.client.get("/python_is.md")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, "text/html; charset=utf-8")
        self.assertIn("<h1>Python is...</h1>",
                        response.get_data(as_text=True))
