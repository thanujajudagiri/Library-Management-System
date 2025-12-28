from flask import Flask, render_template, request, redirect, session
from datetime import date

# Import ONLY db connection (no global cursor)
from Library_db import db

app = Flask(__name__)
app.secret_key = "your_secret_key_here"


# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    error = ""

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        
        cursor = db.cursor()

        cursor.execute("SELECT id, name, password FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        cursor.close()  
        
        if user and password:
                session["id"] = user[0]
                session["name"] = user[1]
                return redirect("/dashboard")
        else:
            error = "Invalid Email or Password"

    return render_template("login.html", error=error)


# ---------------- SIGNUP ----------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = ""

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        cursor = db.cursor()  

        try:
            cursor.execute(
                "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
                (name, email, password)
            )
            db.commit()
            cursor.close()
            return redirect("/")
        except:
            cursor.close()
            error = "Email already exists"

    return render_template("signup.html", error=error)


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/")
    return render_template("dashboard.html")


# ---------------- ADD BOOK ----------------
@app.route("/add_book", methods=["GET", "POST"])
def add_book():
    if "user_id" not in session:
        return redirect("/")

    if request.method == "POST":
        title = request.form["title"]
        author = request.form["author"]
        department = request.form["department"]
        image = request.form["image"]

        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO books (title, author, department, image, status)
            VALUES (%s, %s, %s, %s, 'Available')
        """, (title, author, department, image))
        db.commit()
        cursor.close()

        return redirect("/view_books")

    return render_template("add_book.html")


# ---------------- VIEW + SEARCH BOOKS ----------------
@app.route("/view_books")
def view_books():
    if "user_id" not in session:
        return redirect("/")

    search = request.args.get("search")
    cursor = db.cursor()

    if search:
        cursor.execute("""
            SELECT * FROM books
            WHERE title LIKE %s
               OR author LIKE %s
               OR department LIKE %s
        """, (f"%{search}%", f"%{search}%", f"%{search}%"))
    else:
        cursor.execute("SELECT * FROM books")

    books = cursor.fetchall()
    cursor.close()

    return render_template("view_books.html", books=books)


# ---------------- ISSUE BOOK ----------------
@app.route("/issue/<int:id>")
def issue_book(id):
    if "user_id" not in session:
        return redirect("/")

    cursor = db.cursor()

    # Update status
    cursor.execute(
        "UPDATE books SET status='Issued' WHERE id=%s AND status='Available'",
        (id,)
    )

    # Insert issue record
    cursor.execute("""
        INSERT INTO issued_books (user_id, book_id, issue_date)
        VALUES (%s, %s, %s)
    """, (session["user_id"], id, date.today()))

    db.commit()
    cursor.close()

    return redirect("/issued_books")


# ---------------- ISSUED BOOKS ----------------
@app.route("/issued_books")
def issued_books():
    if "user_id" not in session:
        return redirect("/")

    cursor = db.cursor()
    cursor.execute("""
        SELECT books.id, books.title, issued_books.issue_date
        FROM issued_books
        JOIN books ON books.id = issued_books.book_id
        WHERE issued_books.user_id = %s
    """, (session["user_id"],))

    data = cursor.fetchall()
    cursor.close()

    return render_template("issued_books.html", data=data)


# ---------------- RETURN BOOK ----------------
@app.route("/return/<int:book_id>")
def return_book(book_id):
    if "user_id" not in session:
        return redirect("/")

    cursor = db.cursor()

    cursor.execute(
        "UPDATE books SET status='Available' WHERE id=%s",
        (book_id,)
    )
    cursor.execute(
        "DELETE FROM issued_books WHERE book_id=%s AND user_id=%s",
        (book_id, session["user_id"])
    )

    db.commit()
    cursor.close()

    return redirect("/issued_books")


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)




