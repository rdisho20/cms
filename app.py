from flask import g, Flask, render_template, request, send_from_directory
import os

app = Flask(__name__)

@app.before_request
def get_data_directory():
    g.root = os.path.abspath(os.path.dirname(__file__))
    g.data_dir = os.path.join(g.root, "cms", "data")

@app.route('/')
def index():
    # files = os.listdir(data_dir)
    files = [os.path.basename(path) for path in os.listdir(g.data_dir)]
    return render_template('data.html', files=files)

@app.route('/<file>')
def download_file(file):
    return send_from_directory(g.data_dir, file)

if __name__ == '__main__':
    app.run(debug=True, port=5003)