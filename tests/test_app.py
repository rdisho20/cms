import unittest
from app import app

class CMSTest(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_index(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("about.txt", response.get_data(as_text=True))
        self.assertIn("changes.txt", response.get_data(as_text=True))
        self.assertIn("history.txt", response.get_data(as_text=True))

    def test_download_file(self):
        response = self.client.get("/about.txt")
        self.assertEqual(response.status_code, 200)
        self.assertIn("This is my app.", response.get_data(as_text=True))

    def test_file_nonexistent(self):
        with self.client.get("/test.txt") as response:
            self.assertEqual(response.status_code, 302)

        with self.client.get(response.headers['Location']) as response:
            self.assertEqual(response.status_code, 200)
            self.assertIn("text.txt does not exist",
                          response.get_data(as_text=True))
        
        with self.client.get("/") as response:
            self.assertNotIn("text.txt does not exist",
                             response.get_data(as_text=True))