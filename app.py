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
from uuid import uuid4
from werkzeug.exceptions import NotFound
from functools import wraps
import yaml
from bcrypt import checkpw
import os

app = Flask(__name__)
app.secret_key = 'secret1'

def get_data_path():
    if app.config['TESTING']:
        return os.path.join(os.path.dirname(__file__), 'tests', 'data')
    else:
        return os.path.join(os.path.dirname(__file__), 'cms', 'data')
    
def load_user_credentials():
    filename = 'users.yml'
    root_dir = os.path.dirname(__file__)
    if app.config['TESTING']:
        credentials_path = os.path.join(root_dir, 'tests', filename)
    else:
        credentials_path = os.path.join(root_dir, "cms", filename)
    
    with open(credentials_path, 'r') as file:
        return yaml.safe_load(file)

def valid_credentials(username, password):
    credentials = load_user_credentials()

    if username in credentials:
        stored_password = credentials[username].encode('utf-8')
        return checkpw(password.encode('utf-8'), stored_password)
    else:
        return False

def validate_file_extension(filename):
    return filename.endswith('.txt') or filename.endswith('.md')

def determine_duped_filename(filename):
    # Split into base and extension
    name, ext = os.path.splitext(filename)
    
    # Try to split at the last underscore
    parts = name.rsplit('_', 1)
    print(parts)
    
    if len(parts) == 2 and parts[1].isdigit():
        # Increment number
        number = int(parts[1]) + 1
        name = parts[0]
    else:
        # Start from 1
        number = 1
    
    # Assemble new name
    return f"{name}_{number}{ext}"

'''For finding user IF storing users as dictionaries in the session   
def find_user(name, users):
    return next((user for user in users if user['username'] == name), None)
'''

def user_signed_in():
    return 'username' in session

def require_signed_in_user(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not user_signed_in():
            flash("You must be signed in to do that.")
            return redirect(url_for('show_signin_form'))
        
        return f(*args, **kwargs)
    
    return decorated_function

@app.before_request
def get_data_directory():
    g.data_dir = get_data_path()

@app.route('/')
def index():
    files = [os.path.basename(path) for path in os.listdir(g.data_dir)]
    '''
    user = find_user('admin', session['users'])
    if user:
        user_logged_in = user['logged_in']
    else:
        user_logged_in = False
    
    username = user['username'] if user else ''
    '''
    return render_template('index.html', files=files)

@app.route('/signup')
def signup():
    return render_template('sign_up.html')

@app.route('/<filename>')
def download_document(filename):
    file_path = os.path.join(g.data_dir, filename)

    if os.path.isfile(file_path):
        if filename.endswith('.md'):
            with open(file_path, 'r') as file:
                content = file.read()
            return render_template("markdown.html",
                                    content=markdown(content))
        else:
            return send_from_directory(g.data_dir, filename)
    
    else:
        flash(f"{filename} not found", "error")
        return redirect(url_for('index'))

@app.route('/<filename>/edit')
@require_signed_in_user
def edit_document(filename):
    file_path = os.path.join(g.data_dir, filename)

    if os.path.isfile(file_path):
        with open(file_path, 'r') as file:
            content = file.read()
        return render_template('edit.html', filename=filename, content=content)
    else:
        flash(f"{filename} not found")
        return redirect(url_for('index'))

@app.route('/<filename>', methods=['POST'])
@require_signed_in_user
def save_changes(filename):
    changes = request.form["content"]
    file_path = os.path.join(g.data_dir, filename)
    with open(file_path, 'w') as file:
        file.write(changes)

    flash(f"{filename} has been updated!", "success")
    return redirect(url_for('index'))

@app.route('/duplicate/<filename>', methods=['POST'])
@require_signed_in_user
def duplicate_document(filename):
    duped_filename = determine_duped_filename(filename)
    original_file_path = os.path.join(g.data_dir, filename)

    with open(original_file_path, 'r') as file:
        contents = file.read()

    with open(os.path.join(g.data_dir, duped_filename), 'w') as new_file:
        new_file.write(contents)
    
    flash("File successfully duplicated.")
    return redirect(url_for('index'))

@app.route('/new')
@require_signed_in_user
def new_document():
    return render_template("new.html")

@app.route('/create', methods=['POST'])
@require_signed_in_user
def create_new_document():
    filename = request.form['filename'].strip()
    file_validated = validate_file_extension(filename.casefold())
    file_path = os.path.join(g.data_dir, filename)

    if len(filename) == 0:
        flash("A name is required.")
        return render_template("new.html"), 422
    elif os.path.exists(file_path):
        flash(f"{filename} already exists.")
        return render_template("new.html"), 422
    else:
        if not file_validated:
            flash("That file extension is not supported.")
            return render_template("new.html"), 422
            
        with open(file_path, 'w') as file:
            file.write("")
        flash(f"{filename} has been created.")
        return redirect(url_for('index'))

@app.route('/delete/<filename>', methods=['POST'])
@require_signed_in_user
def delete_document(filename):
    file_path = os.path.join(g.data_dir, filename)
    os.remove(file_path)
    flash(f"{filename} has been deleted!", "success")
    return redirect(url_for('index'))

@app.route('/users/signin')
def show_signin_form():
    return render_template('sign_in.html')

@app.route('/users/signin', methods=['POST'])
def signin():
    username = request.form["username"]
    password = request.form["password"]
    credentials = load_user_credentials()

    if valid_credentials(username, password):
        session['username'] = username
        flash("Welcome!")
        return redirect(url_for('index'))
    else:
        flash("Invalid credentials")
        return render_template('sign_in.html'), 422

@app.route('/users/signout', methods=['POST'])
def signout():
    session.pop('username', None)
    flash(f"You have been signed out.")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5003)