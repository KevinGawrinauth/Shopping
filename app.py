# Import necessary libraries
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, session
import requests
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf.csrf import CSRFProtect
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
import json
import os

# First we are going to initialize the Flask app
app = Flask(__name__)
app.secret_key = b'\xef\xd4\x16\x98h\xc6\xdd\xc3\xc6\xce\x02\xd6@o\x8a|\x08\x1c\xd6\\X{\xeex'
csrf = CSRFProtect(app)  # Enable CSRF protection

# We created a file to store user data (this simulates a database using mysql lite)
USER_FILE = 'user_storage.json'

# Our Kroger API credentials 
client_id = 'kevingawrinauth-b1629c2310698a009e85d726fbc0e9aa8264849196508842534'
client_secret = 'fpfEnrPkQnQcWGySAoig8G6Up1ZosRbV8u0LrKSd'

# Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'login'  
login_manager.init_app(app)

# implemented a helper functions to manage user data in a file
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

# now we will configure the user using Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# Now we will try to create the Form class for login and registration
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign Up')

# Form for the logout button 
class LogoutForm(FlaskForm):
    submit = SubmitField('Sign Out')

# Fetching our Kroger OAuth token
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

# this is our user login route 
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()  # implementing the login form to be displaed
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        users = read_users()  # allow us to read the users from the file saved from mysql lite
        if username in users and users[username]['password'] == password:
            user = User(username)
            login_user(user)
            return redirect(url_for('home'))  # redirect to home after login
        else:
            flash('Invalid username or password')
    return render_template('login.html', form=form)

# our guest login route
@app.route('/guest_login')
def guest_login():
    # automatically log in as a guest
    guest_user = User('guest')
    login_user(guest_user)
    return redirect(url_for('home'))  # should allow us redirect to home after guest login

# the route for our user registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()  #  registration form
    if form.validate_on_submit():
        new_username = form.username.data
        new_password = form.password.data
        users = read_users()  # reads users from the file saved in db 
        
        if new_username in users:
            flash('Username already exists, please choose another.')
        else:
            users[new_username] = {'password': new_password}
            write_users(users)  # saves new user to the file
            flash('User registered successfully! Please log in.')
            return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form.get('email')
        
        # Logic to verify the email and send a reset password link(not implemented fully will do so later)
        if email:
            flash('Password reset instructions have been sent to your email.', 'info')
        else:
            flash('Invalid email address!', 'danger')
        return redirect(url_for('login'))

    # sets the GET request, which render the forgot password page
    return render_template('forgot_password.html')

@app.route('/')
@login_required
def home():
    form = LogoutForm()  # here im initializing the logout form with CSRF protection
    username = "Guest" if current_user.id == 'guest' else current_user.id
    locations = [
        {"id": 1, "name": "Long Island - Amityville", "zip_code": "11701"},
        {"id": 2, "name": "Long Island - Hicksville", "zip_code": "11801"},
        {"id": 3, "name": "Long Island - Commack", "zip_code": "11725"},
        {"id": 4, "name": "Long Island - Syosset", "zip_code": "11791"},
        {"id": 5, "name": "Long Island - Patchogue", "zip_code": "11772"}
    ]
    return render_template('index.html', username=username, form=form, locations=locations)

# route to view cart page
@app.route('/cart')
@login_required
def view_cart():
    cart = session.get('cart', [])
    return render_template('cart.html', cart=cart)

# route to view favorites page
@app.route('/favorites')
@login_required
def view_favorites():
    return render_template('favorites.html')

# our set predefined Long Island locations (Fake for demonstration)
locations = [
    {"id": 1, "name": "Long Island - Amityville", "zip_code": "11701"},
    {"id": 2, "name": "Long Island - Hicksville", "zip_code": "11801"},
    {"id": 3, "name": "Long Island - Commack", "zip_code": "11725"},
    {"id": 4, "name": "Long Island - Syosset", "zip_code": "11791"},
    {"id": 5, "name": "Long Island - Patchogue", "zip_code": "11772"},
]

# route to display store locations
@app.route('/locations')
@login_required
def get_locations():
    return render_template('locations.html', locations=locations)

# route to display products for a selected location
@app.route('/locations/<int:location_id>/products')
@login_required
def get_location_products(location_id):
    selected_location = next((loc for loc in locations if loc["id"] == location_id), None)
    if not selected_location:
        return jsonify({"error": "Invalid location selected"}), 404
    
    # Fetching our products for the selected location using the location_id
    access_token = get_kroger_token(client_id, client_secret)
    search_url = "https://api.kroger.com/v1/products"
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    
    params = {
        'filter.locationId': location_id,  # Use location ID for store-specific pricing
        'filter.limit': 20  # Increase the number of products fetched or displayed in the app
    }

    response = requests.get(search_url, headers=headers, params=params)
    
    if response.status_code == 200:
        products = response.json().get('data')
        return render_template('products.html', products=products, location=selected_location["name"])
    else:
        return jsonify({"error": "Error fetching products for the selected location"}), 500

# route to fetch products based on category
@app.route('/products/<category>')
@login_required
def get_products(category):
    access_token = get_kroger_token(client_id, client_secret)
    search_url = "https://api.kroger.com/v1/products"
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    
    # map category to search terms
    category_mapping = {
        "Fruits": "fruit",
        "Meats": "meat",
        "Drinks": "beverage",
        "Frozen": "frozen"
    }
    
    search_term = category_mapping.get(category, "")
    
    # fetch products based on the selected category
    params = {
        'filter.term': search_term,
        'filter.limit': 10  # Adjust limit as needed shown in app
    }

    response = requests.get(search_url, headers=headers, params=params)
    
    if response.status_code == 200:
        products = response.json().get('data')
        return render_template('products.html', products=products, category=category)
    else:
        return jsonify({"error": "Error fetching products"}), 500

# implemented a function to add an item to the cart
@app.route('/add_to_cart/<product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    # retrieve product info from the form
    product_name = request.form.get('product_name')
    product_price = request.form.get('product_price')

    # initializing the cart if it doesn't exist
    if 'cart' not in session:
        session['cart'] = []
    
    # adding the product to the cart
    session['cart'].append({
        'id': product_id,
        'name': product_name,
        'price': product_price
    })
    
    # updating the cart counter
    session['cart_count'] = len(session['cart'])

    flash(f'Added {product_name} to cart!')
    return redirect(request.referrer)

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    session.clear()  # Clear the session
    logout_user()  # Log out the user
    return redirect(url_for('login'))

@app.route('/discounts')
@login_required
def discounts():
    access_token = get_kroger_token(client_id, client_secret)
    search_url = "https://api.kroger.com/v1/products"
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    
    # Fetch products with discount or promo
    params = {
        'filter.term': 'on sale',  # Filters for items on sale
        'filter.limit': 10  # Number of items to display
    }

    response = requests.get(search_url, headers=headers, params=params)

    if response.status_code == 200:
        products = []
        kroger_data = response.json().get('data')
        
        for product in kroger_data:
            # Handle missing price fields safely using get()
            item = product['items'][0] if product.get('items') else {}
            price = item.get('price', {})
            promo_price = price.get('promo', 'N/A')  # Default to 'N/A' if missing still trouble with this check with free time
            regular_price = price.get('regular', 'N/A')  # Default to 'N/A' if missing
            
            product_info = {
                'name': product.get('description', 'No description'),
                'price': promo_price,
                'original_price': regular_price,
                'imageUrl': product['images'][0]['sizes'][0]['url'] if product.get('images') else '/static/img/default_product.png'
            }
            products.append(product_info)
        
        return render_template('discounts.html', products=products)
    else:
        return jsonify({"error": "Error fetching discounted products"}), 500


# Function to retrieve the cart count to use in templates
@app.context_processor
def cart_counter():
    cart_count = session.get('cart_count', 0)
    return {'cart_count': cart_count}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
