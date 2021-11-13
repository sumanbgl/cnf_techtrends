import sqlite3

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort
import logging
import sys

class Metrics:
    num_db_conns = 0

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    Metrics.num_db_conns += 1
    return connection

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()

    if post:
        app.logger.info('Article %s retrieved', post['title'])

    return post

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
      app.logger.info('Article with post id %s does not exist', post_id)
      return render_template('404.html'), 404
    else:
      return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    app.logger.info('About us page is retrieved')
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()
            app.logger.info('New article with title %s created', title)
            return redirect(url_for('index'))

    return render_template('create.html')

# Define /healthz end point
@app.route('/healthz')
def healthcheck():
    response = app.response_class(
        response=json.dumps({"result":"OK - healthy"}),
        status=200,
        mimetype='application/json'
    )
    return response

# Define /metrics end point
@app.route('/metrics')
def metrics():    
    num_posts = get_post_count()
    response = app.response_class(
        response=json.dumps({"db_connection_count": Metrics.num_db_conns, "post_count":num_posts}),
        status=200,
        mimetype='application/json'
    )
    return response

def get_post_count():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return len(posts)    

# start the application on port 3111
if __name__ == "__main__":
    # streams logs to stdout and stderr
   stdout_handler = logging.StreamHandler(sys.stdout)
   stderr_handler = logging.StreamHandler(sys.stderr)
   handlers = [stdout_handler, stderr_handler]

   logging.basicConfig(level = logging.DEBUG,
                       format='[%(asctime)s %(levelname)s - %(message)s]',
                       handlers=handlers 
                       )
   app.run(host='0.0.0.0', port='3111')
