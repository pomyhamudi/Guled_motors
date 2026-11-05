import hmac
import json
import os
import secrets
import sqlite3
from datetime import date
from functools import wraps
from pathlib import Path
from uuid import uuid4

from flask import (
    Flask,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from werkzeug.utils import secure_filename


BASE_DIR = Path(__file__).resolve().parent
DATABASE = Path(os.environ.get("DATABASE_PATH", BASE_DIR / "database.db"))
UPLOAD_FOLDER = Path(
    os.environ.get("UPLOAD_FOLDER", BASE_DIR / "static" / "uploads")
)
ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY") or secrets.token_hex(32),
    MAX_CONTENT_LENGTH=8 * 1024 * 1024,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("FLASK_ENV") == "production",
)
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

SAMPLE_CARS = [
    ("Mercedes-Benz", "S-Class S 500", 2023, 24500000, 12000, "Automatic", "Petrol", "3.0L turbocharged inline-6, mild hybrid", "A flagship saloon with a serene cabin, intelligent driver assistance and effortless performance.", "https://images.unsplash.com/photo-1618843479313-40f8afb4b4d8?auto=format&fit=crop&w=1200&q=85", "Nappa leather, heated and ventilated seats, ambient lighting, panoramic roof", "LED lighting, 20-inch alloy wheels, chrome detailing"),
    ("BMW", "7 Series 740i", 2022, 21800000, 18500, "Automatic", "Petrol", "3.0L turbocharged inline-6", "Contemporary executive comfort meets confident BMW performance in this beautifully appointed 7 Series.", "https://images.unsplash.com/photo-1555215695-3004980ad54e?auto=format&fit=crop&w=1200&q=85", "Merino leather, executive rear seating, premium surround audio", "Adaptive LED headlights, 20-inch alloy wheels, panoramic glass roof"),
    ("Land Rover", "Range Rover Sport HSE", 2022, 23900000, 22000, "Automatic", "Diesel", "3.0L turbocharged inline-6", "A versatile luxury SUV with composed road manners, refined craftsmanship and all-terrain capability.", "https://images.unsplash.com/photo-1606664515524-ed2f786a0bd6?auto=format&fit=crop&w=1200&q=85", "Windsor leather, Meridian sound system, heated front seats", "Matrix LED headlights, 21-inch alloy wheels, panoramic roof"),
    ("Toyota", "Land Cruiser V8 VX", 2021, 19800000, 31000, "Automatic", "Diesel", "4.5L twin-turbo V8 diesel", "The Land Cruiser's legendary dependability, generous space and go-anywhere confidence.", "https://images.unsplash.com/photo-1519641471654-76ce0107ad1b?auto=format&fit=crop&w=1200&q=85", "Leather upholstery, three-zone climate control, rear entertainment", "LED headlights, 18-inch alloy wheels, side steps"),
    ("Porsche", "Cayenne S", 2022, 20500000, 16000, "Automatic", "Petrol", "2.9L twin-turbo V6", "Sportscar-inspired handling and everyday practicality, finished with a premium leather interior.", "https://images.unsplash.com/photo-1611859266238-4b98091d9d9b?auto=format&fit=crop&w=1200&q=85", "Leather sports seats, BOSE audio, panoramic roof", "LED matrix headlights, 21-inch alloy wheels, sport exhaust"),
    ("Lexus", "LX 600 F Sport", 2023, 28500000, 9000, "Automatic", "Petrol", "3.5L twin-turbo V6", "A commanding flagship SUV combining quiet luxury, modern technology and exceptional build quality.", "https://images.unsplash.com/photo-1518987048-93e29699e79a?auto=format&fit=crop&w=1200&q=85", "Semi-aniline leather, Mark Levinson audio, heated and ventilated seats", "F Sport exterior package, 22-inch alloy wheels, adaptive LED lights"),
    ("Lamborghini", "Urus S", 2022, 49500000, 7800, "Automatic", "Petrol", "4.0L twin-turbo V8", "Super SUV performance with unmistakable Italian design and a richly equipped cabin.", "https://images.unsplash.com/photo-1511919884226-fd3cad34687c?auto=format&fit=crop&w=1200&q=85", "Leather and Alcantara trim, heated sports seats, premium audio", "Sculpted bodywork, 22-inch alloy wheels, carbon ceramic brakes"),
    ("Rolls-Royce", "Cullinan", 2021, 78000000, 6500, "Automatic", "Petrol", "6.75L twin-turbo V12", "Handcrafted refinement, remarkable presence and effortless V12 power in a first-class SUV.", "https://images.unsplash.com/photo-1563720223185-11003d516935?auto=format&fit=crop&w=1200&q=85", "Handcrafted leather, rear theatre configuration, bespoke audio", "Illuminated grille, coach doors, 22-inch polished alloy wheels"),
]


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_error=None):
    database = g.pop("db", None)
    if database is not None:
        database.close()


def init_db():
    database = sqlite3.connect(DATABASE)
    database.executescript(
        """
        CREATE TABLE IF NOT EXISTS cars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT NOT NULL,
            name TEXT NOT NULL,
            year INTEGER NOT NULL,
            price INTEGER NOT NULL,
            mileage INTEGER NOT NULL,
            transmission TEXT NOT NULL,
            fuel TEXT NOT NULL,
            engine TEXT NOT NULL,
            description TEXT NOT NULL,
            interior_features TEXT NOT NULL DEFAULT '',
            exterior_features TEXT NOT NULL DEFAULT '',
            image_url TEXT NOT NULL,
            gallery_json TEXT NOT NULL DEFAULT '[]',
            availability TEXT NOT NULL DEFAULT 'Available',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS inquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            car_interest TEXT,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS app_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """
    )
    existing_columns = {
        row[1] for row in database.execute("PRAGMA table_info(cars)").fetchall()
    }
    for column in ("interior_features", "exterior_features"):
        if column not in existing_columns:
            database.execute(
                f"ALTER TABLE cars ADD COLUMN {column} TEXT NOT NULL DEFAULT ''"
            )
    seeded = database.execute(
        "SELECT value FROM app_meta WHERE key = 'sample_cars_seeded'"
    ).fetchone()
    count = database.execute("SELECT COUNT(*) FROM cars").fetchone()[0]
    if not seeded and count == 0:
        database.executemany(
            """INSERT INTO cars
            (brand, name, year, price, mileage, transmission, fuel, engine,
             description, image_url, interior_features, exterior_features)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            SAMPLE_CARS,
        )
    if not seeded:
        database.execute(
            "INSERT INTO app_meta (key, value) VALUES ('sample_cars_seeded', 'true')"
        )
    database.commit()
    database.close()


def csrf_token():
    token = session.get("_csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf_token"] = token
    return token


@app.context_processor
def inject_template_values():
    return {"csrf_token": csrf_token, "current_year": date.today().year}


@app.before_request
def protect_post_requests():
    if request.method == "POST":
        supplied = request.form.get("csrf_token", "")
        expected = session.get("_csrf_token", "")
        if not expected or not hmac.compare_digest(supplied, expected):
            abort(400, description="Your form session expired. Please refresh and try again.")


def admin_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login", next=request.path))
        return view(**kwargs)

    return wrapped_view


def car_by_id(car_id):
    car = get_db().execute("SELECT * FROM cars WHERE id = ?", (car_id,)).fetchone()
    if car is None:
        abort(404)
    return car


def save_uploaded_image(image):
    if not image or not image.filename:
        return None
    filename = secure_filename(image.filename)
    if "." not in filename:
        abort(400, description="Choose a valid image file.")
    extension = filename.rsplit(".", 1)[1].lower()
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        abort(400, description="Images must be JPG, PNG or WebP.")
    new_name = f"{uuid4().hex}.{extension}"
    image.save(UPLOAD_FOLDER / new_name)
    return f"/uploads/{new_name}"


def save_uploaded_images(images):
    saved_images = []
    for image in images:
        saved_image = save_uploaded_image(image)
        if saved_image:
            saved_images.append(saved_image)
    return saved_images


def remove_uploaded_images(image_paths):
    upload_directory = UPLOAD_FOLDER.resolve()
    for image_path in image_paths:
        if not image_path.startswith(("/uploads/", "/static/uploads/")):
            continue
        filename = image_path.rsplit("/", 1)[-1]
        stored_path = (upload_directory / filename).resolve()
        if stored_path.parent == upload_directory and stored_path.is_file():
            stored_path.unlink()


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


def car_form_values():
    fields = (
        "brand",
        "name",
        "year",
        "price",
        "mileage",
        "transmission",
        "fuel",
        "engine",
        "description",
        "interior_features",
        "exterior_features",
        "availability",
    )
    values = {field: request.form.get(field, "").strip() for field in fields}
    try:
        values["year"] = int(values["year"])
        values["price"] = int(values["price"])
        values["mileage"] = int(values["mileage"])
    except ValueError:
        abort(400, description="Year, price and mileage must be whole numbers.")
    if not all(str(values[field]).strip() for field in fields):
        abort(400, description="Please complete every required car field.")
    if values["year"] < 1900 or values["year"] > 2100 or values["price"] < 0 or values["mileage"] < 0:
        abort(400, description="Enter a valid year, price and mileage.")
    if values["transmission"] not in {"Automatic", "Manual"}:
        abort(400, description="Choose a valid transmission.")
    if values["availability"] not in {"Available", "Reserved", "Sold"}:
        abort(400, description="Choose a valid availability status.")
    return values


@app.route("/")
def home():
    cars = get_db().execute(
        "SELECT * FROM cars WHERE availability = 'Available' ORDER BY created_at DESC, id LIMIT 8"
    ).fetchall()
    return render_template("index.html", cars=cars)


@app.route("/cars")
def cars():
    filters = {
        "search": request.args.get("search", "").strip(),
        "brand": request.args.get("brand", "").strip(),
        "max_price": request.args.get("max_price", "").strip(),
        "year": request.args.get("year", "").strip(),
        "transmission": request.args.get("transmission", "").strip(),
        "fuel": request.args.get("fuel", "").strip(),
    }
    query = "SELECT * FROM cars WHERE availability = 'Available'"
    params = []
    if filters["search"]:
        query += " AND (brand LIKE ? OR name LIKE ?)"
        params.extend([f"%{filters['search']}%", f"%{filters['search']}%"])
    if filters["brand"]:
        query += " AND brand = ?"
        params.append(filters["brand"])
    if filters["max_price"]:
        try:
            max_price = int(filters["max_price"])
        except ValueError:
            abort(400, description="Maximum price must be a whole number.")
        if max_price < 0:
            abort(400, description="Maximum price cannot be negative.")
        query += " AND price <= ?"
        params.append(max_price)
    if filters["year"]:
        try:
            year = int(filters["year"])
        except ValueError:
            abort(400, description="Year must be a whole number.")
        query += " AND year = ?"
        params.append(year)
    if filters["transmission"]:
        query += " AND transmission = ?"
        params.append(filters["transmission"])
    if filters["fuel"]:
        query += " AND fuel = ?"
        params.append(filters["fuel"])
    query += " ORDER BY created_at DESC, id"
    listings = get_db().execute(query, params).fetchall()
    brands = get_db().execute(
        "SELECT DISTINCT brand FROM cars WHERE availability = 'Available' ORDER BY brand"
    ).fetchall()
    return render_template("cars.html", cars=listings, brands=brands, filters=filters)


@app.route("/cars/<int:car_id>")
def car_details(car_id):
    car = car_by_id(car_id)
    gallery = json.loads(car["gallery_json"] or "[]")
    return render_template("car_details.html", car=car, gallery=gallery)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        values = {key: request.form.get(key, "").strip() for key in ("name", "email", "phone", "car_interest", "message")}
        if not all(values[key] for key in ("name", "email", "phone", "message")):
            flash("Please complete your name, email, phone and message.", "error")
            return render_template("contact.html", form=values), 400
        if "@" not in values["email"] or len(values["email"]) > 254:
            flash("Please enter a valid email address.", "error")
            return render_template("contact.html", form=values), 400
        get_db().execute(
            """INSERT INTO inquiries (name, email, phone, car_interest, message)
            VALUES (?, ?, ?, ?, ?)""",
            (values["name"], values["email"], values["phone"], values["car_interest"], values["message"]),
        )
        get_db().commit()
        flash("Thank you. Our team will be in touch shortly.", "success")
        return redirect(url_for("contact"))
    return render_template("contact.html", form={})


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("admin_logged_in"):
        return redirect(url_for("admin_dashboard"))
    if request.method == "POST":
        username = os.environ.get("ADMIN_USERNAME", "")
        password = os.environ.get("ADMIN_PASSWORD", "")
        supplied_username = request.form.get("username", "")
        supplied_password = request.form.get("password", "")
        valid = (
            bool(username and password)
            and hmac.compare_digest(supplied_username, username)
            and hmac.compare_digest(supplied_password, password)
        )
        if valid:
            session.clear()
            session["admin_logged_in"] = True
            flash("Welcome back.", "success")
            destination = request.args.get("next", "")
            return redirect(destination if destination.startswith("/") and not destination.startswith("//") else url_for("admin_dashboard"))
        flash("Sign-in failed. Check your credentials and server configuration.", "error")
    return render_template("login.html")


@app.route("/admin/logout", methods=["POST"])
@admin_required
def admin_logout():
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("home"))


@app.route("/admin")
@admin_required
def admin_dashboard():
    database = get_db()
    listings = database.execute("SELECT * FROM cars ORDER BY created_at DESC, id DESC").fetchall()
    inquiries = database.execute("SELECT * FROM inquiries ORDER BY created_at DESC, id DESC").fetchall()
    return render_template("admin.html", cars=listings, inquiries=inquiries)


@app.route("/admin/cars/add", methods=["POST"])
@admin_required
def add_car():
    values = car_form_values()
    image_url = save_uploaded_image(request.files.get("image")) or request.form.get("image_url", "").strip()
    if not image_url:
        abort(400, description="Upload a car image or provide an image URL.")
    gallery = save_uploaded_images(request.files.getlist("gallery_images"))
    get_db().execute(
        """INSERT INTO cars
        (brand, name, year, price, mileage, transmission, fuel, engine,
         description, interior_features, exterior_features, image_url,
         gallery_json, availability)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            *[values[field] for field in ("brand", "name", "year", "price", "mileage", "transmission", "fuel", "engine", "description", "interior_features", "exterior_features")],
            image_url,
            json.dumps(gallery),
            values["availability"],
        ),
    )
    get_db().commit()
    flash("Car listing added.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/cars/<int:car_id>/edit", methods=["POST"])
@admin_required
def edit_car(car_id):
    existing_car = car_by_id(car_id)
    values = car_form_values()
    uploaded_image = save_uploaded_image(request.files.get("image"))
    image_url = uploaded_image or request.form.get("image_url", "").strip()
    if not image_url:
        image_url = existing_car["image_url"]
    gallery = save_uploaded_images(request.files.getlist("gallery_images"))
    gallery_json = json.dumps(gallery) if gallery else existing_car["gallery_json"]
    get_db().execute(
        """UPDATE cars SET brand = ?, name = ?, year = ?, price = ?, mileage = ?,
        transmission = ?, fuel = ?, engine = ?, description = ?, interior_features = ?,
        exterior_features = ?, image_url = ?, gallery_json = ?, availability = ?
        WHERE id = ?""",
        (
            *[values[field] for field in ("brand", "name", "year", "price", "mileage", "transmission", "fuel", "engine", "description", "interior_features", "exterior_features")],
            image_url,
            gallery_json,
            values["availability"],
            car_id,
        ),
    )
    get_db().commit()
    retired_images = []
    if image_url != existing_car["image_url"]:
        retired_images.append(existing_car["image_url"])
    if gallery:
        retired_images.extend(json.loads(existing_car["gallery_json"] or "[]"))
    remove_uploaded_images(retired_images)
    flash("Car listing updated.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/cars/<int:car_id>/delete", methods=["POST"])
@admin_required
def delete_car(car_id):
    car = car_by_id(car_id)
    get_db().execute("DELETE FROM cars WHERE id = ?", (car_id,))
    get_db().commit()
    remove_uploaded_images(
        [car["image_url"], *json.loads(car["gallery_json"] or "[]")]
    )
    flash("Car listing deleted.", "success")
    return redirect(url_for("admin_dashboard"))


@app.errorhandler(400)
def bad_request(error):
    return render_template("error.html", code=400, message=error.description), 400


@app.errorhandler(404)
def not_found(_error):
    return render_template("error.html", code=404, message="The page or vehicle you requested could not be found."), 404


init_db()

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
