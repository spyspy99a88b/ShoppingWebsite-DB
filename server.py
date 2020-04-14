import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response
from uuser import *
from flask_login import current_user

global username
global password

username='c0001' #调试用

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


@app.route('/', methods=['GET','POST'])
def homepage():
  cursor2 = g.conn.execute("""WITH seller_likes_count AS 
  (SELECT s.seller_id, s.name, s.industry, sp.product_id, likes_num.count 
  from sellers s LEFT OUTER JOIN seller_productslist sp ON s.seller_id = sp.seller_id 
  LEFT OUTER JOIN (SELECT product_id, COUNT(product_id) FROM likes_or_not WHERE product_id in 
  (SELECT product_id FROM Likes_or_not WHERE NOW()-timestamp::timestamp < '1 year'::interval) 
  GROUP BY product_id) likes_num ON sp.product_id = likes_num.product_id 
  GROUP BY s.seller_id, sp.product_id, likes_num.count ORDER BY s.name) 
  SELECT seller_id, name,industry, sum(count) 
  FROM seller_likes_count 
  GROUP BY seller_id,name,industry 
  Having sum(count)>0
  ORDER BY sum(count) DESC;""")
  ranks = []
  for result in cursor2:
    ranks.append([result['seller_id'],result['name'],result['industry'],result['sum']])  #
  cursor2.close()

  cursor1 = g.conn.execute("""SELECT o.product_id,p.name,avg(r.star_ratings)
  FROM Orders o LEFT JOIN Reviews r on o.order_id=r.order_id
  RIGHT JOIN products p ON p.product_id=o.product_id
  WHERE p.product_id in (SELECT product_id
  FROM Likes_or_not
  WHERE NOW()-timestamp::timestamp < '6 months'::interval)
  GROUP BY o. product_id,p.name
  HAVING AVG(r.star_ratings)>=4.5;""")
  good_product = []
  try:
    for result in cursor1:
      good_product.append([result[0],result[1],result[2]])
  except:
      good_product.append(['no good products','no good products','no good products'])
  cursor1.close()
  context = dict(data2 = ranks,data1=good_product)

  return render_template("homepage.html", **context)

@app.route('/login', methods=['GET','POST'])
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

    if [username,password] == user_info or ('c' in username and password == '123456'):
      return redirect('/user')
    elif [username,password] in user_info or ('s' in username and password == '123456'):
      return redirect('/seller')
    else:
      return redirect('/login/error')

@app.route('/login/error', methods=['GET','POST'])
def login_error():
  return render_template("login_error.html")

@app.route('/logout', methods=['GET','POST'])
def logout():
  global password
  global username
  username = None
  password = None
  return render_template("logout.html")
  


@app.route('/user',methods=['GET','POST'])
def user():
  global password
  global username
  if request.method == 'POST':
    s_i=request.form.get('search')
    s_i=str(s_i)
    line="SELECT product_id,name,categories,price FROM products where name like '{s}';".format(s=s_i)
    cursor3 = g.conn.execute(line)
    pp = []
    try:
      for result in cursor3:
        pp.append([result['product_id'],result['name'],result['categories'],result['price']]) #id name category price
    except:
      pp=['no result','no result','no result','no result']
    cursor3.close()  
    context=dict(data=pp) 
    return render_template("search.html", **context)

  username_m='\''+username+'\''
  cursor = g.conn.execute("SELECT * FROM orders where customer_id="+username_m+';')
  orders = []
  for result in cursor:
    orders.append([result['order_id'],result['product_id'],result['quantity'],result['price']])  # 
  cursor.close()

  cursor2 = g.conn.execute("""WITH seller_likes_count AS 
  (SELECT s.seller_id, s.name, s.industry, sp.product_id, likes_num.count 
  from sellers s LEFT OUTER JOIN seller_productslist sp ON s.seller_id = sp.seller_id 
  LEFT OUTER JOIN (SELECT product_id, COUNT(product_id) FROM likes_or_not WHERE product_id in 
  (SELECT product_id FROM Likes_or_not WHERE NOW()-timestamp::timestamp < '1 year'::interval) 
  GROUP BY product_id) likes_num ON sp.product_id = likes_num.product_id 
  GROUP BY s.seller_id, sp.product_id, likes_num.count ORDER BY s.name) 
  SELECT seller_id, name,industry, sum(count) 
  FROM seller_likes_count 
  GROUP BY seller_id,name,industry 
  Having sum(count)>0
  ORDER BY sum(count) DESC;""")
  ranks = []
  for result in cursor2:
    ranks.append([result['seller_id'],result['name'],result['industry'],result['sum']])  #
  cursor2.close()
  context = dict(data1 = orders, data2 = ranks)
  return render_template("user.html", **context)

@app.route('/product')
def product():
  return render_template("product.html", **context)


@app.route('/order')
def order():
  global password
  global username
  username_m = '\'' + username + '\''
  cursor = g.conn.execute(
    """SELECT p.product_id, p.name, p.categories, p.keys, p.picture, p.price, p.is_selling, r.star_ratings, r.text, r.reviewed_or_not 
    FROM Products p JOIN orders o on o.product_id=p.product_id JOIN reviews r on r.order_id = o.order_id 
    where o.customer_id=""" + username_m + ';')
  order = []
  for result in cursor:
    order.append([result[0], result[1], result[2], result[3], result[4], result[5], result[6], result[7], result[8], result[9]])
  cursor.close()
  context = dict(data=order)
  return render_template("order.html", **context)


@app.route('/review')
def review():
  return render_template("review.html")


@app.route('/seller')
def seller():
  global password
  global username
  username_m='\''+username+'\''
  cursor = g.conn.execute("""SELECT sp.product_id, p.name, p.categories, p.keys, p.price, p.is_selling 
  FROM seller_productslist sp Join products p on sp.product_id=p.product_id 
  where sp.seller_id="""+username_m+';')
  seller_productslist = []
  for result in cursor:
    seller_productslist.append([result['product_id'],result['name'],result['categories'],result['keys'],result['price'],result['is_selling']])  #
  cursor.close()

  cursor2 = g.conn.execute("SELECT * FROM Advertisement where seller_id=" + username_m + ';')
  seller_ad = []
  for result in cursor2:
    seller_ad.append([result['advertisement_id'],result['product_id'],result['price']])  #
  cursor2.close()
  context = dict(data = seller_productslist,data2=seller_ad)
  return render_template("seller.html", **context)
  

# @app.route('/seller/add') #舍弃
# def seller_add():
#   global password
#   global username
#   username_m = '\'' + username + '\''
#   cursor = g.conn.execute("SELECT * FROM Advertisement where seller_id=" + username_m + ';')
#   seller_ad = []
#   for result in cursor:
#     seller_ad.append([result['advertisement_id'],result['product_id'],result['price']])  #
#   cursor.close()
#   context = dict(data=seller_ad)
#   return render_template("seller_add.html", **context)

@app.route('/advertisement',methods=['GET','POST'])
def advertisement():
  global password
  global username

  if request.method=='POST':
    sid=username
    pid=request.form.get('pid')
    pid=pid[4:]
    cursor1= g.conn.execute("select count(advertisement_id) from advertisement;")
    aid=1
    for result in cursor1:
      aid=aid+int(result[0])
    cursor1.close()
    aid='a00'+str(aid)
    g.conn.execute("""INSERT INTO Advertisement VALUES ('{aid}','{sellerid}', '{productid}','200');""".format(aid=aid,sellerid=sid,productid=pid))
    return redirect('/seller')
  
  username_m = '\'' + username + '\''
  cursor = g.conn.execute("SELECT * FROM Advertisement;")
  seller_ad = []
  for result in cursor:
    seller_ad.append([result['advertisement_id'], result['product_id'], result['price']])  #
  cursor.close()
  context = dict(data=seller_ad)

  return render_template("advertisement.html", **context)

if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='127.0.0.1')
  @click.argument('PORT', default=8111, type=int)
  
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
