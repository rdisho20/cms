from flask import (
    flash,
    Flask,
    g,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)

from markdown import markdown
from werkzeug.exceptions import NotFound
import os

app = Flask(__name__)
app.secret_key = 'secret1'

@app.before_request
def get_data_directory():
    g.root = os.path.abspath(os.path.dirname(__file__))
    g.data_dir = os.path.join(g.root, "cms", "data")

@app.route('/')
def index():
    # files = os.listdir(data_dir)
    files = [os.path.basename(path) for path in os.listdir(g.data_dir)]
    return render_template('data.html', files=files)

@app.route('/<filename>')
def download_file(filename):
    file_path = os.path.join(g.data_dir, filename)

    if os.path.isfile(file_path):
        if filename.endswith('.md'):
            with open(file_path, 'r') as file:
                return markdown(file.read())
        else:
            return send_from_directory(g.data_dir, filename)
    
    else:
        flash(f"{filename} not found", "error")
        return redirect(url_for('index'))

@app.route('/<filename>/edit')
def edit_file(filename):
    file_path = os.path.join(g.data_dir, filename)

    if os.path.isfile(file_path):
        with open(file_path, 'r') as file:
            content = file.read()
        return render_template('edit.html', filename=filename, content=content)
    else:
        flash(f"{filename} not found")
        return redirect(url_for('index'))

@app.route('/<filename>', methods=['POST'])
def save_changes(filename):
    changes = request.form["content"]
    file_path = os.path.join(g.data_dir, filename)
    with open(file_path, 'w') as file:
        file.write(changes)

    flash(f"{filename.upper()} has been updated!", "success")
    return redirect(url_for('index'))

'''
@app.errorhandler(404)
def file_not_found(error):
    session.modified = True
    return redirect(url_for('index'), 302)
'''

if __name__ == '__main__':
    app.run(debug=True, port=5003)