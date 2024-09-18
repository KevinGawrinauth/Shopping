from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, session
import requests
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf.csrf import CSRFProtect
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
import json
import os

# Initializing flash to run
app = Flask(__name__)
app.secret_key = b'\xef\xd4\x16\x98h\xc6\xdd\xc3\xc6\xce\x02\xd6@o\x8a|\x08\x1c\xd6\\X{\xeex'
csrf = CSRFProtect(app)  # Enable CSRF protection

# File to store user data (sqlite-type database storrage)
USER_FILE = 'user_storage.json'

# Our Kroger API credentials 
client_id = 'kevingawrinauth-b1629c2310698a009e85d726fbc0e9aa8264849196508842534'
client_secret = 'fpfEnrPkQnQcWGySAoig8G6Up1ZosRbV8u0LrKSd'

# Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'login'  # This sets '/login' as the default login page
login_manager.init_app(app)

# Helper function to manage user data in a file
def read_users():
    if not os.path.exists(USER_FILE):
        return {}
    with open(USER_FILE, 'r') as file:
        return json.load(file)

def write_users(users):
    with open(USER_FILE, 'w') as file:
        json.dump(users, file)

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id):
        self.id = id

#  Flask-Login for loading the user
@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# login and registration classes
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign Up')

# Form for the logout button to include CSRF token
class LogoutForm(FlaskForm):
    submit = SubmitField('Sign Out')

# Fetch Kroger OAuth token
def get_kroger_token(client_id, client_secret):
    token_url = "https://api.kroger.com/v1/connect/oauth2/token"
    data = {
        'grant_type': 'client_credentials',
        'scope': 'product.compact'
    }
    auth = (client_id, client_secret)
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    response = requests.post(token_url, headers=headers, data=data, auth=auth)
    
    if response.status_code == 200:
        return response.json().get('access_token')
    else:
        raise Exception("Error fetching access token: " + str(response.json()))

# Route for user login
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()  # Create an instance of the login form
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        users = read_users()  # Read users from the file
        if username in users and users[username]['password'] == password:
            user = User(username)
            login_user(user)
            return redirect(url_for('home'))  # Redirect to home after login
        else:
            flash('Invalid username or password')
    return render_template('login.html', form=form)

# Route for guest login
@app.route('/guest_login')
def guest_login():
    # Automatically log in as a guest
    guest_user = User('guest')
    login_user(guest_user)
    return redirect(url_for('home'))  # Redirect to home after guest login

# Route for user registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()  # Create an instance of the registration form
    if form.validate_on_submit():
        new_username = form.username.data
        new_password = form.password.data
        users = read_users()  # Read users from the file
        
        if new_username in users:
            flash('Username already exists, please choose another.')
        else:
            users[new_username] = {'password': new_password}
            write_users(users)  # Save new user to the file
            flash('User registered successfully! Please log in.')
            return redirect(url_for('login'))
    
    return render_template('register.html', form=form)


@app.route('/logout', methods=['POST'])
@login_required
def logout():
    session.clear()  
    logout_user()  # Log out the user
    return redirect(url_for('login'))

@app.route('/')
@login_required
def home():
    form = LogoutForm()  # Initialize the logout form with CSRF protection
    username = "Guest" if current_user.id == 'guest' else current_user.id
    locations = [
        {"id": 1, "name": "Long Island - Amityville", "zip_code": "11701"},
        {"id": 2, "name": "Long Island - Hicksville", "zip_code": "11801"},
        {"id": 3, "name": "Long Island - Commack", "zip_code": "11725"},
        {"id": 4, "name": "Long Island - Syosset", "zip_code": "11791"},
        {"id": 5, "name": "Long Island - Patchogue", "zip_code": "11772"}
    ]
    return render_template('index.html', username=username, form=form, locations=locations)

# imeplementation for view cart page
@app.route('/cart')
@login_required
def view_cart():
    cart = session.get('cart', [])
    return render_template('cart.html', cart=cart)

# view favorites page
@app.route('/favorites')
@login_required
def view_favorites():
    return render_template('favorites.html')

# Predefined Long Island locations (no full logic yet)
locations = [
    {"id": 1, "name": "Long Island - Amityville", "zip_code": "11701"},
    {"id": 2, "name": "Long Island - Hicksville", "zip_code": "11801"},
    {"id": 3, "name": "Long Island - Commack", "zip_code": "11725"},
    {"id": 4, "name": "Long Island - Syosset", "zip_code": "11791"},
    {"id": 5, "name": "Long Island - Patchogue", "zip_code": "11772"},
]

# displaying the display store locations
@app.route('/locations')
@login_required
def get_locations():
    return render_template('locations.html', locations=locations)

# display products for a selected location(not implemented fully)
@app.route('/locations/<int:location_id>/products')
@login_required
def get_location_products(location_id):
    selected_location = next((loc for loc in locations if loc["id"] == location_id), None)
    if not selected_location:
        return jsonify({"error": "Invalid location selected"}), 404
    
    # Fetch products for the selected location using the location_id
    access_token = get_kroger_token(client_id, client_secret)
    search_url = "https://api.kroger.com/v1/products"
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    
    params = {
        'filter.locationId': location_id,  # Use location ID for store-specific pricing
        'filter.limit': 20  # Increase the number of products fetched
    }

    response = requests.get(search_url, headers=headers, params=params)
    
    if response.status_code == 200:
        products = response.json().get('data')
        return render_template('products.html', products=products, location=selected_location["name"])
    else:
        return jsonify({"error": "Error fetching products for the selected location"}), 500

#we will set the api to fetch products based on category
@app.route('/products/<category>')
@login_required
def get_products(category):
    access_token = get_kroger_token(client_id, client_secret)
    search_url = "https://api.kroger.com/v1/products"
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    
   
    category_mapping = {
        "Fruits": "fruit",
        "Meats": "meat",
        "Drinks": "beverage",
        "Frozen": "frozen"
    }
    
    search_term = category_mapping.get(category, "")
    
    # Fetch products based on the selected category
    params = {
        'filter.term': search_term,
        
    }

    response = requests.get(search_url, headers=headers, params=params)
    
    if response.status_code == 200:
        products = response.json().get('data')
        return render_template('products.html', products=products, category=category)
    else:
        return jsonify({"error": "Error fetching products"}), 500

# Function to add an item to the cart
@app.route('/add_to_cart/<product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    # Retrieve product info from the form
    product_name = request.form.get('product_name')
    product_price = request.form.get('product_price')

    # Initialize the cart if it doesn't exist
    if 'cart' not in session:
        session['cart'] = []
    
    # Add the product to the cart
    session['cart'].append({
        'id': product_id,
        'name': product_name,
        'price': product_price
    })
    
    # Update the cart counter
    session['cart_count'] = len(session['cart'])

    flash(f'Added {product_name} to cart!')
    return redirect(request.referrer)

# Function to retrieve the cart count to use in templates
@app.context_processor
def cart_counter():
    cart_count = session.get('cart_count', 0)
    return {'cart_count': cart_count}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)