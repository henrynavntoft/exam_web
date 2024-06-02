import pathlib
from bottle import request, response
import re
import sqlite3
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import requests
from io import BytesIO

ITEMS_PER_PAGE = 2
COOKIE_SECRET = "41ebeca46f3b-4d77-a8e2-554659075C6319a2fbfb-9a2D-4fb6-Afcad32abb26a5e0"

############################################################################################
# Custom exceptions

def handle_exception(ex):
    # Default status code and message
    status_code = 500
    message = "System under maintenance"

    # Check if the exception contains a status code
    if isinstance(ex.args, tuple) and len(ex.args) == 2:
        message, status_code = ex.args
    else:
        message = str(ex)

    # Map specific status codes to more detailed messages if needed
    if status_code == 400:
        message = f"Bad request: {message}"
    elif status_code == 401:
        message = f"Unauthorized: {message}"
    elif status_code == 403:
        message = f"Forbidden: {message}"
    elif status_code == 404:
        message = f"Not found: {message}"
    elif status_code == 500:
        message = f"Internal server error: {message}"

    # Set the response status code
    response.status = status_code
    print(message)

    # Return an HTML template snippet with the error message
    return f"""
    <template mix-target="#toast">
        <div mix-ttl="3000" class="error">
            {message}
        </div>
    </template>
    """

###########################################################################################
# SQLite database connection

##############################
def dict_factory(cursor, row):
    col_names = [col[0] for col in cursor.description]
    return {key: value for key, value in zip(col_names, row)}

##############################
def db():
    try:
        db = sqlite3.connect(str(pathlib.Path(__file__).parent.resolve())+"/company.db")  
        db.row_factory = dict_factory
        return db
    except Exception as ex:
        return handle_exception(ex)


###########################################################################################
# Utility functions

##############################
def no_cache():
    response.add_header("Cache-Control", "no-cache, no-store, must-revalidate")
    response.add_header("Pragma", "no-cache")
    response.add_header("Expires", 0)    


##############################
def validate_user_logged():
    user = request.get_cookie("user", secret=COOKIE_SECRET)
    if user is None: 
        raise Exception("User not logged in", 401)
    return user

##############################
def check_user_status():
    user_status = {
        'is_logged': False,
        'is_customer': False,
        'is_admin': False,
        'is_partner': False
    }
    
    try:
        user = validate_user_logged()
        user_status['is_logged'] = True
        if user['user_role'] == 'customer':
            user_status['is_customer'] = True
        if user['user_role'] == 'admin':
            user_status['is_admin'] = True
        if user['user_role'] == 'partner':
            user_status['is_partner'] = True
    except Exception as ex:
        pass
    
    return user_status

############################## 
def validate_user_has_rights_to_item(user, item_pk):
    try:
        database = db()
        q = database.execute("SELECT * FROM items WHERE item_pk = ?", (item_pk,))
        item = q.fetchone()

        if user['user_pk'] == item['item_owner_fk'] or user['user_role'] == 'admin':
            return True
        else:
            raise Exception("You do not have the rights to do that", 403)
    except Exception as ex:
        return handle_exception(ex)
    

##############################
def validate_user_has_rights_to_image(user, image_url):
    try:
        database = db()
        q = database.execute("SELECT * FROM item_images WHERE image_url = ?", (image_url,))
        image = q.fetchone()

        if not image:
            raise Exception("Image not found", 404)

        item = database.execute("SELECT * FROM items WHERE item_pk = ?", (image['item_fk'],)).fetchone()
        if not item:
            raise Exception("Item not found", 404)

        if user['user_pk'] == item['item_owner_fk'] or user['user_role'] == 'admin':
            return True
        else:
            raise Exception("You do not have the rights to do that", 403)
    except Exception as ex:
        return handle_exception(ex)
    

###########################################################################################

############################## GROUP ITEMS WITH IMAGES
def group_items_with_images(rows):
    items = {}
    for row in rows:
        item_pk = row['item_pk']
        if item_pk not in items:
            items[item_pk] = {
                'item_pk': row['item_pk'],
                'item_name': row['item_name'],
                'item_description': row['item_description'],
                'item_splash_image': row['item_splash_image'],
                'item_price_per_night': row['item_price_per_night'],
                'item_lat': row['item_lat'],
                'item_lon': row['item_lon'],
                'item_stars': row['item_stars'],
                'item_created_at': row['item_created_at'],
                'item_updated_at': row['item_updated_at'],
                'item_deleted_at': row['item_deleted_at'],
                'item_is_blocked': row['item_is_blocked'],
                'item_is_booked': row['item_is_booked'],
                'item_images': []
            }
        if row['image_url']:
            items[item_pk]['item_images'].append(row['image_url'])

    return list(items.values())



########################################################################################### USER VALIDATION
############################## USER_PK VALIDATION

USER_PK_LEN = 32
USER_PK_REGEX = "^[a-f0-9]{32}$"

def validate_user_pk():
    user_pk = request.forms.get("user_pk", "").strip()
    if not re.match(USER_PK_REGEX, user_pk):
        raise Exception("user_pk invalid", 400)
    return user_pk

 
############################## USER_EMAIL VALIDATION

EMAIL_MAX = 100
EMAIL_REGEX = "^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$"

def validate_user_email():
    user_email = request.forms.get("user_email", "").strip()
    if not re.match(EMAIL_REGEX, user_email):
        raise Exception("email invalid", 400)
    if len(user_email) > EMAIL_MAX:
        raise Exception(f"email must be less than {EMAIL_MAX} characters", 400)
    return user_email

############################## USER_USERNAME VALIDATION

USER_USERNAME_MIN = 2
USER_USERNAME_MAX = 20
USER_USERNAME_REGEX = "^[a-zA-Z]{2,20}$"

def validate_user_username():
    user_username = request.forms.get("user_username", "").strip()
    if not re.match(USER_USERNAME_REGEX, user_username):
        raise Exception(f"username must be between {USER_USERNAME_MIN} and {USER_USERNAME_MAX} characters, and contain only letters", 400)
    return user_username

############################## USER_FIRST_NAME VALIDATION

FIRST_NAME_MIN = 2
FIRST_NAME_MAX = 20

def validate_user_first_name():
    user_first_name = request.forms.get("user_first_name", "").strip()
    if not re.match(USER_USERNAME_REGEX, user_first_name):
        raise Exception(f"First name must be between {FIRST_NAME_MIN} and {FIRST_NAME_MAX} characters, and contain only letters.", 400)
    return user_first_name


############################## USER_LAST_NAME VALIDATION

LAST_NAME_MIN = 2
LAST_NAME_MAX = 20

def validate_user_last_name():
    user_last_name = request.forms.get("user_last_name", "").strip()
    if not re.match(USER_USERNAME_REGEX, user_last_name):
        raise Exception(f"Last name must be between {LAST_NAME_MIN} and {LAST_NAME_MAX} characters, and contain only letters.", 400)
    return user_last_name

############################## USER_PASSWORD VALIDATION
USER_PASSWORD_MIN = 6
USER_PASSWORD_MAX = 50
USER_PASSWORD_REGEX = "^.{6,50}$"
# USER_PASSWORD_REGEX = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{8,}$"

def validate_user_password():
    user_password = request.forms.get("user_password", "").strip()
    if not re.match(USER_PASSWORD_REGEX, user_password):
        raise Exception(f"Password must be between {USER_PASSWORD_MIN} and {USER_PASSWORD_MAX} characters.", 400)
    return user_password

############################## USER_CONFIRM_PASSWORD VALIDATION

def validate_user_confirm_password():
    user_password = request.forms.get("user_password", "").strip()
    user_confirm_password = request.forms.get("user_confirm_password", "").strip()
    if user_password != user_confirm_password:
        raise Exception("Password and confirm password do not match.", 400)
    return user_confirm_password


############################## USER_ROLE VALIDATION
CUSTOMER_ROLE = "customer"
PARTNER_ROLE = "partner"

def validate_user_role():
    user_role = request.forms.get("user_role", "").strip()
    if user_role != CUSTOMER_ROLE and user_role != PARTNER_ROLE:
        raise Exception(f"The role '{user_role}' is neither '{CUSTOMER_ROLE}' nor '{PARTNER_ROLE}'", 400)
    return user_role


########################################################################################### ITEM VALIDATION

############################## ITEM_PK VALIDATION
ITEM_PK_LEN = 32
ITEM_PK_REGEX = "^[a-f0-9]{32}$"

def validate_item_pk():
    item_pk = request.forms.get("item_pk", "").strip()
    if not re.match(ITEM_PK_REGEX, item_pk):
        raise Exception("Item pk invalid", 400)
    return item_pk

############################## ITEM_NAME VALIDATION
ITEM_NAME_MIN = 6
ITEM_NAME_MAX = 50
ITEM_NAME_REGEX = "^.{6,50}$"

def validate_item_name():
    item_name = request.forms.get("item_name", "").strip()
    if not re.match(ITEM_NAME_REGEX, item_name):
        raise Exception(f"Property name must be between {ITEM_NAME_MIN} and {ITEM_NAME_MAX} characters.", 400)
    return item_name

############################## ITEM_PRICE VALIDATION
ITEM_PRICE_MIN = 1
ITEM_PRICE_MAX = 99999999
ITEM_PRICE_REGEX = "^\d{1,8}(\.\d{1,2})?$" 

def validate_item_price_per_night():
    item_price_per_night = request.forms.get("item_price_per_night", "").strip()
    if not re.match(ITEM_PRICE_REGEX, item_price_per_night):
        raise Exception(f"Price must be a number between {ITEM_PRICE_MIN} and {ITEM_PRICE_MAX} digits.", 400)
    return item_price_per_night

############################## ITEM_DESCRIPTION VALIDATION
ITEM_DESCRIPTION_MIN = 6
ITEM_DESCRIPTION_MAX = 200
ITEM_DESCRIPTION_REGEX = "^.{6,200}$"

def validate_item_description():
    item_description = request.forms.get("item_description", "").strip()
    if not re.match(ITEM_DESCRIPTION_REGEX, item_description):
        raise Exception(f"Description must be between {ITEM_DESCRIPTION_MIN} and {ITEM_DESCRIPTION_MAX} characters.", 400)
    return item_description

############################## ITEM_IMAGES VALIDATION 
# NOTE: When 0 images are uploaded it checks for file extenstion and shold check for number of images. So behavior is slightly wrong but works.
ITEM_IMAGES_MIN = 1
ITEM_IMAGES_MAX = 5
ITEM_IMAGE_MAX_SIZE = 1024 * 1024 * 5  # 5MB


def validate_item_images():
    item_images = request.files.getall("item_images")

    # Ensure that the number of images is within the allowed range
    if not item_images:
        raise Exception(f"No images uploaded. Must upload between {ITEM_IMAGES_MIN} and {ITEM_IMAGES_MAX} images.", 400)
    
    if len(item_images) < ITEM_IMAGES_MIN or len(item_images) > ITEM_IMAGES_MAX:
        raise Exception(f"Invalid number of images, must be between {ITEM_IMAGES_MIN} and {ITEM_IMAGES_MAX}", 400)

    allowed_extensions = {'.png', '.jpg', '.jpeg', '.webp'}
    for image in item_images:
        # Check if the filename is empty
        if not image.filename:
            raise Exception("Image file name is empty", 400)
        
        # Check the image extension
        extension = pathlib.Path(image.filename).suffix.lower()
        if extension == "":
            raise Exception("No images provided", 400)
        if extension not in allowed_extensions:
            raise Exception("Invalid image extension", 400)

        # Read the file into memory and check its size
        file_in_memory = BytesIO(image.file.read())
        if len(file_in_memory.getvalue()) > ITEM_IMAGE_MAX_SIZE:
            raise Exception("Image size exceeds the maximum allowed size of 5MB", 400)

        # Go back to the start of the file for further operations
        image.file.seek(0)

    return item_images

############################## 
def validate_item_images_no_image_ok():
    item_images = request.files.getall("item_images")
    print("Item images:", item_images)

    # Ensure that the number of images is within the allowed range when combined with existing images
    if len(item_images) == 0:
        return []

    allowed_extensions = {'.png', '.jpg', '.jpeg', '.webp'}
    for image in item_images:
        # Check if the filename is empty
        if not image.filename:
            return "no-image"

        # Check the image extension
        extension = pathlib.Path(image.filename).suffix.lower()
        if extension == "":
            return "no-image"
        if extension not in allowed_extensions:
            raise Exception("Invalid image extension", 400)

        # Read the file into memory and check its size
        file_in_memory = BytesIO(image.file.read())
        if len(file_in_memory.getvalue()) > ITEM_IMAGE_MAX_SIZE:
            raise Exception("Image size exceeds the maximum allowed size of 5MB", 400)

        # Go back to the start of the file for further operations
        image.file.seek(0)

    return item_images



########################################################################################### EMAILS

SENDER_EMAIL = "henrylnavntoft@gmail.com"

try:
    import production #type: ignore
    base_url = "https://henrynavntoft.pythonanywhere.com"
except:
    base_url =   "http://0.0.0.0"

############################## VERIFY USER EMAIL
def send_verification_email(from_email, to_email, verification_id):
    try:

        message = MIMEMultipart()
        message["To"] = from_email
        message["From"] = to_email
        message["Subject"] = 'Verify your account'

        email_body = f""" 
            <html>
            <body>
                <h1>Welcome to BottleBnB!</h1>
                <p>Thank you for signing up. To activate your account, please click the link below:</p>
                <a href="{base_url}/activate_user/{verification_id}">Activate Account</a>
            </body>
            </html>
        """
 
        messageText = MIMEText(email_body, 'html')
        message.attach(messageText)
 
        email = from_email
        password = 'jglkhstighdhpreb'
 
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.ehlo('Gmail')
        server.starttls()
        server.login(email,password)
        from_email = from_email
        to_email  = to_email
        server.sendmail(from_email,to_email,message.as_string())
 
        server.quit()
    except Exception as ex:
        return handle_exception(ex)
    


############################## RESET PASSWORD EMAIL
def send_password_reset_email(from_email, to_email, user_pk):
    try:
        message = MIMEMultipart()
        message["To"] = from_email
        message["From"] = to_email
        message["Subject"] = 'Password Reset'

        email_body = f""" 
        <body>
            <h1>Reset Your Password</h1>
            <p>Click the link below to reset your password:</p>
            <a href="{base_url}/reset_password/{user_pk}">Reset Password</a>
        </body>
        """
 
        messageText = MIMEText(email_body, 'html')
        message.attach(messageText)
 
        email = from_email
        password = 'jglkhstighdhpreb'
 
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.ehlo('Gmail')
        server.starttls()
        server.login(email, password)
        server.sendmail(from_email, to_email, message.as_string())
        server.quit()
    except Exception as ex:
        return handle_exception(ex)
    


############################## CONFIRM DELETE EMAIL
def send_confirm_delete(from_email, to_email, user_pk):
    try:
        message = MIMEMultipart()
        message["To"] = from_email
        message["From"] = to_email
        message["Subject"] = 'Your profile has been deleted'


        email_body = """
        <body>
            <h1>Your profile has been deleted</h1>
        </body>
        """
 
        messageText = MIMEText(email_body, 'html')
        message.attach(messageText)
 
        email = from_email
        password = 'jglkhstighdhpreb'
 
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.ehlo('Gmail')
        server.starttls()
        server.login(email, password)
        server.sendmail(from_email, to_email, message.as_string())
        server.quit()
    except Exception as ex:
        return handle_exception(ex)


############################## USER BLOCKED EMAIL
def user_blocked(from_email, to_email, user_pk):
    try:
        message = MIMEMultipart()
        message["To"] = from_email
        message["From"] = to_email
        message["Subject"] = 'Your profile has been blocked'
        email_body= f""" 
<body>
    <h1>Your user has been blocked</h1>

</body>
            """
 
        messageText = MIMEText(email_body, 'html')
        message.attach(messageText)
 
        email = from_email
        password = 'jglkhstighdhpreb'
 
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.ehlo('Gmail')
        server.starttls()
        server.login(email, password)
        server.sendmail(from_email, to_email, message.as_string())
        server.quit()
    except Exception as ex:
        return handle_exception(ex)


############################## USER UNBLOCKED EMAIL
def user_unblocked(from_email, to_email, user_pk):
    try:
        message = MIMEMultipart()
        message["To"] = from_email
        message["From"] = to_email
        message["Subject"] = 'Your profile has been unblocked'
        email_body = f"""

<body>
    <h1>Your user has been unblocked</h1>

</body>

        """
 
        messageText = MIMEText(email_body, 'html')
        message.attach(messageText)
 
        email = from_email
        password = 'jglkhstighdhpreb'
 
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.ehlo('Gmail')
        server.starttls()
        server.login(email, password)
        server.sendmail(from_email, to_email, message.as_string())
        server.quit()
    except Exception as ex:
        return handle_exception(ex)

############################## ITEM BLOCKED EMAIL
def item_blocked (from_email, to_email, item_pk):
    try:
        message = MIMEMultipart()
        message["To"] = from_email
        message["From"] = to_email
        message["Subject"] = 'Your property has been blocked'
        email_body = f"""

<body>
    <h1>Your item has been blocked</h1>

</body>
"""
 
        messageText = MIMEText(email_body, 'html')
        message.attach(messageText)
 
        email = from_email
        password = 'jglkhstighdhpreb'
 
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.ehlo('Gmail')
        server.starttls()
        server.login(email, password)
        server.sendmail(from_email, to_email, message.as_string())
        server.quit()
    except Exception as ex:
        return handle_exception(ex)



############################## ITEM UNBLOCKED EMAIL
def item_unblocked (from_email, to_email, item_pk):
    try:
        message = MIMEMultipart()
        message["To"] = from_email
        message["From"] = to_email
        message["Subject"] = 'Your property has been unblocked'
        email_body = f"""

<body>
    <h1>Your item has been unblocked</h1>
</body>

"""
 
        messageText = MIMEText(email_body, 'html')
        message.attach(messageText)
 
        email = from_email
        password = 'jglkhstighdhpreb'
 
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.ehlo('Gmail')
        server.starttls()
        server.login(email, password)
        server.sendmail(from_email, to_email, message.as_string())
        server.quit()
    except Exception as ex:
        return handle_exception(ex)






###########################################################################################
## ARANGODB CONNECTION

def db_arango(query):
    try:
        url = "http://arangodb:8529/_api/cursor"
        res = requests.post( url, json = query )
        print(res)
        print(res.text)
        return res.json()
    
    except Exception as ex:
        return handle_exception(ex)
    