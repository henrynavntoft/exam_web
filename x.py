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

class HTTPException(Exception):
    def __init__(self, default_message, status_code, custom_message=None):
        # Combine the default message and the custom message if provided
        if custom_message:
            self.full_message = f"{default_message}: {custom_message}"
        else:
            self.full_message = default_message
        super().__init__(self.full_message)
        self.status_code = status_code
    def __str__(self):
        return f"{self.status_code} - {self.full_message}"

class BadRequest(HTTPException):
    def __init__(self, custom_message=None):
        super().__init__("Bad request", 400, custom_message)

class Unauthorized(HTTPException):
    def __init__(self, custom_message=None):
        super().__init__("Unauthorized", 401, custom_message)

class Forbidden(HTTPException):
    def __init__(self, custom_message=None):
        super().__init__("Forbidden", 403, custom_message)

class NotFound(HTTPException):
    def __init__(self, custom_message=None):
        super().__init__("Not found", 404, custom_message)

class InternalServerError(HTTPException):
    def __init__(self, custom_message=None):
        super().__init__("Internal server error", 500, custom_message)


###########################################################################################
def handle_exception(ex):
    if isinstance(ex, BadRequest):
        response.status = ex.status_code
        message = str(ex)
    elif isinstance(ex, Unauthorized):
        response.status = ex.status_code
        message = str(ex)
    elif isinstance(ex, Forbidden):
        response.status = ex.status_code
        message = str(ex)
    elif isinstance(ex, NotFound):
        response.status = ex.status_code
        message = str(ex)
    elif isinstance(ex, InternalServerError):
        response.status = ex.status_code
        message = str(ex)
    else:
        response.status = 500
        message = "System under maintenance"
        print(ex)  # Log the unexpected exception for debugging

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
        raise InternalServerError(str(ex))


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
        raise Unauthorized("You must be logged in to do that")
    return user


############################## 
def validate_user_has_rights_to_item(user, item_pk):
    try:
        database = db()
        q = database.execute("SELECT * FROM items WHERE item_pk = ?", (item_pk,))
        item = q.fetchone()

        if user['user_pk'] == item['item_owner_fk'] or user['user_role'] == 'admin':
            return True
        else:
            raise Forbidden("You do not have the rights to do that")
    except sqlite3.Error as e:
            raise InternalServerError(f"Database error: {e}")
    except HTTPException as e:
            raise e
    except Exception as e:
            raise BadRequest(str(e))
    

##############################
def validate_user_has_rights_to_image(user, image_url):
    try:
        database = db()
        q = database.execute("SELECT * FROM item_images WHERE image_url = ?", (image_url,))
        image = q.fetchone()

        if not image:
            raise NotFound("Image not found")

        item = database.execute("SELECT * FROM items WHERE item_pk = ?", (image['item_fk'],)).fetchone()
        if not item:
            raise NotFound("Item not found")

        if user['user_pk'] == item['item_owner_fk'] or user['user_role'] == 'admin':
            return True
        else:
            raise Forbidden("You do not have the rights to do that")
    except sqlite3.Error as e:
        raise InternalServerError(f"Database error: {e}")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise BadRequest(str(e))
    



########################################################################################### USER VALIDATION
############################## USER_PK VALIDATION

USER_PK_LEN = 32
USER_PK_REGEX = "^[a-f0-9]{32}$"

def validate_user_pk():
    user_pk = request.forms.get("user_pk", "").strip()
    if not re.match(USER_PK_REGEX, user_pk):
        raise BadRequest("user_pk invalid")
    return user_pk

 
############################## USER_EMAIL VALIDATION

EMAIL_MAX = 100
EMAIL_REGEX = "^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$"

def validate_user_email():
    user_email = request.forms.get("user_email", "").strip()
    if not re.match(EMAIL_REGEX, user_email):
        raise BadRequest("email invalid")
    if len(user_email) > EMAIL_MAX:
        raise BadRequest(f"email must be less than {EMAIL_MAX} characters")
    return user_email

############################## USER_USERNAME VALIDATION

USER_USERNAME_MIN = 2
USER_USERNAME_MAX = 20
USER_USERNAME_REGEX = "^[a-zA-Z]{2,20}$"

def validate_user_username():
    user_username = request.forms.get("user_username", "").strip()
    if not re.match(USER_USERNAME_REGEX, user_username):
        raise BadRequest(f"username must be between {USER_USERNAME_MIN} and {USER_USERNAME_MAX} characters, and contain only letters")
    return user_username

############################## USER_FIRST_NAME VALIDATION

FIRST_NAME_MIN = 2
FIRST_NAME_MAX = 20

def validate_user_first_name():
    user_first_name = request.forms.get("user_first_name", "").strip()
    if not re.match(USER_USERNAME_REGEX, user_first_name):
        raise BadRequest(f"First name must be between {FIRST_NAME_MIN} and {FIRST_NAME_MAX} characters, and contain only letters.")
    return user_first_name


############################## USER_LAST_NAME VALIDATION

LAST_NAME_MIN = 2
LAST_NAME_MAX = 20

def validate_user_last_name():
    user_last_name = request.forms.get("user_last_name", "").strip()
    if not re.match(USER_USERNAME_REGEX, user_last_name):
        raise BadRequest(f"Last name must be between {LAST_NAME_MIN} and {LAST_NAME_MAX} characters, and contain only letters.")
    return user_last_name

############################## USER_PASSWORD VALIDATION
USER_PASSWORD_MIN = 6
USER_PASSWORD_MAX = 50
USER_PASSWORD_REGEX = "^.{6,50}$"

def validate_user_password():
    user_password = request.forms.get("user_password", "").strip()
    if not re.match(USER_PASSWORD_REGEX, user_password):
        raise BadRequest(f"Password must be between {USER_PASSWORD_MIN} and {USER_PASSWORD_MAX} characters.")
    return user_password

############################## USER_CONFIRM_PASSWORD VALIDATION

def validate_user_confirm_password():
    user_password = request.forms.get("user_password", "").strip()
    user_confirm_password = request.forms.get("user_confirm_password", "").strip()
    if user_password != user_confirm_password:
        raise BadRequest("Password and confirm password do not match.")
    return user_confirm_password


############################## USER_ROLE VALIDATION
CUSTOMER_ROLE = "customer"
PARTNER_ROLE = "partner"

def validate_user_role():
    user_role = request.forms.get("user_role", "").strip()
    if user_role != CUSTOMER_ROLE and user_role != PARTNER_ROLE:
        raise BadRequest(f"The role '{user_role}' is neither '{CUSTOMER_ROLE}' nor '{PARTNER_ROLE}'")
    return user_role


########################################################################################### ITEM VALIDATION

############################## ITEM_PK VALIDATION
ITEM_PK_LEN = 32
ITEM_PK_REGEX = "^[a-f0-9]{32}$"

def validate_item_pk():
    item_pk = request.forms.get("item_pk", "").strip()
    if not re.match(ITEM_PK_REGEX, item_pk):
        raise BadRequest("Item pk invalid")
    return item_pk

############################## ITEM_NAME VALIDATION
ITEM_NAME_MIN = 6
ITEM_NAME_MAX = 50
ITEM_NAME_REGEX = "^.{6,50}$"

def validate_item_name():
    item_name = request.forms.get("item_name", "").strip()
    if not re.match(ITEM_NAME_REGEX, item_name):
        raise BadRequest(f"Property name must be between {ITEM_NAME_MIN} and {ITEM_NAME_MAX} characters.")
    return item_name

############################## ITEM_PRICE VALIDATION
ITEM_PRICE_MIN = 1
ITEM_PRICE_MAX = 99999999
ITEM_PRICE_REGEX = "^\d{1,8}(\.\d{1,2})?$" 

def validate_item_price_per_night():
    item_price_per_night = request.forms.get("item_price_per_night", "").strip()
    if not re.match(ITEM_PRICE_REGEX, item_price_per_night):
        raise BadRequest(f"Price must be a number between {ITEM_PRICE_MIN} and {ITEM_PRICE_MAX} digits.")
    return item_price_per_night

############################## ITEM_DESCRIPTION VALIDATION
ITEM_DESCRIPTION_MIN = 6
ITEM_DESCRIPTION_MAX = 200
ITEM_DESCRIPTION_REGEX = "^.{6,200}$"

def validate_item_description():
    item_description = request.forms.get("item_description", "").strip()
    if not re.match(ITEM_DESCRIPTION_REGEX, item_description):
        raise BadRequest(f"Description must be between {ITEM_DESCRIPTION_MIN} and {ITEM_DESCRIPTION_MAX} characters.")
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
        raise BadRequest(f"No images uploaded. Must upload between {ITEM_IMAGES_MIN} and {ITEM_IMAGES_MAX} images.")
    
    if len(item_images) < ITEM_IMAGES_MIN or len(item_images) > ITEM_IMAGES_MAX:
        raise BadRequest(f"Invalid number of images, must be between {ITEM_IMAGES_MIN} and {ITEM_IMAGES_MAX}")

    allowed_extensions = {'.png', '.jpg', '.jpeg', '.webp'}
    for image in item_images:
        # Check if the filename is empty
        if not image.filename:
            raise BadRequest("Image file name is empty")
        
        # Check the image extension
        if pathlib.Path(image.filename).suffix.lower() not in allowed_extensions:
            raise BadRequest("Invalid image extension")

        # Read the file into memory and check its size
        file_in_memory = BytesIO(image.file.read())
        if len(file_in_memory.getvalue()) > ITEM_IMAGE_MAX_SIZE:
            raise BadRequest("Image size exceeds the maximum allowed size of 5MB")

        # Go back to the start of the file for further operations
        image.file.seek(0)

    return item_images


########################################################################################### EMAILS

SENDER_EMAIL = "henrylnavntoft@gmail.com"

############################## VERIFY USER EMAIL
def send_verification_email(from_email, to_email, verification_id):
    try:

        message = MIMEMultipart()
        message["To"] = from_email
        message["From"] = to_email
        message["Subject"] = 'Testing my email to verify'

        try:
            import production #type: ignore
            base_url = "https://henrynavntoft.pythonanywhere.com"
        except:
            base_url =   "http://0.0.0.0"


        email_body= f""" 
                        <!DOCTYPE html>
                        <html lang="en">
                        <head>
                            <meta charset="UTF-8" />
                            <meta
                            name="viewport"
                            content="width=device-width, initial-scale=1.0"
                            />
                            <title>Verification Email</title>
                        </head>
                        <body>
                            <h1>You need to verify your account</h1>
                            <a href="{base_url}/activate_user/{verification_id}">Activate user </a>
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
        print(ex)
        return "error"
    


############################## RESET PASSWORD EMAIL
def send_password_reset_email(from_email, to_email, user_pk):
    try:
        message = MIMEMultipart()
        message["To"] = from_email
        message["From"] = to_email
        message["Subject"] = 'Password Reset'
        
        try:
            import production #type: ignore
            base_url = "https://henrynavntoft.pythonanywhere.com"
        except:
            base_url =   "http://0.0.0.0"


        email_body= f""" 
                        <!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Reset Password Email</title>
</head>

<body>
    <h1>Reset Your Password</h1>
    <p>Click the link below to reset your password:</p>
    <a href="{base_url}/reset_password/{user_pk}">Reset Password</a>
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
        server.login(email, password)
        server.sendmail(from_email, to_email, message.as_string())
        server.quit()
    except Exception as ex:
        print(ex)
        return "error"
    


############################## CONFIRM DELETE EMAIL
def send_confirm_delete(from_email, to_email, user_pk):
    try:
        message = MIMEMultipart()
        message["To"] = from_email
        message["From"] = to_email
        message["Subject"] = 'Your profile has been deleted'


        email_body= f""" 
                        <!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Your profile has been deleted</title>
</head>

<body>
    <h1>Your profile has been deleted</h1>
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
        server.login(email, password)
        server.sendmail(from_email, to_email, message.as_string())
        server.quit()
    except Exception as ex:
        print(ex)
        return "error"


############################## USER BLOCKED EMAIL
def user_blocked(from_email, to_email, user_pk):
    try:
        message = MIMEMultipart()
        message["To"] = from_email
        message["From"] = to_email
        message["Subject"] = 'Your profile has been blocked'
        email_body= f""" 
                    <!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Your user has been blocked</title>
</head>

<body>
    <h1>Your user has been blocked</h1>

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
        server.login(email, password)
        server.sendmail(from_email, to_email, message.as_string())
        server.quit()
    except Exception as ex:
        print(ex)
        return "error"
    


############################## USER UNBLOCKED EMAIL
def user_unblocked(from_email, to_email, user_pk):
    try:
        message = MIMEMultipart()
        message["To"] = from_email
        message["From"] = to_email
        message["Subject"] = 'Your profile has been unblocked'
        email_body = f"""
        <!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Your user has been unblocked</title>
</head>

<body>
    <h1>Your user has been unblocked</h1>

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
        server.login(email, password)
        server.sendmail(from_email, to_email, message.as_string())
        server.quit()
    except Exception as ex:
        print(ex)
        return "error"

############################## ITEM BLOCKED EMAIL
def item_blocked (from_email, to_email, item_pk):
    try:
        message = MIMEMultipart()
        message["To"] = from_email
        message["From"] = to_email
        message["Subject"] = 'Your property has been blocked'
        email_body = f"""
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Your item has been blocked</title>
</head>

<body>
    <h1>Your item has been blocked</h1>

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
        server.login(email, password)
        server.sendmail(from_email, to_email, message.as_string())
        server.quit()
    except Exception as ex:
        print(ex)
        return "error"



############################## ITEM UNBLOCKED EMAIL
def item_unblocked (from_email, to_email, item_pk):
    try:
        message = MIMEMultipart()
        message["To"] = from_email
        message["From"] = to_email
        message["Subject"] = 'Your property has been unblocked'
        email_body = f"""
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Your item has been unblocked</title>
</head>

<body>
    <h1>Your item has been unblocked</h1>

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
        server.login(email, password)
        server.sendmail(from_email, to_email, message.as_string())
        server.quit()
    except Exception as ex:
        print(ex)
        return "error"



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
        print("#"*50)
        print(ex)
    finally:
        pass