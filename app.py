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
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mail import Mail, Message
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from flask import g


# First we are going to initialize the Flask app
app = Flask(__name__)
app.secret_key = b'\xef\xd4\x16\x98h\xc6\xdd\xc3\xc6\xce\x02\xd6@o\x8a|\x08\x1c\xd6\\X{\xeex'
csrf = CSRFProtect(app)  # Enable CSRF protection
# Configure Flask-Mail using environment variables
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() in ['true', '1', 'yes']
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

# Initialize Flask-Mail
mail = Mail(app)

import requests

sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
def send_direct_email(to_email):
    url = "https://api.sendgrid.com/v3/mail/send"
    headers = {
        "Authorization": f"Bearer {os.getenv('SENDGRID_API_KEY')}",
        "Content-Type": "application/json"
    }
    data = {
        "personalizations": [
            {
                "to": [{"email": to_email}],
                "dynamic_template_data": {
                    "reset_url": "http://127.0.0.1:5000/reset-password",  # Guys this is temporary url for local reset
                    "username": to_email  
                }
            }
        ],
        "from": {"email": "kgawrinauth1@pride.hofstra.edu"},
        "template_id": "d-9c2c93acfa0e40cbbeea3cf01582af1b"  # our custom template using the sendgrid api we made
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(data))
    print("Direct API call status:", response.status_code)
    print("Response text:", response.text)


@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password_page():
    if request.method == 'POST':
        email = request.form.get('email')
        new_password = request.form.get('new_password')
        
       
        users = read_users()
        

        for username, user_info in users.items():
            if user_info.get('email') == email:
               
                user_info['password'] = new_password
                write_users(users)  
                flash('Password updated successfully!', 'success')
                return redirect(url_for('login'))
        
        flash('Email not found. Please check and try again.', 'danger')


    return render_template('reset_password_updated.html')

# We created a file to store user data (this simulates a database using mysql lite) x
USER_FILE = 'user_storage.json'

# Our Kroger API credentials 
client_id = 'kevingawrinauth-b1629c2310698a009e85d726fbc0e9aa8264849196508842534'
client_secret = 'fpfEnrPkQnQcWGySAoig8G6Up1ZosRbV8u0LrKSd'

app.secret_key = b'\xef\xd4\x16\x98h\xc6\xdd\xc3\xc6\xce\x02\xd6@o\x8a|\x08\x1c\xd6\\X{\xeex'
def load_user_storage():
    try:
        # Load and return the user data from user_Storage.json
        with open("user_storage.json", "r") as f:
            users = json.load(f)
            print("Users loaded successfully:", users)  # Debugging line
            return users
    except FileNotFoundError:
        print("Error: user_storage.json file not found.")
        return {}
    except json.JSONDecodeError:
        print("Error: user_storage.json is not a valid JSON file.")
        return {}

@app.context_processor
def inject_username():
    user_id = session.get("user_id")
    if user_id:
        users = load_user_storage()  # Load users from JSON file
        user = users.get(user_id)
        if user:
            return {"username": user.get("name", user_id)}
    return {"username": "Guest"}


# Initialize Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)
def get_kroger_token(client_id, client_secret):
    token_url = "https://api.kroger.com/v1/connect/oauth2/token"
    data = {
        'grant_type': 'client_credentials',
        'scope': 'product.compact'
    }
    auth = (client_id, client_secret)
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    response = requests.post(token_url, headers=headers, data=data, auth=auth)

    # Log full response for debugging
    print("Token Response Status Code:", response.status_code)
    print("Token Response Text:", response.text)

    # Check for JSON format response
    if response.status_code == 200:
        try:
            return response.json().get('access_token')
        except ValueError:
            # In case JSON decoding fails
            raise Exception("Error decoding JSON response while fetching access token.")
    else:
        # Handle error case explicitly
        raise Exception("Error fetching access token: Response Code " + str(response.status_code) + ", Response Text: " + response.text)

@app.route('/locations')
def fetch_locations():
    # Get access token
    access_token = get_kroger_token(client_id, client_secret)
    location_url = "https://api.kroger.com/v1/locations"
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    params = {
        'filter.radiusInMiles': 50,  # Adjusted radius
        'filter.limit': 250          # Limit to 250 locations
    }
    # Make the API call
    response = requests.get(location_url, headers=headers, params=params)
    
    # Logging response for debugging
    print("Status Code:", response.status_code)
    print("Response Text:", response.text)

    # Check and parse response
    if response.status_code == 200:
        locations = response.json().get('data', [])
        return render_template('index.html', locations=locations)
    else:
        flash("Error fetching locations.", "danger")
        return redirect(url_for('home'))

# Disable CSRF for testing
app.config['WTF_CSRF_ENABLED'] = False
# implemented a helper functions to manage user data in a file
def read_users(source='regular'):
    if source and not os.path.exists(USER_FILE):
        file_path = 'google_accounts.json'
    else:
        file_path = 'user_storage.json'
    with open(file_path, 'r') as file:
        return json.load(file)
def read_user(username):
    users = read_users()
    return users.get(username)

def write_users(users,source='regular'):
    file_path = 'google_accounts.json' if source == 'google' else 'user_storage.json'
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            try:
                existing_users = json.load(file)  # Load existing data
            except json.JSONDecodeError:
                existing_users = {}  
    else:
        existing_users = {} 
    
    existing_users.update(users)

    with open(file_path, 'w') as file:
        json.dump(existing_users, file, indent=4)

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
    
@app.route('/update_user', methods=['POST'])
@login_required
def update_user():
    # Get current user's ID and read their data
    username = current_user.id
    users = read_users()
    
    if username in users:
        # Update user information from form data
        users[username]['name'] = request.form['name']
        users[username]['email'] = request.form['email']
        users[username]['phone'] = request.form['phone']
        users[username]['address'] = request.form['address']
        
        # Write updated user data back to JSON file
        write_users(users)
        
        flash("User details updated successfully!", "success")
    else:
        flash("User not found.", "danger")
    
    return redirect(url_for('settings'))


@app.route('/orderhistory')
@login_required
def orderhistory():
    # Sample order data with renamed attribute to avoid conflict
    order_history = [
        {
            "date": "2024-10-12",
            "order_items": [
                {"name": "Sample Item 1", "price": 5.00},
                {"name": "Sample Item 2", "price": 7.50}
            ],
            "total_price": 12.50
        },
        {
            "date": "2024-10-13",
            "order_items": [
                {"name": "Sample Item 3", "price": 3.00},
                {"name": "Sample Item 4", "price": 6.50}
            ],
            "total_price": 9.50
        }
    ]

    return render_template('orderhistory.html', order_history=order_history)


@app.route('/settings')
@login_required
def settings():
    users = read_users()
    user_data = users.get(current_user.id, {})
    return render_template('settings.html', user_data=user_data)

@app.route('/login', methods=['GET', 'POST'], endpoint='login')
def login():
    form = LoginForm()  # Use LoginForm for the login form
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        # Load users from JSON file
        users = read_users()
        if not users:
            print("Error: No users loaded from user_storage.json.")
            return "User data not loaded. Check user_storage.json.", 500

        # Check user credentials
        if username in users and users[username]['password'] == password:
            user = User(username)  # Create a user object
            login_user(user)  # Log in the user

            # Load the user's cart and calculate the cart count
            cart_data = read_cart(username)
            session['user_id'] = username  # Store user ID in session
            session['cart_count'] = sum(item.get('quantity', 1) for item in cart_data['cart_items'])  # Calculate total quantity
            session.modified = True  # Ensure session is saved

            flash('Login successful!', 'success')
            return redirect(url_for('home'))  # Redirect to home or desired page
        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html', form=form)

@app.route('/save_for_later/<int:index>', methods=['POST'])
@login_required
def save_for_later(index):
    username = session.get('user_id')

    if username:
        # Retrieve the user's data (cart_items and saved_items) from JSON
        user_data = read_cart(username)
        cart = user_data.get('cart_items', [])
        saved_items = user_data.get('saved_items', [])

        # Ensure index is valid before moving the item
        if 0 <= index < len(cart):
            item = cart.pop(index)  # Remove the item from cart
            saved_items.append(item)  # Add it to saved items

            # Update the user's data in the JSON file
            write_cart(username, {'cart_items': cart, 'saved_items': saved_items})

            # Recalculate cart counter based on remaining items in the cart
            session['cart_count'] = sum(item.get('quantity', 1) for item in cart)
            session.modified = True  # Mark session as modified

            flash("Item saved for later.", "info")
        else:
            flash("Item not found in cart.", "danger")
    else:
        flash("User not logged in.", "danger")

    return redirect(url_for('view_cart'))

@app.route('/move_to_cart/<int:index>', methods=['POST'])
@login_required
def move_to_cart(index):
    user_id = session.get("user_id")
    user_data = read_cart(user_id)
    cart = user_data.get('cart_items', [])
    saved_items = user_data.get('saved_items', [])
    if 0 <= index < len(saved_items):
        item = saved_items.pop(index)
        cart.append(item)
        write_cart(user_id, {"cart_items": cart, "saved_items": saved_items})
        session['cart_count'] = sum(item['quantity'] for item in cart)
        flash("Item moved back to cart.", "success")
    return redirect(url_for('view_cart'))


# our guest login route
@app.route('/guest_login')
def guest_login():
    # automatically log in as a guest
    guest_user = User('guest')
    login_user(guest_user)
    return redirect(url_for('home'))  # should allow us redirect to home after guest login


@app.route('/api/product/<product_id>', methods=['GET'])
def get_product(product_id):
    access_token = get_kroger_token(client_id, client_secret)
    search_url = f"https://api.kroger.com/v1/products/{product_id}"
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}

    response = requests.get(search_url, headers=headers)
    if response.status_code == 200:
        product = response.json().get('data')
        if product:
            return jsonify(product)
    return jsonify({"error": "Product not found"}), 404

FAVORITES_FILE = "favorites.json"

def read_favorites():
    if os.path.exists(FAVORITES_FILE):
        with open(FAVORITES_FILE, 'r') as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                print("Error reading favorites file: malformed JSON.")
                return []
    return []

def write_favorites(favorites):
    with open(FAVORITES_FILE, 'w') as file:
        json.dump(favorites, file, indent=4)

@app.route('/toggle_favorite', methods=['POST'])
def toggle_favorite():
    data = request.get_json()

    # Ensure required fields are present
    required_fields = ['name', 'price', 'image_url']
    for field in required_fields:
        if not data.get(field):
            print(f"Missing or empty field: {field}")
            return jsonify({"message": f"Missing field: {field}", "status": "error"}), 400

    favorites = read_favorites()
    item_exists = any(fav['name'] == data['name'] for fav in favorites)

    # Toggle the favorite item based on the name
    if item_exists:
        favorites = [fav for fav in favorites if fav['name'] != data['name']]
        status = "removed"
    else:
        favorites.append({
            'name': data['name'],
            'price': data['price'],
            'image_url': data['image_url']
        })
        status = "added"

    # Write updated favorites to file
    write_favorites(favorites)
    return jsonify({"message": f"Favorite {status} successfully", "status": status})


@app.route('/get_favorites', methods=['GET'])
def get_favorites():
    favorites = read_favorites()
    return jsonify(favorites)

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

@app.route('/forgot-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        # Get the email entered in the form
        email = request.form.get('email')
        print(f"Email entered for reset: {email}")

        # Load the users and search for the email in the JSON structure
        users = read_users()
        user_found = False
        for username, user_data in users.items():
            if user_data.get('email') == email:
                user_found = True
                send_direct_email(email)
                flash('Password reset instructions have been sent to your email.', 'info')
                break

        if not user_found:
            flash('Email address not found.', 'danger')

        # Redirect to the login page or another confirmation page
        return redirect(url_for('login'))

    # Render the forgot password page for GET requests
    return render_template('forgot_password.html')

@app.route('/')
@login_required
def home():
    selected_location = read_selected_location()  # Get the selected location from locations.json
    locations = get_locations()  # Fetch all available locations

    form = LogoutForm()
    username = "Guest" if current_user.id == 'guest' else current_user.id

    # Pass selected_location to the index.html template
    return render_template('index.html', username=username, form=form, locations=locations, selected_location=selected_location)

@app.route('/favorites')
@login_required
def view_favorites():
    favorites = read_favorites()  # Retrieve all favorite items directly
    return render_template('favorites.html', favorites=favorites)

def get_locations():
    access_token = get_kroger_token(client_id, client_secret)
    location_url = "https://api.kroger.com/v1/locations"
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    params = {'filter.radiusInMiles': 50}
    response = requests.get(location_url, headers=headers, params=params)
    return response.json().get('data', []) if response.status_code == 200 else []

import os
import json

LOCATION_FILE = 'locations.json'

def read_selected_location():
    if not os.path.exists(LOCATION_FILE):
        return None
    with open(LOCATION_FILE, 'r') as file:
        data = json.load(file)
    return data.get('selected_location', None)

def write_selected_location(location_id):
    with open(LOCATION_FILE, 'w') as file:
        json.dump({'selected_location': location_id}, file)
import json
import os

CART_FILE = "cart.json"
import os
import json

CART_FILE = 'cart.json'  # File to store cart data

# Helper function to read the cart from the file
def read_cart(user_id):
    """Read cart and saved items for a specific user."""
    if os.path.exists(CART_FILE):
        with open(CART_FILE, 'r') as file:
            try:
                data = json.load(file)  # Load all cart data
                user_cart = data.get(user_id, {})  # Get cart for specific user
                return {
                    'cart_items': user_cart.get('cart_items', []),  # Ensure cart_items is a list
                    'saved_items': user_cart.get('saved_items', [])  # Ensure saved_items is a list
                }
            except json.JSONDecodeError:
                print("Error decoding JSON from cart file.")
    # Return empty structure if file doesn't exist or user has no cart
    return {'cart_items': [], 'saved_items': []}

# Helper function to write the cart to the file
def write_cart(user_id, cart):
    """Write cart and saved items for a specific user."""
    data = {}
    # Load existing cart data if the file exists
    if os.path.exists(CART_FILE):
        with open(CART_FILE, 'r') as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                print("Error decoding JSON. Overwriting file.")
    # Update the user's cart
    data[user_id] = cart
    # Save the updated data back to the file
    with open(CART_FILE, 'w') as file:
        json.dump(data, file, indent=4)

def get_user_cart(username):
    """Retrieve the cart for a specific user from the JSON data."""
    cart_data = read_cart(username)  # Pass `username` to read_cart to get specific user's data
    return cart_data

def add_item_to_cart(username, item):
    """Add an item to the user's cart in the JSON data."""
    cart_data = read_cart()
    user_cart = cart_data.get(username, [])

    # Check if item is already in the cart; update quantity if so
    for existing_item in user_cart:
        if existing_item['name'] == item['name']:
            existing_item['quantity'] += item['quantity']
            break
    else:
        # If not found, add new item
        user_cart.append(item)

    # Save updated cart data
    cart_data[username] = user_cart
    write_cart(cart_data)

def remove_item_from_cart(username, item_name):
    """Remove an item from the user's cart in the JSON data."""
    cart_data = read_cart(username)  # Retrieve the user's specific cart directly from cart.json
    
    # Ensure we have a valid dictionary and user cart exists
    if isinstance(cart_data, dict):
        user_cart = cart_data.get(username, [])

        # Filter out the item to remove
        user_cart = [item for item in user_cart if item['name'] != item_name]
        
        # Update the user's cart in the overall cart data and save to cart.json
        cart_data[username] = user_cart
        write_cart(username, user_cart)

@app.route('/add_to_cart', methods=['POST'])
@login_required
def add_to_cart():
    user_id = session.get("user_id")
    if not user_id:
        flash("User not logged in.", "danger")
        return redirect(url_for('login'))

    # Retrieve product details from the form
    product_name = request.form.get('product_name')
    product_price = request.form.get('product_price')
    product_image = request.form.get('product_image')
    category = request.form.get('category')  # For redirect after adding to cart
    product_quantity = request.form.get('product_quantity', 1)  # Default to 1 if not provided

    # Validate and convert product_price to float
    try:
        product_price = float(product_price)
    except (ValueError, TypeError):
        product_price = 0.0  # Default to 0.0 if invalid
        print(f"Warning: Invalid price for {product_name}. Defaulting to 0.0.")

    # Validate and convert product_quantity to int
    try:
        product_quantity = int(product_quantity)
    except (ValueError, TypeError):
        product_quantity = 1  # Default to 1 if invalid
        print(f"Warning: Invalid quantity for {product_name}. Defaulting to 1.")

    # Load the user's cart data from cart.json
    cart_data = read_cart(user_id)

    # Ensure cart_items is a list
    if not isinstance(cart_data.get('cart_items'), list):
        cart_data['cart_items'] = []

    cart = cart_data['cart_items']

    # Check if the product already exists in the cart
    item_exists = False
    for item in cart:
        if item.get('name') == product_name:
            item['quantity'] += product_quantity  # Update quantity based on form input
            item_exists = True
            break

    # If the product is new, add it to the cart
    if not item_exists:
        cart.append({
            'name': product_name,
            'price': product_price,
            'image': product_image,
            'quantity': product_quantity  # Set quantity from form input
        })

    # Save the updated cart back to cart.json
    write_cart(user_id, cart_data)

    # Update the session cart count based on the total quantity of items
    session['cart_count'] = sum(item['quantity'] for item in cart)
    session.modified = True  # Ensure session updates are saved

    flash(f"{product_quantity}x {product_name} added to your cart.", "success")
    return redirect(url_for('get_products', category=category))


from urllib.parse import unquote

@app.route('/remove_item/<int:index>', methods=['POST'])
@login_required
def remove_item(index):
    username = session.get('user_id')

    if username:
        # Retrieve the user's cart data (cart_items and saved_items)
        user_data = read_cart(username)
        cart = user_data.get('cart_items', [])

        # Validate index range
        if 0 <= index < len(cart):
            cart.pop(index)  # Remove the item from the cart
            write_cart(username, {'cart_items': cart, 'saved_items': user_data.get('saved_items', [])})

            # Update cart count in session (sum of quantities)
            session['cart_count'] = sum(item.get('quantity', 1) for item in cart)
            session.modified = True
            flash("Item removed from cart.", "success")
        else:
            flash("Item not found in cart.", "danger")
    else:
        flash("User not logged in.", "danger")

    return redirect(url_for('view_cart'))


@app.route('/update_quantity/<int:index>/<operation>', methods=['POST'])
@login_required
def update_quantity(index, operation):
    user_id = session.get('user_id')  # Get the user_id from the session

    if user_id:
        # Retrieve the user's cart data from JSON
        user_cart_data = read_cart(user_id)

        # Get cart_items from the retrieved cart data
        cart_items = user_cart_data.get('cart_items', [])

        # Ensure the index is within bounds
        if 0 <= index < len(cart_items):
            item = cart_items[index]  # Access the specific cart item

            # Handle quantity updates based on the operation
            if operation == 'increase':
                item['quantity'] += 1  # Increment the quantity
            elif operation == 'decrease' and item['quantity'] > 1:
                item['quantity'] -= 1  # Decrement the quantity only if > 1

            # Update the user's cart data in JSON
            user_cart_data['cart_items'] = cart_items  # Update the cart_items
            write_cart(user_id, user_cart_data)

            # Recalculate the total cart count for the session
            session['cart_count'] = sum(
                item.get('quantity', 1) for item in cart_items
            )  # Default to 1 if quantity is missing

            # Mark the session as modified to ensure updates are saved
            session.modified = True

            flash("Item quantity updated successfully.", "success")
        else:
            flash("Invalid item index. Please try again.", "danger")
    else:
        flash("User not found. Please log in again.", "danger")

    return redirect(url_for('view_cart'))


@app.route('/cart')
@login_required
def view_cart():
    user_id = session.get("user_id")
    user_data = read_cart(user_id)  # Retrieve user data (cart_items and saved_items) from JSON

    # Extract cart_items and initialize saved_items if missing
    cart = user_data.get('cart_items', [])
    saved_items = user_data.get('saved_items', [])

    # Ensure all prices in the cart are valid floats
    for item in cart:
        try:
            item['price'] = float(item.get('price', 0))  # Handle missing prices by defaulting to 0
        except (ValueError, TypeError):
            item['price'] = 0.00

    # Calculate the total amount in the cart
    total_amount = sum(item['price'] * item['quantity'] for item in cart)

    # Render the template, passing both cart and saved_items
    return render_template(
        'cart.html',
        cart=cart,
        total_amount=total_amount,
        saved_items=saved_items
    )


@app.context_processor
def inject_cart_count():
    return {'cart_count': session.get('cart_count', 0)}

# Logout route (POST only with CSRF protection)
@app.route('/logout', methods=['POST'])
@login_required
def logout():
    session.clear()  # Explicitly clear the session
    logout_user()  # Log out the user
    
    return redirect(url_for('login'))




@app.route('/products/<category>')
@login_required
def get_products(category):
    # Get the saved location ID
    location_id = read_selected_location()  # Ensure this reads from locations.json

    if not location_id:
        flash("Please select a store location to view prices.", "warning")
        return redirect(url_for('home'))

    try:
        access_token = get_kroger_token(client_id, client_secret)
    except Exception as e:
        flash("Error fetching access token.", "danger")
        return redirect(url_for('home'))

    search_url = "https://api.kroger.com/v1/products"
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}

    # Get the search query from request arguments (for free-text search)
    query = request.args.get('query', '').strip()
    page = int(request.args.get('page', 1))  # Default to page 1 if not provided

    # Map category to search terms if no custom query is provided
    if query:
        search_term = query  # Use the query as the search term
    else:
        category_mapping = {
            "Vegetables": "vegetables",
            "Fruits": "fruits",
            "Meats": "meat",
            "Frozen": "frozen",
            "Dairy": "dairy",
            "Bread": "bread",
            "Canned": "canned food",
            "Snacks": "snack",
            "Drinks": "beverage",
            "PersonalCare": "personal care"
        }
        search_term = category_mapping.get(category, "")

    # Set up page modifications
    params = {
        'filter.term': search_term,
        'filter.locationId': location_id,
        'filter.limit': 50,  # Page size set to 50
        'filter.start': (page - 1) * 50  # Offset calculated based on page number
    }

    response = requests.get(search_url, headers=headers, params=params)

    if response.status_code == 200:
        products = response.json().get('data', [])

        # Validate product data
        validated_products = []
        for product in products:
            product_data = {
                'description': product.get('description', 'No description'),
                'images': product.get('images', [{'sizes': [{'url': '/static/img/default_image.png'}]}]),
                'items': product.get('items', [{'price': {'regular': 'N/A'}}]),
                'delivery_date': product.get('delivery_date', 'Tomorrow'),
            }

            # Ensure all nested data exists
            if not product_data['images'][0].get('sizes'):
                product_data['images'][0]['sizes'] = [{'url': '/static/img/default_image.png'}]

            validated_products.append(product_data)

        has_next_page = len(validated_products) == 50  # Check if there's another page

        return render_template(
            'products.html',
            products=validated_products,
            category=category if not query else "Search Results",
            page=page,
            has_next_page=has_next_page,
            query=query
        )
    else:
        flash("Error fetching products.", "danger")
        return redirect(url_for('home'))


# Function to retrieve the cart count to use in templates
@app.context_processor
def cart_counter():
    cart_count = session.get('cart_count', 0)
    return {'cart_count': cart_count}

@app.route('/discounts', methods=['GET'])
@app.route('/discounts/<string:category>', methods=['GET'])
@login_required
def discounts(category=None):
    """
    Render discounts.html for general discounts or category_discounts.html for specific categories.
    """
    try:
        access_token = get_kroger_token(client_id, client_secret)
    except Exception as e:
        flash("Error fetching access token.", "danger")
        return redirect(url_for('home'))

    search_url = "https://api.kroger.com/v1/products"
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}

    # Fetch the selected store location
    location_id = read_selected_location()
    if not location_id:
        flash("No store location selected. Please select a location first.", "warning")
        return redirect(url_for('home'))

    # Set API filter parameters
    params = {
        'filter.locationId': location_id,
        'filter.limit': 50,
       
    }

    # Add filter for category-specific discounts or general discounts
    if category:
        params['filter.term'] = category.lower()  # Filter by category
    else:
        params['filter.term'] = 'on sale'  # General filter for discounted items

    # Fetch discounted products
    response = requests.get(search_url, headers=headers, params=params)

    if response.status_code == 200:
        products = []
        kroger_data = response.json().get('data', [])

        for product in kroger_data:
            item = product['items'][0] if product.get('items') else {}
            price = item.get('price', {})
            promo_price = price.get('promo', 'N/A')
            regular_price = price.get('regular', 'N/A')

            product_info = {
                'name': product.get('description', 'No description'),
                'price': promo_price,
                'original_price': regular_price,
                'imageUrl': product['images'][0]['sizes'][0]['url'] if product.get('images') else '/static/img/default_product.png'
            }
            products.append(product_info)

        # Render the correct template
        if category:
            return render_template('category_discounts.html', category=category.capitalize(), products=products)
        else:
            return render_template('discounts.html', products=products)
    else:
        flash("Error fetching discounted products. Please try again.", "danger")
        return redirect(url_for('home'))





@app.route('/checkout')
@login_required
def checkout():
    user_id = session.get("user_id")

    # Retrieve the cart directly from cart.json using user_id
    user_data = read_cart(user_id)
    cart_items = user_data.get("cart_items", []) if isinstance(user_data, dict) else []

    # Calculate subtotal and other amounts
    try:
        subtotal = sum(float(item.get('price', 0)) * item.get('quantity', 0) for item in cart_items)
        total_quantity = sum(item.get('quantity', 0) for item in cart_items)
    except (ValueError, TypeError, KeyError):
        subtotal = 0
        total_quantity = 0

    sales_tax_rate = 0.08625
    sales_tax = subtotal * sales_tax_rate
    total_cost = subtotal + sales_tax

    return render_template(
        'checkout.html',
        cart_items=cart_items,
        subtotal=subtotal,
        sales_tax=sales_tax,
        total_cost=total_cost,
    )

def send_order_confirmation_email(recipient_email, name, address, city, zip_code):
    # Set up SendGrid API URL and headers
    url = "https://api.sendgrid.com/v3/mail/send"
    headers = {
        "Authorization": f"Bearer {os.getenv('SENDGRID_API_KEY')}"
,  # Replace with your SendGrid API Key
        "Content-Type": "application/json"
    }
    
    # Email data, including the template ID and recipient information
    data =data = {
    "personalizations": [
        {
            "to": [{"email": recipient_email}],
            "dynamic_template_data": {
                "customer_name": name,
                "address": address,
                "city": city,
                "zip_code": zip_code,
            }
        }
    ],
    "from": {"email": "kgawrinauth1@pride.hofstra.edu"},
    "template_id": "d-54cbef9f0d5a46c3a5c99a01efb9c0de",
    "subject": "Order Confirmation"
}
    # Send the request
    response = requests.post(url, headers=headers, json=data)
    
    # Check the response
    if response.status_code == 202:
        print("Order confirmation email sent successfully!")
    else:
        print("Failed to send email. Status Code:", response.status_code)
        print("Response:", response.json())

@app.route('/process_checkout', methods=['POST'])
@login_required
def process_checkout():
    # Retrieve form data
    name = request.form.get('name')
    address = request.form.get('address')
    city = request.form.get('city')
    zip_code = request.form.get('zip')

    user_id = session.get("user_id")

    # Try to get the user's email from the session
    to_email = session.get("user_email")
    if not to_email:
        users = load_user_storage()
        if user_id and user_id in users:
            to_email = users[user_id].get("email")

    print(f"User email for order confirmation: {to_email}")

    # Send confirmation email if email is present
    if to_email:
        send_order_confirmation_email(to_email, name, address, city, zip_code)

    # Clear the cart in `cart.json`
    cart_data = read_cart(user_id)
    cart_data['cart_items'] = []  # Empty the user's cart
    write_cart(user_id, cart_data)  # Save changes back to the file

    # Clear session cart count
    session['cart_count'] = 0
    session.modified = True

    flash("Thank you for your order! A confirmation email has been sent.", "success")
    return redirect(url_for('home'))


def read_selected_location():
    if not os.path.exists('locations.json'):
        return None
    with open('locations.json', 'r') as file:
        data = json.load(file)
    return data.get('selected_location', None)

@app.route('/account_info')
@login_required
def account_info():
    users = read_users()
    user_data = users.get(current_user.id, {})
    return render_template('account_info.html', user_data=user_data)

@app.route('/set_location')
def set_location():
    location_id = request.args.get('location_id')
    
    if location_id:
        write_selected_location(location_id)  # Update the JSON file with the new location
        flash("Location updated successfully.", "success")
    else:
        flash("No location ID provided.", "danger")
    
    return redirect(request.referrer or url_for('home'))

@app.route('/loyalty_rewards')
@login_required
def loyalty_rewards():
    # Example data; ideally, fetch this from a database
    rewards_info = {
        "points": 1200,
        "tier": "Gold",
        "next_tier_points": 3000,
        "next_tier_name": "Platinum",
        "points_to_next_tier": 3000 - 1200  # Calculate remaining points needed
    }
    rewards_history = [
        {"date": "2024-10-15", "description": "Redeemed 10% off coupon", "points_used": 100},
        {"date": "2024-09-30", "description": "Free delivery voucher", "points_used": 50},
        {"date": "2024-09-20", "description": "5% off on next purchase", "points_used": 80},
    ]
    return render_template(
        'loyalty_rewards.html',
        rewards_info=rewards_info,
        rewards_history=rewards_history
    )

@app.context_processor
def inject_locations():
    # Only fetch locations if not already in the session
    if 'locations' not in session:
        try:
            access_token = get_kroger_token(client_id, client_secret)
            location_url = "https://api.kroger.com/v1/locations"
            headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
            params = {'filter.radiusInMiles': 50, 'filter.limit': 900}
            response = requests.get(location_url, headers=headers, params=params)
            
            if response.status_code == 200:
                session['locations'] = response.json().get('data', [])
            else:
                session['locations'] = []
        except Exception as e:
            session['locations'] = []
            print(f"Error fetching locations: {e}")
    
    return {'locations': session.get('locations', [])}

@app.route('/faq')
def faq():
    return render_template('faq.html')

@app.route('/translate', methods=['POST'])
def translate_text():
    data = request.get_json()
    text = data.get('text', '')
    target_language = data.get('target', 'es')  # Default to Spanish

    if text:
        result = translate_client.translate(text, target_language=target_language)
        return jsonify(result['translatedText'])
    return jsonify({"error": "No text provided"}), 400

@app.context_processor
def inject_selected_location_and_locations():
    selected_location = read_selected_location()  # Retrieves selected location if stored
    
    # Access token and Kroger API endpoint
    access_token = get_kroger_token(client_id, client_secret)
    location_url = "https://api.kroger.com/v1/locations"
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    params = {
        'filter.radiusInMiles': 50,
        'filter.limit': 350
    }

    # Fetch locations
    try:
        response = requests.get(location_url, headers=headers, params=params)
        if response.status_code == 200:
            locations = response.json().get('data', [])
        else:
            print(f"Error fetching locations: {response.status_code} - {response.text}")
            locations = []  # Fallback to empty list if fetch fails
    except Exception as e:
        print("Exception occurred while fetching locations:", e)
        locations = []  # Fallback in case of exception

    # Inject selected location and locations data into the template context
    return {'selected_location': selected_location, 'locations': locations}

GOOGLE_CLIENT_ID = '948980706830-8ff2bi5o0lupforj4u8h5odjs66krb1p.apps.googleusercontent.com'
GOOGLE_CLIENT_SECRET = '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'
CONF_URL = 'https://accounts.google.com/.well-known/openid-configuration'

from authlib.integrations.flask_client import OAuth
import uuid

# Initialize OAuth
oauth = OAuth(app)
oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url=CONF_URL,
    client_kwargs={'scope': 'openid email profile'}
)


# Google Authentication
@app.route('/google/')
def google():
    # Redirect to google_auth function
    nonce = uuid.uuid4().hex
    session['nonce'] = nonce
    redirect_uri = url_for('google_auth', _external=True)
    return oauth.google.authorize_redirect(redirect_uri,nonce=nonce)

@app.route('/google/auth/')
def google_auth():
    token = oauth.google.authorize_access_token()
    nonce = session.pop('nonce', None)

    if nonce is None:
        flash("Invalid session. Please try logging in again.", "error")
        return redirect(url_for('login'))

    user_info = oauth.google.parse_id_token(token, nonce=nonce)
    if user_info:
        user_id = user_info.get('email')  # Use email as the unique identifier
        users = read_users()  # Load users from user_storage.json

        # If the user doesn't exist, create a new entry in user_storage.json
        if user_id not in users:
            users[user_id] = {
                "password": None,  # Google accounts don't use passwords
                "name": user_info.get('name', ""),
                "email": user_info.get('email', ""),
                "phone": "",  # Default empty phone field
                "address": "",  # Default empty address field
            }
            write_users(users)  # Save to user_storage.json

        # Log the user in
        user = User(user_id)
        login_user(user)
        session['user_id'] = user_id

        # Initialize cart count in session
        user_data = read_cart(user_id)  # Read the user's cart
        cart = user_data.get('cart_items', [])

        # Validate that cart is a list of dictionaries
        if isinstance(cart, list) and all(isinstance(item, dict) for item in cart):
            session['cart_count'] = sum(item.get('quantity', 1) for item in cart)
        else:
            session['cart_count'] = 0  # Default to 0 if cart structure is invalid

        flash(f"Welcome, {user_info.get('name')}!", "success")
        return redirect(url_for('home'))
    else:
        flash("Failed to retrieve user information from Google.", "danger")
        return redirect(url_for('login'))

    
@app.route('/saved_items')
@login_required
def view_saved_items():
    user_id = session.get("user_id")
    cart_data = read_cart(user_id)
    saved_items = cart_data.get("saved_items", [])

    return render_template('saved_items.html', saved_items=saved_items)






if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)