import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response
from uuser import *
from flask_login import current_user

global username
global password

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
DATABASEURI = "postgresql://ps3142:spyyzh@35.231.103.173/proj1part2"
engine = create_engine(DATABASEURI)


engine.execute("""CREATE TABLE IF NOT EXISTS test (
  id serial,
  name text
);""")
engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")


@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request.

  The variable g is globally accessible.
  """
  try:
    g.conn = engine.connect()
  except:
    print("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

    

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't, the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass



# If you wanted the user to go to, for example, localhost:8111/foobar/ with POST or GET then you could use:
#       @app.route("/foobar/", methods=["POST", "GET"])
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
@app.route('/index')
def index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments, e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """

  # DEBUG: this is debugging code to see what request looks like
  print(request.args)


  #
  # example of a database query
  #
  cursor = g.conn.execute("SELECT name FROM products")
  names = []
  for result in cursor:
    names.append(result['name'])  # can also be accessed using result[0]
  cursor.close()
  context = dict(data = names)

  #
  # Flask uses Jinja templates, which is an extension to HTML where you can
  # pass data to a template and dynamically generate HTML based on the data
  # (you can think of it as simple PHP)
  # documentation: https://realpython.com/blog/python/primer-on-jinja-templating/
  #
  # You can see an example template in templates/index.html
  #
  # context are the variables that are passed to the template.
  # for example, "data" key in the context variable defined below will be 
  # accessible as a variable in index.html:
  #
  #     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
  #     <div>{{data}}</div>
  #     
  #     # creates a <div> tag for each element in data
  #     # will print: 
  #     #
  #     #   <div>grace hopper</div>
  #     #   <div>alan turing</div>
  #     #   <div>ada lovelace</div>
  #     #
  #     {% for n in data %}
  #     <div>{{n}}</div>
  #     {% endfor %}
  #
  


  #
  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html
  #
  return render_template("index.html", **context)

@app.route('/another')
def another():
  return render_template("another.html")

@app.route('/add', methods=['POST'])
def add():
  name = request.form['name']
  g.conn.execute('INSERT INTO test(name) VALUES (%s)', name)
  return redirect('/')

@app.route('/', methods=['GET','POST'])
def login():
  global password
  global username
  if request.method == 'GET':
        return render_template('login.html')
  else:
    username=request.form.get('username')
    password=request.form.get('password')
    g.user=username
    g.password=password
    cursor = g.conn.execute("SELECT Customer_ID,password FROM Customers;")
    user_info = list()
    for result in cursor:
      user_info.append([result[0],result[1]])
    cursor.close()

    if password == '123456' and 'c' in username: #有点问题
      return redirect('/user')
    elif password == '123456' and 's' in username:
      return redirect('/seller')
    else:
      return username+password+user_info[0][0]+user_info[0][1]+'密码错误'

@app.route('/user')
def user():
  global password
  global username
  username_m='\''+username+'\''
  cursor = g.conn.execute("SELECT * FROM orders where customer_id="+username_m+';')
  orders = []
  for result in cursor:
    orders.append([result['order_id'],result['product_id'],result['quantity'],result['price']])  # 
  cursor.close()
  context = dict(data = orders)
  return render_template("user.html", **context)

@app.route('/product')
def product():
  return render_template("index.html", **context)

@app.route('/order')
def order():
  return render_template("index.html", **context)


@app.route('/seller')
def seller():
  global password
  global username
  username_m='\''+username+'\''
  cursor = g.conn.execute("SELECT * FROM seller_productslist where seller_id="+username_m+';')
  seller_productslist = []
  for result in cursor:
    seller_productslist.append(result['product_id'])  #
  cursor.close()
  context = dict(data = seller_productslist)
  return render_template("seller.html", **context)
  

@app.route('/seller/add')
def seller_add():
  return render_template("index.html", **context)

@app.route('/advertisement')
def advertisement():
  return render_template("index.html", **context)

if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8113, type=int)
  
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using:

        python server.py

    Show the help text using:

        python server.py --help

    """

    HOST, PORT = host, port
    print("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

  run()
