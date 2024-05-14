import pathlib
# import sys
# sys.path.insert(0, str(pathlib.Path(__file__).parent.resolve())+"/bottle")
from bottle import request, response, template
import re
import sqlite3
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib


ITEMS_PER_PAGE = 2
COOKIE_SECRET = "41ebeca46f3b-4d77-a8e2-554659075C6319a2fbfb-9a2D-4fb6-Afcad32abb26a5e0"


##############################
def dict_factory(cursor, row):
    col_names = [col[0] for col in cursor.description]
    return {key: value for key, value in zip(col_names, row)}

##############################

def db():
    db = sqlite3.connect(str(pathlib.Path(__file__).parent.resolve())+"/company.db")  
    db.row_factory = dict_factory
    return db


##############################
def no_cache():
    response.add_header("Cache-Control", "no-cache, no-store, must-revalidate")
    response.add_header("Pragma", "no-cache")
    response.add_header("Expires", 0)    


##############################
def validate_user_logged():
    user = request.get_cookie("user", secret=COOKIE_SECRET)
    if user is None: raise Exception("user must login", 400)
    return user


############################## TODO: DO WE NEED THIS???

""" def validate_logged():
    # Prevent logged pages from caching
    response.add_header("Cache-Control", "no-cache, no-store, must-revalidate")
    response.add_header("Pragma", "no-cache")
    response.add_header("Expires", "0")  
    user_id = request.get_cookie("id", secret = COOKIE_SECRET_KEY)
    if not user_id: raise Exception("***** user not logged *****", 400)
    return user_id """


########################################################################################### USER VALIDATION



############################## TODO: WE NEED TO VALIDATE IDS/PKS

USER_PK_LEN = 32
USER_PK_REGEX = "^[a-f0-9]{32}$"

def validate_user_pk():
	error = f"user_pk invalid"
	user_pk = request.forms.get("user_pk", "").strip()      
	if not re.match(USER_PK_REGEX, user_pk): raise Exception(error, 400)
	return user_pk


##############################

EMAIL_MAX = 100
EMAIL_REGEX = "^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$"

def validate_user_email():
    error = f"email invalid"
    user_email = request.forms.get("user_email", "").strip()
    if not re.match(EMAIL_REGEX, user_email): raise Exception(error, 400)
    return user_email

##############################

USER_USERNAME_MIN = 2
USER_USERNAME_MAX = 20
USER_USERNAME_REGEX = "^[a-zA-Z]{2,20}$"

def validate_user_username():
    error = f"username {USER_USERNAME_MIN} to {USER_USERNAME_MAX} lowercase english letters"
    user_username = request.forms.get("user_username", "").strip()
    if not re.match(USER_USERNAME_REGEX, user_username): raise Exception(error, 400)
    return user_username

##############################

FIRST_NAME_MIN = 2
FIRST_NAME_MAX = 20

def validate_user_first_name():
    error = f"name {FIRST_NAME_MIN} to {FIRST_NAME_MAX} characters"
    user_first_name = request.forms.get("user_first_name", "").strip()
    if not re.match(USER_USERNAME_REGEX, user_first_name): raise Exception(error, 400)
    return user_first_name

##############################

LAST_NAME_MIN = 2
LAST_NAME_MAX = 20

def validate_user_last_name():
  error = f"last_name {LAST_NAME_MIN} to {LAST_NAME_MAX} characters"
  user_last_name = request.forms.get("user_last_name", "").strip()
  if not re.match(USER_USERNAME_REGEX, user_last_name): raise Exception(error, 400)
  return user_last_name

##############################

USER_PASSWORD_MIN = 6
USER_PASSWORD_MAX = 50
USER_PASSWORD_REGEX = "^.{6,50}$"

##############################

USER_PASSWORD_MIN = 6
USER_PASSWORD_MAX = 50
USER_PASSWORD_REGEX = "^.{6,50}$"

def validate_user_password():
    error = f"password {USER_PASSWORD_MIN} to {USER_PASSWORD_MAX} characters"
    user_password = request.forms.get("user_password", "").strip()
    if not re.match(USER_PASSWORD_REGEX, user_password): raise Exception(error, 400)
    return user_password

##############################

def validate_user_confirm_password():
  error = f"password and confirm_password do not match"
  user_password = request.forms.get("user_password", "").strip()
  user_confirm_password = request.forms.get("user_confirm_password", "").strip()
  if user_password != user_confirm_password: raise Exception(error, 400)
  return user_confirm_password


##############################
CUSTOMER_ROLE = "customer"
PARTNER_ROLE = "partner"

def validate_user_role():
    user_role = request.forms.get("user_role", "").strip()
    error = f"The role ###{user_role}### is neither {CUSTOMER_ROLE} or {PARTNER_ROLE}"
    if user_role != CUSTOMER_ROLE and user_role != PARTNER_ROLE:
        raise Exception(error, 400)
    return user_role


########################################################################################### ITEMS/PROPERTIES VALIDATION


#TODO: finsih validation
############################## 
ITEM_PK_LEN = 32
ITEM_PK_REGEX = "^[a-f0-9]{32}$"

def validate_item_pk():
	error = f"item pk invalid"
	item_pk = request.forms.get("item_pk", "").strip()      
	if not re.match(ITEM_PK_REGEX, item_pk): raise Exception(error, 400)
	return item_pk





##############################
ITEM_NAME_MIN = 6
ITEM_NAME_MAX = 50
ITEM_NAME_REGEX = "^.{6,50}$"

def validate_item_name():
  error = f"Property name {ITEM_NAME_MIN} to {ITEM_NAME_MAX} characters"
  item_name = request.forms.get("item_name", "").strip()
  if not re.match(ITEM_NAME_REGEX, item_name): raise Exception(error, 400)
  return item_name

##############################
ITEM_PRICE_MIN = 1
ITEM_PRICE_MAX = 99999999
ITEM_PRICE_REGEX = "^\d{1,8}(\.\d{1,2})?$" 

def validate_item_price_per_night():
  error = f"Price must be between {ITEM_PRICE_MIN} and {ITEM_PRICE_MAX} digits"
  item_price_per_night = request.forms.get("item_price_per_night", "").strip()
  if not re.match(ITEM_PRICE_REGEX, item_price_per_night): raise Exception(error, 400)
  return item_price_per_night

##############################
ITEM_DESCRIPTION_MIN = 6
ITEM_DESCRIPTION_MAX = 200
ITEM_DESCRIPTION_REGEX = "^.{6,200}$"

def validate_item_description():
  error = f"Description {ITEM_DESCRIPTION_MIN} to {ITEM_DESCRIPTION_MAX} characters"
  item_description = request.forms.get("item_description", "").strip()
  if not re.match(ITEM_DESCRIPTION_REGEX, item_description): raise Exception(error, 400)
  return item_description

############################## TODO: Fix this, we need to validate the image size and number of images
ITEM_IMAGES_MIN = 1
ITEM_IMAGES_MAX = 5
ITEM_IMAGE_MAX_SIZE = 1024 * 1024 * 5 # 5MB


def validate_item_images():
    error_num = "Number of images must be between 1 and 5."
    item_images = request.files.getall("item_images")

    if not item_images or len(item_images) < 1 or len(item_images) > 5:
        raise Exception(400, error_num)

    return item_images



########################################################################################### EMAILS

SENDER_EMAIL = "henrylnavntoft@gmail.com"

##############################
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
    


##############################
def send_password_reset_email(from_email, to_email, user_pk):
    try:
        message = MIMEMultipart()
        message["To"] = from_email
        message["From"] = to_email
        message["Subject"] = 'Password Reset'
        email_body = template("views/password_reset_email", key=user_pk)
 
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
    


##############################
def send_confirm_delete(from_email, to_email, user_pk):
    try:
        message = MIMEMultipart()
        message["To"] = from_email
        message["From"] = to_email
        message["Subject"] = 'Your profile has been deleted'
        email_body = template("views/deleted_profile_email", key=user_pk)
 
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


##############################
def user_blocked(from_email, to_email, user_pk):
    try:
        message = MIMEMultipart()
        message["To"] = from_email
        message["From"] = to_email
        message["Subject"] = 'Your profile has been blocked'
        email_body = template("views/blocked_profile_email", key=user_pk)
 
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
    
##############################
def user_unblocked(from_email, to_email, user_pk):
    try:
        message = MIMEMultipart()
        message["To"] = from_email
        message["From"] = to_email
        message["Subject"] = 'Your profile has been unblocked'
        email_body = template("views/unblocked_profile_email", key=user_pk)
 
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

##############################
def item_blocked (from_email, to_email, item_pk):
    try:
        message = MIMEMultipart()
        message["To"] = from_email
        message["From"] = to_email
        message["Subject"] = 'Your property has been blocked'
        email_body = template("views/blocked_item_email", key=item_pk)
 
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



##############################
def item_unblocked (from_email, to_email, item_pk):
    try:
        message = MIMEMultipart()
        message["To"] = from_email
        message["From"] = to_email
        message["Subject"] = 'Your property has been unblocked'
        email_body = template("views/unblocked_item_email", key=item_pk)
 
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









