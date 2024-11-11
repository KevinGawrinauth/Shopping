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
        with open("user_Storage.json", "r") as f:
            users = json.load(f)
            print("Users loaded successfully:", users)  # Debugging line
            return users
    except FileNotFoundError:
        print("Error: user_Storage.json file not found.")
        return {}
    except json.JSONDecodeError:
        print("Error: user_Storage.json is not a valid JSON file.")
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
def read_users():
    if not os.path.exists(USER_FILE):
        return {}
    with open(USER_FILE, 'r') as file:
        return json.load(file)
def read_user(username):
    users = read_users()
    return users.get(username)

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

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()  # Use LoginForm for the login form
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        # Load users from JSON file
        users = read_users()
        if not users:
            print("Error: No users loaded from user_Storage.json.")
            return "User data not loaded. Check user_Storage.json.", 500

        # Check user credentials
        if username in users and users[username]['password'] == password:
            user = User(username)
            login_user(user)  # Log in the user

            # Store only essential data in the session
            session['user_id'] = username
            session['cart_count'] = sum(item.get('quantity', 1) for item in read_cart(username))  # Calculate and store only the count
            session.modified = True  # Ensure session updates are saved

            return redirect(url_for('home'))
        else:
            flash('Invalid username or password')

    return render_template('login.html', form=form)



@app.route('/save_for_later/<int:index>', methods=['POST'])
@login_required
def save_for_later(index):
    username = session.get('user_id')

    if username:
        # Retrieve the user's cart from JSON and saved items from the session
        cart = get_user_cart(username)
        saved_items = session.get('saved_items', [])

        # Ensure index is valid before moving the item
        if 0 <= index < len(cart):
            item = cart.pop(index)  # Remove the item from cart
            saved_items.append(item)  # Add it to saved items

            # Update both cart in JSON and session data
            write_cart(username, cart)  # Persist the updated cart to JSON
            session['saved_items'] = saved_items  # Update saved items in session

            # Mark session as modified to save changes
            session.modified = True

            flash("Item saved for later.", "info")
        else:
            flash("Item not found in cart.", "danger")

    return redirect(url_for('view_cart'))



@app.route('/move_to_cart/<int:index>', methods=['POST'])
@login_required
def move_to_cart(index):
    username = session.get('user_id')

    if username:
        cart = get_user_cart(username)  # Get cart from JSON
        saved_items = session.get('saved_items', [])

        try:
            # Move the item from saved items back to cart
            item = saved_items.pop(index)
            cart.append(item)

            # Update both cart and saved items
            write_cart(username, cart)  # Persist updated cart to JSON
            session['saved_items'] = saved_items  # Update saved items in session
            session.modified = True

            flash("Item moved back to cart.", "success")
        except IndexError:
            flash("Item not found in saved items.", "danger")

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

# Helper function to read the cart from the file
def read_cart(user_id):
    if os.path.exists(CART_FILE):
        with open(CART_FILE, 'r') as file:
            data = json.load(file)
            return data.get(user_id, [])
    return []

# Helper function to write the cart to the file
def write_cart(user_id, cart):
    data = {}
    if os.path.exists(CART_FILE):
        with open(CART_FILE, 'r') as file:
            data = json.load(file)
    
    data[user_id] = cart  # Update the user's cart data
    
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
    product_name = request.form.get('product_name')
    product_price = request.form.get('product_price')
    product_image = request.form.get('product_image')
    category = request.form.get('category')  # Capture the category from the form

    # Validate and convert product_price
    try:
        product_price = float(product_price)
    except (ValueError, TypeError):
        # If product_price is invalid, set it to 0.0 and log a warning
        product_price = 0.0
        print(f"Warning: Invalid price for {product_name}. Defaulting to 0.0.")

    # Load the user's cart from the JSON file
    cart = read_cart(user_id)

    # Check if product is already in cart and update quantity
    item_exists = False
    for item in cart:
        if item['name'] == product_name:
            item['quantity'] += 1
            item_exists = True
            break

    # If it's a new item, add it to the cart
    if not item_exists:
        cart.append({
            'name': product_name,
            'price': product_price,
            'image': product_image,
            'quantity': 1
        })

    # Save updated cart to JSON file
    write_cart(user_id, cart)

    # Update cart count in the session based on the total quantity of items
    session['cart_count'] = sum(item['quantity'] for item in cart)
    session.modified = True  # Mark session as modified

    return redirect(url_for('get_products', category=category))




from urllib.parse import unquote

from urllib.parse import unquote

@app.route('/remove_item/<int:index>', methods=['POST'])
@login_required
def remove_item(index):
    username = session.get('user_id')

    if username:
        # Retrieve the user's cart from cart.json
        user_cart = get_user_cart(username)

        # Ensure the index is within range before removing the item
        if 0 <= index < len(user_cart):
            user_cart.pop(index)  # Remove item at the specified index
            write_cart(username, user_cart)  # Update the cart in cart.json

            # Update the cart count in the session
            session['cart_count'] = len(user_cart)
        else:
            flash("Item not found in cart.", "danger")

    flash("Item removed from cart.", "success")
    return redirect(url_for('view_cart'))





@app.route('/update_quantity/<int:index>/<operation>', methods=['POST'])
@login_required
def update_quantity(index, operation):
    username = session.get('user_id')

    if username:
        user_cart = get_user_cart(username)

        # Ensure index is valid
        if 0 <= index < len(user_cart):
            item = user_cart[index]
            
            # Increase or decrease quantity based on operation
            if operation == 'increase':
                item['quantity'] += 1
            elif operation == 'decrease' and item['quantity'] > 1:
                item['quantity'] -= 1

            # Update the cart in cart.json
            write_cart(username, user_cart)
            
            # Update cart count in session if needed
            session['cart_count'] = sum(item.get('quantity', 1) for item in user_cart)
        else:
            flash("Item not found in cart.", "danger")

    return redirect(url_for('view_cart'))



@app.route('/cart')
@login_required
def view_cart():
    user_id = session.get("user_id")
    cart = read_cart(user_id)  # Load cart from JSON file

    # Ensure all prices are valid floats and handle missing prices
    for item in cart:
        try:
            item['price'] = float(item.get('price', 0))  # Handle missing prices by defaulting to 0
        except (ValueError, TypeError):
            item['price'] = 0.00

    # Calculate the total amount in the cart
    total_amount = sum(item['price'] * item['quantity'] for item in cart)

    return render_template('cart.html', cart=cart, total_amount=total_amount)





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


@app.route('/discounts')
@login_required
def discounts():
    access_token = get_kroger_token(client_id, client_secret)
    search_url = "https://api.kroger.com/v1/products"
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    
    # Fetch products with discount or promo
    params = {
        'filter.term': 'on sale',  # Filters for items on sale
        'filter.limit': 5  # Number of items to display
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
    
    # Route to handle the search functionality with category filtering

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
        

    # Set up pagination parameters
    params = {
        'filter.term': search_term,
        'filter.locationId': location_id,
        'filter.limit': 50,  # Page size set to 50
        'filter.start': (page - 1) * 50  # Offset calculated based on page number
    }

    response = requests.get(search_url, headers=headers, params=params)

    if response.status_code == 200:
        products = response.json().get('data', [])
        has_next_page = len(products) == 50  # Check if there's another page

        return render_template(
            'products.html',
            products=products,
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


@app.route('/checkout')
@login_required
def checkout():
    user_id = session.get("user_id")
    cart_items = read_cart(user_id)  # Retrieve the cart directly from cart.json using user_id

    # Calculate subtotal and other amounts
    subtotal = sum(float(item['price']) * item['quantity'] for item in cart_items)
    total_quantity = sum(item['quantity'] for item in cart_items)
    sales_tax_rate = 0.08625
    sales_tax = subtotal * sales_tax_rate
    total_cost = subtotal + sales_tax

    return render_template('checkout.html', cart_items=cart_items, subtotal=subtotal, sales_tax=sales_tax, total_cost=total_cost)

    
app.config['MAIL_SERVER'] = 'smtp.sendgrid.net'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'apikey'  # SendGrid requires 'apikey' as the username
app.config['MAIL_PASSWORD'] = os.getenv('SENDGRID_API_KEY')  # Set your API key here
app.config['MAIL_DEFAULT_SENDER'] = 'kgawrinauth1@pride.hofstra.edu'




mail = Mail(app)
def send_order_confirmation_email(to_email, name, address, city, zip_code):
    try:
        msg = Message(
            "Order Confirmation",
            recipients=[to_email],
            html=f"""
                <h2>Order Confirmation</h2>
                <p>Hello {name},</p>
                <p>Thank you for your order!</p>
                <p><strong>Shipping Address:</strong><br>
                {address}, {city}, {zip_code}</p>
                <p>We appreciate your business!</p>
            """
        )
        mail.send(msg)
        print("Order confirmation email sent successfully!")
    except Exception as e:
        print("Error while sending email:", e)


@app.route('/process_checkout', methods=['POST'])
@app.route('/process_checkout', methods=['POST'])
@login_required
def process_checkout():
    # Retrieve form data
    name = request.form.get('name')
    address = request.form.get('address')
    city = request.form.get('city')
    zip_code = request.form.get('zip')
    to_email = session.get("user_email")  # Assumes user's email is stored in session

    # Clear the cart after checkout
    session.pop('cart', None)
    session['cart_count'] = 0

    # Send order confirmation email if email is present
    if to_email:
        send_order_confirmation_email(to_email, name, address, city, zip_code)
        flash("Thank you for your order! A confirmation email has been sent.", "success")
    else:
        flash("Order placed successfully, but no email was sent due to missing email address.", "info")

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

from flask import Flask, request, jsonify
from google.cloud import translate_v2 as translate
import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/kevingawrinauth/grocery_app/rising-cable-441021-b1-337bc9fa13da.json'
translate_client = translate.Client()


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




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
