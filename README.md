# GULED MOTORS

A responsive luxury-car dealership website built with Flask, SQLite, HTML, CSS and JavaScript. The first run creates `database.db` and seeds the eight sample vehicles automatically.

## Run locally on Windows

Open PowerShell in this project folder and run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Set credentials for the admin dashboard and a secret key for Flask sessions. Keep these values private:

```powershell
$env:ADMIN_USERNAME = "your-admin-name"
$env:ADMIN_PASSWORD = "use-a-long-unique-password"
$env:SECRET_KEY = (python -c "import secrets; print(secrets.token_hex(32))")
python app.py
```

Visit [http://127.0.0.1:5000](http://127.0.0.1:5000). Sign in to the dashboard at [http://127.0.0.1:5000/admin/login](http://127.0.0.1:5000/admin/login) using the credentials set above. These PowerShell environment variables apply only to the current terminal session.

The included Flask server is for local development. Use a production WSGI server and HTTPS when deploying. Set `FLASK_ENV=production` to enable secure session cookies.

## Customer accounts

Visitors can browse cars and contact the sales team without signing in. The **Log in** and **Sign up** links in the main navigation are for optional customer accounts; staff should continue to use the separate **Admin access** link in the footer. Customer passwords are stored as password hashes in the SQLite database, not as plain text.

## Deploy on Render

1. Push this repository to GitHub.
2. In Render, choose **New → Blueprint**, connect this repository, and deploy the `render.yaml` blueprint.
3. Enter values for `ADMIN_USERNAME` and `ADMIN_PASSWORD` when prompted, then use the generated Render URL to open the site.

The blueprint uses a paid Starter web service because SQLite data and uploaded images require a persistent disk. Keep the Render environment variables and disk configured when redeploying; do not put credentials in the repository.

## Managing the website

- **Add a car:** Sign in, complete the “Add a vehicle” form, add a cover image and optional gallery images, then submit. Images can be JPG, PNG or WebP, up to 8 MB total per request.
- **Edit a car:** Open its row in “Manage vehicles,” make changes, and save. Leave image fields empty to keep the current images.
- **Change availability:** Set a listing to Available, Reserved or Sold. Only available vehicles appear in the public collection.
- **Delete a car:** Open its row and use “Delete listing.”
- **Review enquiries:** Contact-form submissions and completed chatbot sales enquiries appear in the Enquiries section of the admin dashboard.
- **Back up data:** Locally, stop the app and copy `database.db` and `static/uploads/`. On Render, back up the persistent disk mounted at `/var/data`, which contains the database and uploaded images.

The app also initializes the database schema on startup. Sample vehicles are inserted once when the database is first created; deleting listings later will not restore them. Listings and enquiries are stored in SQLite. The customer chat is a rule-based helper, not an AI service: vehicle details and availability come from current inventory, and purchase enquiries are saved in the admin dashboard after the customer provides their name, preferred vehicle, budget, phone number and preferred payment method. Financing options and payment terms are not confirmed by the chat.

## Project layout

```text
app.py                  Flask routes, SQLite setup, chat replies, and admin actions
render.yaml             Render web service and persistent disk configuration
database.db             Created automatically on first run
requirements.txt        Python dependencies
templates/               Jinja templates for public and admin pages
templates/customer_*.html Customer registration and account pages
static/css/style.css     Responsive site styles
static/js/script.js     Navigation, inventory chat, and delete confirmation
static/uploads/          Uploaded car images
```
