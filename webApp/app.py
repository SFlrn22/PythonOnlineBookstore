from flask import Flask, flash, redirect, render_template, request, session, g, url_for
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
import psycopg2
from psycopg2 import OperationalError, errorcodes, errors
import string 
import random
app = Flask(__name__, static_url_path='/static', static_folder="static")

app.config["TEMPLATES_AUTO_RELOAD"] = True

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

conn = psycopg2.connect(database="", 
                        user = "", 
                        password = "", 
                        host = "", 
                        port = "")


cs = conn.cursor()

@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

def Error(message):
    def escape(s):
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                        ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("error.html", top="Oops", bottom=escape(message))

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def regenerate_code(code):
    snr = 10
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k = snr))
    codeq = "SELECT code FROM purch_user"
    cs.execute(codeq)
    codes = cs.fetchall()
    for uniquecode in codes:
        if uniquecode[0] == code:
            regenerate_code(code)
    return code

@app.route("/")
def index():
    if session.get("user_id") is None:
        return render_template("index.html")
    else:
        uid = session["user_id"]
        q = "SELECT type FROM users where id = %s"
        cs.execute(q, (uid,))
        res = cs.fetchall()
        if res[0][0] == "user" or res[0][0] == "":
            return render_template("index.html")
        elif res[0][0] == "admin":
            return redirect("/indexA")

@app.route("/indexA")
def indexA():
    return render_template("index_A.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        fn = request.form.get("firstname")
        ln = request.form.get("lastname")
        username = request.form.get("username")
        email = request.form.get("email")
        nrtel = request.form.get("nrtel")
        password = request.form.get("password")
        confi = request.form.get("confirmation")

        if not fn:
            return Error("First name missing")
        if not ln:
            return Error("Last name missing")
        if not username:
            return Error("Username missing")
        if not email:
            return Error("Email missing")
        if not nrtel:
            return Error("Phone number missing")
        if not password:
            return Error("Password missing")
        if not confi:
            return Error("Password confirmation missing")

        query = "SELECT * from users WHERE username = %s"
        cs.execute(query, (username,))
        res = cs.fetchall()
        if len(res) != 0:
            return Error("Username already exists")
        
        query2 = "SELECT * from users WHERE email = %s"
        cs.execute(query2, (email,))
        res2 = cs.fetchall()
        if len(res2) != 0:
                return Error("Email already exists")

        passh = generate_password_hash(password)

        insertq = "INSERT INTO USERS (firstname, lastname, username, password, email, phonenumber, type) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id"
        typeu = "user"
        vals = (fn, ln, username, passh, email, nrtel, typeu)
        cs.execute(insertq, vals)
        c_user = cs.fetchone()[0]
        conn.commit()
        session["user_id"] = c_user
        flash(u"Registered with success", 'success')

        return render_template("index.html")

    else:
        return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        
        username = request.form.get("username")
        password = request.form.get("password")

        if not username:
            return Error("Username missing")
        if not password:
            return Error("Password missing")

        query = "SELECT * from users WHERE username = %s"
        cs.execute(query, (username,))
        res = cs.fetchall()

        if len(res) != 1:
            return Error("Invalid username")

        if not check_password_hash(res[0][4], password):
            return Error("Invalid password")
        
        session["user_id"] = res[0][0]


        user_type = res[0][7]
        if user_type == "user":
            return render_template("index.html")
        if user_type == "admin":
            return redirect("/indexA")
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
     session.clear()
     return redirect("/")

@app.route("/products", methods=["GET", "POST"])
def products():
    if request.method == "POST":
        uid = session['user_id']
        bid = request.form.get("prodid")
        query = "SELECT * FROM books where id = {b}".format(b=bid)
        cs.execute(query)
        book = cs.fetchall()
        query2 = "SELECT username, review, id, book_id FROM users AS u INNER JOIN ratings as r ON u.id = r.user_id where book_id = {b}".format(b=bid)
        cs.execute(query2)
        ratings = cs.fetchall()
        return render_template("product.html", database = book, ratings = ratings, bid = bid, uid = uid)
    else:
        query = "SELECT * FROM books"
        cs.execute(query)
        books = cs.fetchall()
        return render_template("products.html", database = books)

@app.route("/productsA", methods=["GET", "POST"])
def productsA():
    if request.method == "POST" and "prodid" in request.form:
        bid = request.form.get("prodid")
        query = "SELECT * FROM books where id = {b}".format(b=bid)
        cs.execute(query)
        book = cs.fetchall()
        query2 = "SELECT username, review, rating FROM users AS u INNER JOIN ratings as r ON u.id = r.user_id where book_id = {b}".format(b=bid)
        cs.execute(query2)
        ratings = cs.fetchall()
        return render_template("productA.html", database = book, ratings = ratings, bid = bid)
    elif request.method == "POST" and "proddid" in request.form:
        idb = request.form.get("proddid")
        query = "DELETE FROM books WHERE id = %s"
        cs.execute(query, (idb, ))
        conn.commit()
        flash(u'Book deleted successfully', 'success')
        return redirect("/productsA")
    else:
        query = "SELECT * FROM books"
        cs.execute(query)
        books = cs.fetchall()
        return render_template("productsA.html", database = books)


@app.route("/product", methods=["GET","POST"])
def product():
    if request.method == "POST" and "reviewinp" in request.form:
        bid = request.form.get('bookid')
        uid = session['user_id']
        review = request.form.get('reviewinp')
        insertq = "INSERT INTO ratings (book_id, user_id, review) VALUES (%s, %s, %s)"
        vals = (bid, uid, review)
        try: 
            cs.execute(insertq, vals)
            conn.commit()
        except:
            conn.rollback()
            return Error("Already commented")

        query = "SELECT * FROM books where id = {b}".format(b=bid)
        cs.execute(query)
        book = cs.fetchall()
        query2 = "SELECT username, review, rating FROM users AS u INNER JOIN ratings as r ON u.id = r.user_id where book_id = {b}".format(b=bid)
        cs.execute(query2)
        ratings = cs.fetchall()
        return render_template("product.html", database = book, ratings = ratings, bid = bid, uid = uid)
    elif request.method == "POST" and "sprodid" in request.form:
        pid = request.form.get("sprodid")
        uid = session['user_id']
        insertq = "INSERT INTO cart (book_id, user_id) VALUES (%s, %s)"
        vals = (pid, uid)
        try: 
            cs.execute(insertq, vals)
            conn.commit()
        except:
            conn.rollback()
            return Error("Transaction error")
        
        return redirect("/cart")
    elif request.method == "POST" and "bookid" in request.form:
        userid = request.form.get("userid")
        bookid = request.form.get("bookid")
        query = "DELETE FROM ratings WHERE book_id = %s and user_id = %s"
        vals = (bookid, userid)
        try:
            cs.execute(query, vals)
            conn.commit()
        except:
            conn.rollback()
            return Error("Transaction error")
        query = "SELECT * FROM books where id = {b}".format(b=bookid)
        cs.execute(query)
        book = cs.fetchall()
        query2 = "SELECT username, review FROM users AS u INNER JOIN ratings as r ON u.id = r.user_id where book_id = {b}".format(b=bookid)
        cs.execute(query2)
        ratings = cs.fetchall()
        return render_template("product.html", database = book, ratings = ratings, bid = bookid, uid = userid)
    elif request.method == "GET":
        uid = session['user_id']
        bid = request.form.get("prodid")
        query = "SELECT * FROM books where id = {b}".format(b=bid)
        cs.execute(query)
        book = cs.fetchall()
        query2 = "SELECT username, review, isbn FROM users AS u INNER JOIN ratings as r ON u.id = r.user_id where book_id = {b}".format(b=bid)
        cs.execute(query2)
        ratings = cs.fetchall()
        return render_template("product.html", database = book, ratings = ratings, bid = bid, uid = uid)

@app.route("/productA", methods=["GET", "POST"])
def productA():
    if request.method == "POST":
        name = request.form.get("usern")
        query = "SELECT id FROM users WHERE username like %s"
        cs.execute(query, (name, ))
        nid = cs.fetchall()
        dq = "DELETE FROM ratings WHERE user_id = %s"
        try:
            cs.execute(dq, (nid[0][0], ))
            conn.commit()
        except:
            conn.rollback()
            return Error("Something went wrong")
        bid = request.form.get("bid")
        print("\nPRINT\n")
        print(bid)
        query = "SELECT * FROM books where id = {b}".format(b=bid)
        cs.execute(query)
        book = cs.fetchall()
        query2 = "SELECT username, review, rating, book_id FROM users AS u INNER JOIN ratings as r ON u.id = r.user_id where book_id = {b}".format(b=bid)
        cs.execute(query2)
        ratings = cs.fetchall()
        flash(u'Comment deleted successfully', 'success')
        return render_template("productA.html", database = book, ratings = ratings, bid = bid)
    elif request.method == "GET":
        bid = request.form.get("prodid")
        query = "SELECT * FROM books where id = {b}".format(b=bid)
        cs.execute(query)
        book = cs.fetchall()
        query2 = "SELECT username, review, rating, FROM users AS u INNER JOIN ratings as r ON u.id = r.user_id where book_id = {b}".format(b=bid)
        cs.execute(query2)
        ratings = cs.fetchall()
        return render_template("productA.html", database = book, ratings = ratings, bid = bid)

@app.route("/cart", methods=["GET","POST"])
@login_required
def cart():
    if request.method == "GET":
        uid = session['user_id']
        query = "SELECT title,author,publisher,publicationyear,b.id FROM cart as c INNER JOIN books as b on c.book_id = b.id where user_id = {b}".format(b=uid)
        cs.execute(query)
        cart = cs.fetchall()
        return render_template("cart.html", database = cart)
    elif request.method == "POST" and "rmi" not in request.form:
        uid = session['user_id']
        query = "SELECT book_id FROM cart where user_id = {b}".format(b=uid)
        cs.execute(query)
        books = cs.fetchall()
        insertq1 = "INSERT INTO purch_user (code, user_id, status) VALUES (%s, %s, %s) RETURNING idp"
        snr = 10
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k = snr))
        codeq = "SELECT code FROM purch_user"
        cs.execute(codeq)
        codes = cs.fetchall()
        for uniquecode in codes:
            if uniquecode[0] == code:
                code = regenerate_code(code)
        vals = (code, uid, "unassigned")
        try: 
            cs.execute(insertq1, vals)
            idp = cs.fetchone()[0]
            conn.commit()
        except:
            conn.rollback()
            return Error("Something went wrong")
        insertq2 = "INSERT INTO purch_content (book_id, purchase_id) VALUES (%s, %s)"
        for rows in books:
            vals = (rows[0], idp)
            try: 
                cs.execute(insertq2, vals)
                conn.commit()
            except:
                conn.rollback()
                return Error("Something went wrong")

        for rows in books:
            cs.execute("DELETE FROM cart where book_id = %s", (rows[0],))
        conn.commit()
        return redirect("\purchase")
    elif request.method == "POST" and "rmi" in request.form:
        uid = session['user_id']
        rmi = request.form.get("rmi")
        dq = "DELETE FROM cart WHERE book_id = %s AND user_id = %s"
        vals = (rmi, uid)
        cs.execute(dq, vals)
        conn.commit()
        return redirect("/cart")
        # query2 = "SELECT pno FROM purchase where user_id = {b}".format(b=uid)
        # cs.execute(query2)
        # nop = cs.fetchall()
        # print(nop)
        # maxp = max(nop, default = 0)
        # insertq = "INSERT INTO purchase (book_id, user_id, pno, status) VALUES (%s, %s, %s, %s)"
        # for rows in books:
        #     if maxp == 0:
        #         vals = (rows[0], uid, 1, "In transit")
        #         try: 
        #             cs.execute(insertq, vals)
        #             conn.commit()
        #         except:
        #             conn.rollback()
        #             return Error("Something went wrong")
        #     else:
        #         vals = (rows[0], uid, maxp[0] + 1, "In transit")
        #         try: 
        #             cs.execute(insertq, vals)
        #             conn.commit()
        #         except:
        #             conn.rollback()
        #             return Error("Something went wrong")

@app.route("/purchase", methods=["GET", 'POST'])
@login_required
def purchase():
    if request.method == "GET":
        uid = session['user_id']
        query = "SELECT title, author, publicationyear, code, status, timeadd FROM purch_view WHERE user_id = %s ORDER BY status,timeadd"
        val = uid
        cs.execute(query, (val,))
        purch = cs.fetchall()
        query2 = "SELECT DISTINCT(code), status, timeadd FROM purch_view WHERE user_id = %s ORDER BY status,timeadd"
        val2 = uid
        cs.execute(query2, (val2,))
        uc = cs.fetchall()
        return render_template("purchase.html", database = purch, codes = uc)
        # query = "SELECT title, author, publisher, publicationyear, pno FROM purchase as p INNER JOIN books as b on p.book_id = b.id where user_id = {b}".format(b=uid)
        # cs.execute(query)
        # purch = cs.fetchall()
        # query2 = "SELECT pno FROM purchase as p INNER JOIN books as b on p.book_id = b.id where user_id = {b}".format(b=uid)
        # cs.execute(query2)
        # nos = cs.fetchall()
        # maxv = max(nos, default = 0)
        # return render_template("purchase.html", database = purch, maxn = maxv)
    if request.method == "POST":
        code = request.form.get("rec")
        q = "UPDATE purch_user SET received = %s WHERE code = %s"
        vals = ('yes', code)
        conn.commit()
        try: 
            cs.execute(q, vals)
            conn.commit()
        except:
            conn.rollback()
            return Error("Something went wrong")
        
        sq = "SELECT delivered, received FROM purch_user WHERE code = %s"
        cs.execute(sq, (code,))
        stats = cs.fetchone()
        deliv = stats[0]
        rec = stats[1]

        if deliv == "yes" and rec == "yes":
            qf = "UPDATE purch_user SET status = %s WHERE code = %s"
            vals = ('finished', code)
            conn.commit()
            try: 
                cs.execute(qf, vals)
                conn.commit()
            except:
                conn.rollback()
                return Error("Something went wrong")

        return redirect("/purchase")
@app.route("/addb", methods=["GET", "POST"])
def addb():
    if request.method == "POST":
        isbn = request.form.get("isbn")
        title = request.form.get("title")
        author = request.form.get("author")
        publisher = request.form.get("publisher")
        yop = request.form.get("yop")
        description = request.form.get("description")
        psimg = request.form.get("psimg")
        pimg = request.form.get("pimg")

        if not isbn:
            return Error("ISBN missing")
        if not title:
            return Error("Title missing")
        if not author:
            return Error("Author missing")
        if not publisher:
            return Error("Publisher missing")
        if not yop:
            return Error("Year of publication missing")
        if not description:
            return Error("Description missing")
        if not psimg:
            return Error("Big image link missing")

        query = "SELECT * from books WHERE isbn = %s"
        cs.execute(query, (isbn,))
        res = cs.fetchall()
        if len(res) != 0:
            return Error("Book already exists")
        
        iq = "INSERT INTO books (isbn, title, author, publisher, publicationyear, description, imglink, pimg) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        vals = (isbn, title, author, publisher, yop, description, psimg, pimg) 
        try:
            cs.execute(iq, vals)
            conn.commit()
        except:
            conn.rollback()
            return Error("Something went wrong")
        
        flash(u'Book added successfully', 'success')
        return render_template("addb.html")
    else:
        return render_template("addb.html")

@app.route("/plog", methods=["GET", "POST"])
@login_required
def plog():
    if request.method == "GET":
        query = "SELECT username, code, title, status from purch_view as pv INNER JOIN users as u ON pv.user_id = u.id ORDER BY status, timeadd"
        cs.execute(query)
        purch = cs.fetchall()
        q2 = "SELECT DISTINCT(username) from purch_view as pv INNER JOIN users as u ON pv.user_id = u.id"
        cs.execute(q2)
        usn = cs.fetchall()
        q3 = "SELECT DISTINCT(code), username, timeadd, status from purch_view as pv INNER JOIN users as u ON pv.user_id = u.id ORDER BY status, timeadd"
        cs.execute(q3)
        codes = cs.fetchall()
        cq = "SELECT id, username FROM couriers"
        cs.execute(cq)
        couriers = cs.fetchall()
        return render_template("plog.html", database = purch, users = usn, codes = codes, couriers = couriers)
    if request.method == "POST":
        pcode = request.form.get("addc")
        courierid = request.form.get("courrid")
        query = "SELECT idp FROM purch_user WHERE code = %s"
        cs.execute(query, (pcode,))
        idp = cs.fetchone()[0]
        iq = "INSERT INTO purch_courier (courier_id, purchase_id) VALUES (%s, %s)"
        vals = (courierid, idp)
        try:
            cs.execute(iq, vals)
            conn.commit()
        except:
            conn.rollback()
            return Error("Something went wrong")
        updq = "UPDATE purch_user SET status = %s WHERE idp = %s"
        valsu = ("in transit", idp)
        try:
            cs.execute(updq, valsu)
            conn.commit()
        except:
            conn.rollback()
            return Error("Something went wrong")
        return redirect("/plog")
        # query = "SELECT title, pno, username FROM (purchase as p INNER JOIN books as b on p.book_id = b.id) INNER JOIN users as u ON p.user_id = u.id ORDER BY user_id, pno"
        # cs.execute(query)
        # purch = cs.fetchall()
        # query2 = "SELECT username, max(pno) FROM (SELECT title, pno, username FROM (purchase as p INNER JOIN books as b on p.book_id = b.id) INNER JOIN users as u ON p.user_id = u.id ORDER BY user_id, pno) as q GROUP BY q.username ORDER BY q.username"
        # cs.execute(query2)
        # nos = cs.fetchall()
        # return render_template("plog.html", database = purch, maxn = nos)