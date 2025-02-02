# IMPORT
#########################
from bottle import default_app, get, post, put, delete, request, response, run, static_file, template
import x
import bcrypt
import json
import credentials
import git
import uuid
import time as epoch
import random
import os
from pathlib import Path


# GIT UPDATE
##############################
@post('/secret')
def git_update():
  repo = git.Repo('./exam_web')
  origin = repo.remotes.origin
  repo.create_head('main', origin.refs.main).set_tracking_branch(origin.refs.main).checkout()
  origin.pull()
  return ""


# SERVING STATIC FILES
##############################
@get("/app.css")
def _():
    return static_file("app.css", ".")


##############################
@get("/<file_name>.js")
def _(file_name):
    return static_file(file_name+".js", ".")


##############################
@get("/images/<item_splash_image>")
def _(item_splash_image):
    return static_file(item_splash_image, "images")



# ROUTES
##############################
@get("/signup")
def _():
    x.no_cache()
    return template("signup.html", title="Sign Up")


##############################
@get("/login")
def _():
    x.no_cache()
    return template("login.html", title="Login")

##############################
@get("/change_password")
def _():
    x.no_cache()
    return template("change_password.html")

##############################
@get("/logout")
def _():
    response.delete_cookie("user")
    response.status = 303
    response.set_header('Location', '/login')
    return


############################## HOME
##############################
@get("/")
def _():
    try:
        db = x.db()
        
        user_status = x.check_user_status()

        
        query = """
        SELECT * FROM item_images 
        INNER JOIN items ON item_images.item_fk = items.item_pk 
        WHERE items.item_is_blocked = 0 
        ORDER BY item_created_at
        """
        
        q = db.execute(query)

        rows = q.fetchall()
        
        items = x.group_items_with_images(rows)

        items = items[:x.ITEMS_PER_PAGE]

        return template("index.html", items=items, mapbox_token=credentials.mapbox_token, 
                        is_logged=user_status["is_logged"], is_customer=user_status["is_customer"])
    
    except Exception as ex:
         return x.handle_exception(ex)
    finally:
        if "db" in locals(): db.close()


############################## GET MORE ITEMS
############################## 
@get("/items/page/<page_number>")
def _(page_number):
    try:
        
        user_status = x.check_user_status()

        db = x.db()

        query = """
        SELECT * FROM item_images 
        INNER JOIN items ON item_images.item_fk = items.item_pk 
        WHERE items.item_is_blocked = 0 
        ORDER BY item_created_at
        """

        q = db.execute(query)

        rows = q.fetchall()
        
        items = x.group_items_with_images(rows)

        next_page = int(page_number) + 1
        
        offset = (int(page_number) - 1) * x.ITEMS_PER_PAGE

        items = items[offset:offset + x.ITEMS_PER_PAGE]

        html = ""
        
        for item in items: 
            html += template("_item", item=item, is_logged=user_status["is_logged"], is_customer=user_status["is_customer"])    
        
        btn_more = template("__btn_more", page_number=next_page)
        
        if len(items) < x.ITEMS_PER_PAGE: 
            btn_more = ""
        
        return f"""
        <template mix-target="#items" mix-bottom>
            {html}
        </template>

        <template mix-target="#more" mix-replace>
            {btn_more}
        </template>
        
        <template mix-function="mapPins">
        {json.dumps(items)}
        </template>
        """
    
    except Exception as ex:
        return x.handle_exception(ex)
    
    finally:
        if "db" in locals(): db.close()

############################## SINGLE PROPERTY
@get("/property/<item_pk>")
def _(item_pk):
    try:
        user_status = x.check_user_status()

        db = x.db()

        query = """
        SELECT * FROM item_images 
        INNER JOIN items ON item_images.item_fk = items.item_pk 
        WHERE items.item_pk = ? 
        AND items.item_is_blocked = 0
        """

        q = db.execute(query, (item_pk,))
        
        rows = q.fetchall()
        
        item = x.group_items_with_images(rows)[0]
    
        
        if not item:
            raise Exception("Item not found", 404)
        

        return template("property.html", item=item, is_logged=user_status["is_logged"], is_customer=user_status["is_customer"])
    except Exception as ex:
        return x.handle_exception(ex)
    finally:
        if "db" in locals(): db.close()


########################################################### PROFILE
############################## GET PROFILE
@get("/profile")
def _():
    try:
        x.no_cache()

        user_status = x.check_user_status()

        user = x.validate_user_logged()

        if not user_status['is_logged']:
            return

        db = x.db()

        # If user is a partner
        if user_status['is_partner']:
            query = """
            SELECT *
            FROM item_images
            INNER JOIN items ON item_images.item_fk = items.item_pk
            WHERE items.item_owner_fk = ? AND items.item_is_blocked = 0
            ORDER BY item_created_at
            """

            q = db.execute(query, (user['user_pk'],))
            
            rows = q.fetchall()
            
            items = x.group_items_with_images(rows)

            return template("profile_partner.html", is_logged=user_status['is_logged'], user=user, items=items, is_partner=user_status['is_partner'], title="Partner Profile")
        
        # If user is a customer
        if user_status['is_customer']:
            return template("profile_customer.html", is_logged=user_status['is_logged'], user=user, title="Customer Profile")
        
        # If user is an admin
        if user_status['is_admin']:
            query = """
            SELECT * FROM item_images 
            INNER JOIN items ON item_images.item_fk = items.item_pk 
            ORDER BY item_created_at
            """
            q = db.execute(query)
            
            q2 = db.execute("SELECT * FROM users WHERE user_role != 'admin'")
            
            rows = q.fetchall()
            
            users = q2.fetchall()

            items = x.group_items_with_images(rows)

            return template("profile.html", is_logged=user_status['is_logged'], items=items, user=user, users=users, is_admin=user_status['is_admin'], title="Admin Profile")

    except Exception as ex:
        response.status = 303
        response.set_header('Location', '/login')
        return

    finally:
        if "db" in locals():
            db.close()

############################## EDIT PROFILE
@put("/edit_profile")
def _():
    try:
        user = x.validate_user_logged()
        
        user_username = x.validate_user_username()
        user_first_name = x.validate_user_first_name()
        user_last_name = x.validate_user_last_name()
        user_updated_at = epoch.time()
        
        db = x.db()
        
        db.execute("UPDATE users SET user_username = ?, user_first_name = ?, user_last_name = ?, user_updated_at = ? WHERE user_pk = ?", (user_username, user_first_name, user_last_name, user_updated_at, user["user_pk"]))
        
        db.commit()

        # Spread the user and update the user information
        updated_user = {**user, "user_username": user_username, "user_first_name": user_first_name, "user_last_name": user_last_name, "user_updated_at": user_updated_at}

        try:
            import production #type: ignore
            is_cookie_https = True
        except:
            is_cookie_https = False

        response.set_cookie("user", updated_user, secret=x.COOKIE_SECRET, httponly=True, secure=is_cookie_https, path='/')

        return """
        <template mix-redirect="/profile">
        </template>
        """   
    except Exception as ex:
        response.status = 303
        response.set_header('Location', '/login')
        return
    
    finally:
        if "db" in locals(): db.close()


##############################  EDIT PASSWORD
@put("/edit_password")
def _():
    try:

        user_pk = x.validate_user_pk()
        user_password = x.validate_user_password()
        user_confrim_password = x.validate_user_confirm_password()
        user_updated_at = epoch.time()

        if user_password != user_confrim_password:
            raise Exception("Passwords do not match", 400)

        
        # this makes user_password into a byte string
        password = user_password.encode() 
        
        # Adding the salt to password
        salt = bcrypt.gensalt()
        # Hashing the password
        hashed = bcrypt.hashpw(password, salt)
        
        # Convert the hashed password to a string
        hashed_str = hashed.decode('utf-8')
        
        db = x.db()
        db.execute("UPDATE users SET user_password = ?, user_updated_at = ? WHERE user_pk = ?", (hashed_str, user_updated_at, user_pk))
        db.commit()
        
        response.delete_cookie("user")
        

        return f"""
            <template mix-target="#frm_edit_password" mix-replace>
            <div>
                <h1> Your password has been changed </h1>
                <a class="text-blue-600 underline" href="/login"> Click here to login </a>
            </div>
            </template>
            """

    except Exception as ex:
        return x.handle_exception(ex)
    
    finally:
        if "db" in locals(): db.close()


##############################
@put("/delete_profile")
def _():
    try:
        user = x.validate_user_logged()

        if user['user_role'] == 'admin':
            raise Exception("Admins cannot delete their profiles", 403)

        db = x.db()
        
        db.execute("UPDATE users SET user_deleted_at = 1 WHERE user_pk = ?", (user["user_pk"],))
        
        db.commit()

        x.send_confirm_delete(x.SENDER_EMAIL, user["user_email"], user["user_pk"])

        response.delete_cookie("user")

        return """
        <template mix-redirect="/login">
        </template>
        """
        
    except Exception as ex:
        print(ex)
        response.status = 303
        response.set_header('Location', '/login')
        return
    
    
    finally:
        if "db" in locals(): 
            db.close()



############################## SIGNUP
##############################
@post("/signup")    
def _():
    try:
        user_email = x.validate_user_email()
        user_password = x.validate_user_password()
        user_confirm_password = x.validate_user_confirm_password()
        user_username = x.validate_user_username()
        user_first_name = x.validate_user_first_name()
        user_last_name = x.validate_user_last_name()

        user_role = x.validate_user_role()

        user_pk = str(uuid.uuid4().hex)
        user_created_at = epoch.time()


        if user_password != user_confirm_password:
            raise Exception("Passwords do not match", 400)
        

        # this makes user_password into a byte string
        password = user_password.encode() 
        
        # Adding the salt to password
        salt = bcrypt.gensalt()
        # Hashing the password
        hashed = bcrypt.hashpw(password, salt)
        
        # Convert the hashed password to a string
        hashed_str = hashed.decode('utf-8')


        db = x.db()
        db.execute("INSERT INTO users (user_pk, user_username, user_first_name, user_last_name, user_email, user_password, user_role, user_created_at, user_updated_at, user_deleted_at, user_is_verified, user_is_blocked) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (user_pk, user_username, user_first_name, user_last_name, user_email, hashed_str, user_role, user_created_at, "0", "0", "0", "0"))
        db.commit()

        x.send_verification_email(x.SENDER_EMAIL, user_email, user_pk)
   
        return """
        <template mix-redirect="/login">
        </template>
        """
    
    except Exception as ex:
        return x.handle_exception(ex)
    finally:
        if "db" in locals(): db.close()


############################## Should be a put, but since we cant send mixhtml in the mail it is a get
@get("/activate_user/<id>")
def _(id):
    try:
        db = x.db()
        db.execute("UPDATE users SET user_is_verified = 1 WHERE user_pk = ?", (id,))
        db.commit()
        return template("activate_user.html")
    except Exception as ex:
        return x.handle_exception(ex)
    finally:
        if "db" in locals(): db.close()

##############################
@put("/block_user")
def _():
    try:
        user = x.validate_user_logged()
        if user['user_role'] == "admin":
            user_email = x.validate_user_email()
            user_pk = x.validate_user_pk()
            db = x.db()
            db.execute("UPDATE users SET user_is_blocked = 1 WHERE user_pk = ?", (user_pk,))
            db.commit()

            x.user_blocked(x.SENDER_EMAIL, user_email, user_pk)

            return """
            <template mix-redirect="/profile">
            </template>
            """
        else:
            raise Exception("User is not an admin", 403)
        
    except Exception as ex:
        return x.handle_exception(ex)
    finally:
        if "db" in locals(): db.close()    

##############################
@put("/unblock_user")
def _():
    try:
        user = x.validate_user_logged()
        if user['user_role'] == "admin":
            user_email = x.validate_user_email()
            user_pk = x.validate_user_pk()
            db = x.db()
            q = db.execute("UPDATE users SET user_is_blocked = 0 WHERE user_pk = ?", (user_pk,))
            db.commit()

            x.user_unblocked(x.SENDER_EMAIL, user_email, user_pk)
        
            return """
            <template mix-redirect="/profile">
            </template>
            """
        else:
            raise Exception("User is not an admin", 403)
    except Exception as ex:
        return x.handle_exception(ex)
    finally:
        if "db" in locals(): db.close()


############################## LOGIN
##############################
@post("/login")
def _():
    try:
        user_email = x.validate_user_email()
        user_password = x.validate_user_password()
        

        db = x.db()
        
        q = db.execute("SELECT * FROM users WHERE user_email = ? LIMIT 1", (user_email,))
        
        user = q.fetchone()

        if not user:
            raise Exception("User not found", 404)
        if user.get("user_is_verified") != 1:
            raise Exception("User is not verified", 403)
        if user.get("user_is_blocked") != 0:
            raise Exception("User is blocked", 403)
        if user.get("user_deleted_at") != 0:
            raise Exception("User is not found", 404)
        

        if not bcrypt.checkpw(user_password.encode(), user["user_password"].encode()): raise Exception ("Invalid credentials", 400)
        
        user.pop("user_password") # Do not put the user's password in the cookie
        
        try:
            import production #type: ignore
            is_cookie_https = True
        except:
            is_cookie_https = False   

        response.set_cookie("user", user, secret=x.COOKIE_SECRET, httponly=True, secure=is_cookie_https)
        
        return """
        <template mix-redirect="/profile">
        </template>
        """
    except Exception as ex:
        return x.handle_exception(ex)
    finally:
        if "db" in locals(): db.close()



############################## FORGOT PASSWORD
@post("/forgot_password")
def _():
    try:
        user_email = x.validate_user_email()
        db = x.db()
        q = db.execute("SELECT * FROM users WHERE user_email = ? LIMIT 1", (user_email,))
        user = q.fetchone()
        if not user:
            raise Exception("User not found", 404)
        user_pk = user["user_pk"]
        x.send_password_reset_email('henrylnavntoft@gmail.com', user_email, user_pk)
        return """
        <template mix-target="#toast">
            <div mix-ttl="3000" class="ok">
                Password reset email sent successfully
            </div>
        </template>
        """
    except Exception as ex:
        return x.handle_exception(ex)
    finally:
        if "db" in locals(): db.close()


############################## RESET PASSWORD
@get("/reset_password/<id>")
def _(id):
    try:
        db = x.db()
        q = db.execute("SELECT * FROM users WHERE user_pk = ?", (id,))
        user = q.fetchone()
        if not user:
            raise Exception("User not found", 404)
        return template("reset_password.html", user=user, id=id)
    except Exception as ex:
        print(ex)
        return x.handle_exception(ex)
    finally:
        if "db" in locals(): db.close()









############################## ITEMS
############################## ADD ITEM
@post("/add_item")
def _():
    try:
        user = x.validate_user_logged()
        if user['user_role'] != "partner":
            raise Exception("User is not a partner", 403)
        else:
            

            # User
            user_pk = user['user_pk']

            # Item
            item_pk = uuid.uuid4().hex
            item_name = x.validate_item_name()
            item_description = x.validate_item_description()
            item_price_per_night = x.validate_item_price_per_night()
            item_lat = random.uniform(55.615, 55.727)
            item_lon = random.uniform(12.451, 12.650)
            item_stars = round(random.uniform(1, 5), 2)
            item_created_at = epoch.time()
            item_updated_at = 0
            item_deleted_at = 0
            item_is_blocked = 0
            item_is_booked = 0
        

            # Images
            item_images = x.validate_item_images()

            # Initialize the first image URL for the splash image
            first_image_filename = f"{item_pk}_{uuid.uuid4().hex}.{item_images[0].filename.split('.')[-1]}"

            # Insert the property into the items table
            db = x.db()
            db.execute("INSERT INTO items (item_pk, item_name, item_description, item_splash_image, item_price_per_night, item_lat, item_lon, item_stars, item_created_at, item_updated_at, item_deleted_at, item_is_blocked, item_is_booked, item_owner_fk) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (item_pk, item_name, item_description, first_image_filename, item_price_per_night, item_lat, item_lon, item_stars, item_created_at, item_updated_at, item_deleted_at, item_is_blocked, item_is_booked, user_pk))
            db.commit()



            # Process each image, rename it, save it, and store just the filename in the database
            for image in item_images:
                filename = f"{item_pk}_{uuid.uuid4().hex}.{image.filename.split('.')[-1]}"
                try: 
                    import production #type: ignore
                    path = f"/home/henrynavntoft/exam_web/images/{filename}"
                except:
                    path = f"images/{filename}"
                
                image.save(path) # Save the image with the new filename

                # Insert the image filename into the item_images table (without path)
                db.execute("INSERT INTO item_images (item_fk, image_url) VALUES (?, ?)", (item_pk, filename))
                db.commit()

            return """
            <template mix-redirect="/profile">
            </template>
            """

    except Exception as ex:
        return x.handle_exception(ex)

    
    finally:
        if "db" in locals(): db.close()



############################## EDIT ITEM 
@put("/edit_item")
def _():
    try:
        user = x.validate_user_logged()
        item_pk = x.validate_item_pk()
        item_name = x.validate_item_name()
        item_description = x.validate_item_description()
        item_price_per_night = x.validate_item_price_per_night()
        item_updated_at = epoch.time()

        x.validate_user_has_rights_to_item(user, item_pk)

        db = x.db()

        # Update item details
        db.execute("""UPDATE items
        SET item_name = ?, item_description = ?, item_price_per_night = ?, item_updated_at = ?
        WHERE item_pk = ?""",
        (item_name, item_description, item_price_per_night, item_updated_at, item_pk))
        
        db.commit()

        # Fetch existing images from the database
        old_images = db.execute("SELECT image_url FROM item_images WHERE item_fk = ?", (item_pk,)).fetchall()
        old_image_count = len(old_images)
        print("Old images:", old_images)

        # Determine if new images can be added based on the current number of images
        new_images = x.validate_item_images_no_image_ok()

        # Validate the total number of images
        if new_images != "no-image":
            total_images = old_image_count + len(new_images)
            if total_images > 5:
                raise Exception("Total number of images exceeds the maximum allowed 5", 400)
            elif total_images < 1:
                raise Exception("There must be at least 1 image for the item.", 400)

            # Process each new image, rename it, save it, and store the filename in the database
            for image in new_images:
                filename = f"{item_pk}_{uuid.uuid4().hex}.{image.filename.split('.')[-1]}"
                try: 
                    import production #type: ignore
                    path = f"/home/henrynavntoft/exam_web/images/{filename}"
                except:
                    path = f"images/{filename}"
                
                image.save(str(path))  # Save the image with the new filename
                
                # Insert the image filename into the item_images table (without path)
                db.execute("INSERT INTO item_images (item_fk, image_url) VALUES (?, ?)", (item_pk, filename))
            db.commit()

        return """
        <template mix-redirect="/profile">
        </template>
        """
    except Exception as ex:
        print(ex)
        return x.handle_exception(ex)
    finally:
        if "db" in locals(): db.close()



############################## DELETE IMAGE
@delete("/delete_image/<image_url>")
def _(image_url):
    try:
        user = x.validate_user_logged()

        # Validate if the user has rights to the image
        x.validate_user_has_rights_to_image(user, image_url)

        db = x.db()

        # Fetch the image row
        image_row = db.execute("SELECT * FROM item_images WHERE image_url = ?", (image_url,)).fetchone()
        if not image_row:
            raise Exception("Image not found", 400)

        # Fetch all images associated with the item
        all_images = db.execute("SELECT image_url FROM item_images WHERE item_fk = ?", (image_row['item_fk'],)).fetchall()

        # Check how many images are left
        remaining_images = len(all_images)
        if remaining_images <= 1:
            raise Exception("Cannot delete the last image of an item.", 400)

        # Delete the image file if it exists
        path = Path(f"images/{image_url}")
        if path.exists():
            path.unlink()  # Delete the image file
            print("Image deleted successfully.")
        else:
            print("Image file not found.")

        # Delete the image record from the database
        db.execute("DELETE FROM item_images WHERE image_url = ?", (image_url,))
        db.commit()

        return """
        <template mix-redirect="/profile">
        </template>
        """
    
    except Exception as ex:
        return x.handle_exception(ex)
    
    finally:
        if "db" in locals(): db.close()



##############################  DELETE ITEM
@delete("/delete_item/<item_pk>") 
def _(item_pk):
    try:
        user = x.validate_user_logged()

        x.validate_user_has_rights_to_item(user, item_pk)

        db = x.db()

        images = db.execute("SELECT image_url FROM item_images WHERE item_fk = ?", (item_pk,)).fetchall()

        for image in images:
            file_path = os.path.join('images', image['image_url'])  
            if os.path.exists(file_path):
                os.remove(file_path)
        
        db.execute("DELETE FROM item_images WHERE item_fk = ?", (item_pk,))
        db.commit()


        db.execute("DELETE FROM items WHERE item_pk = ?", (item_pk,))
        db.commit()
        return """
        <template mix-redirect="/profile">
        </template>
        """
    except Exception as ex:
        return x.handle_exception(ex)
    finally:
        if "db" in locals(): db.close()


##############################
@put("/book_item")
def _():
    try:
        user = x.validate_user_logged()
        if user['user_role'] != "customer":
            raise Exception("User is not a customer", 403)
        else:
            item_pk = x.validate_item_pk()
            db = x.db()
            db.execute("UPDATE items SET item_is_booked = 1 WHERE item_pk = ?", (item_pk,))
            db.commit()

            return """
            <template mix-redirect="/">
            </template>
            """
    except Exception as ex:
        return x.handle_exception(ex)
    finally:
        if "db" in locals(): db.close()

##############################
@put("/unbook_item")
def _():
    try:
        user = x.validate_user_logged()
        if user['user_role'] != "customer":
            raise Exception("User is not a customer", 403)
        else:
            item_pk = x.validate_item_pk()
            db = x.db()
            db.execute("UPDATE items SET item_is_booked = 0 WHERE item_pk = ?", (item_pk,))
            db.commit()
        
            return """
            <template mix-redirect="/">
            </template>
            """
    except Exception as ex:
        return x.handle_exception(ex)
    finally:
        if "db" in locals(): db.close()


##############################
@put("/block_item")
def _():
    try:
        item_pk = x.validate_item_pk()

        db = x.db()

        item = db.execute("SELECT * FROM items WHERE item_pk = ?", (item_pk,)).fetchone()
        if not item:
            raise Exception("Item not found", 404)
        
        user = x.validate_user_logged()

        if user['user_role'] != "admin":
            raise Exception("User is not an admin", 403)
        
        x.validate_user_has_rights_to_item(user, item_pk)
        

        # Update the item to set it as blocked
        db.execute("UPDATE items SET item_is_blocked = 1 WHERE item_pk = ?", (item_pk,))
        
        # Retrieve the owner's email directly from the users table using the item_owner field from the items table
        query = """
        SELECT u.user_email 
        FROM users u 
        JOIN items i ON u.user_pk = i.item_owner_fk 
        WHERE i.item_pk = ?
        """
        q = db.execute(query, (item_pk,))
        user_info = q.fetchone()
        
        if not user_info:
            raise Exception("User not found", 404)
        
        user_email = user_info['user_email']
        
        db.commit()

        x.item_blocked(x.SENDER_EMAIL, user_email, item_pk)

        return """
        <template mix-redirect="/profile">
        </template>
        """
    except Exception as ex:
        return x.handle_exception(ex)
    finally:
        if "db" in locals(): db.close()


##############################
@put("/unblock_item")
def _():
    try:
        item_pk = x.validate_item_pk()

        db = x.db()

        item = db.execute("SELECT * FROM items WHERE item_pk = ?", (item_pk,)).fetchone()
        if not item:
            raise Exception("Item not found", 404)
        
        user = x.validate_user_logged()
        if user['user_role'] != "admin":
            raise Exception("User is not an admin", 403)

        x.validate_user_has_rights_to_item(user, item_pk)
        
        
        
        # Update the item to set it as blocked
        db.execute("UPDATE items SET item_is_blocked = 0 WHERE item_pk = ?", (item_pk,))

        
        
        # Retrieve the owner's email directly from the users table using the item_owner field from the items table
        query = """
        SELECT u.user_email 
        FROM users u 
        JOIN items i ON u.user_pk = i.item_owner_fk 
        WHERE i.item_pk = ?
        """
        q = db.execute(query, (item_pk,))
        user_info = q.fetchone()
        
        if not user_info:
            raise Exception("User not found", 404)
        
        user_email = user_info['user_email']
        
        db.commit()

        db.commit()

        x.item_unblocked(x.SENDER_EMAIL, user_email, item_pk)   
        return """
        <template mix-redirect="/profile">
        </template>
        """
    except Exception as ex:
        return x.handle_exception(ex)
    finally:
        if "db" in locals(): db.close()


# ARANGO DB
# CRUD OPERATIONS
########################################################################################################

# Get all users
##############################
@get("/arangodb/users")
def _():
    try:
        # Query to fetch all users
        users = x.db_arango({
            "query": "FOR user IN users RETURN user"
            })
        
        # Check if users are fetched successfully
        if users and "result" in users:
            # Return the users as JSON
            response.content_type = 'application/json'
            return {"status": "success", "data": users["result"]}
        else:
            return {"status": "failure", "message": "Failed to fetch users."}
    except Exception as ex:
        return x.handle_exception(ex)
    finally:
        pass

# Get user by user_id
##############################
@get("/arangodb/user/<user_id>")
def _(user_id):
    try:
        # Fetch the user from the database
        user = x.db_arango({
            "query": "FOR user IN users FILTER user.user_id == @user_id RETURN user", 
            "bindVars": {"user_id": int(user_id)}
            })
        
        # Check if user is fetched successfully
        if user and "result" in user and user["result"]:
            # Return the user as JSON
            return {"status": "success", "data": user["result"][0]}
        else:
            response.status = 404
            return {"status": "failure", "message": "User not found"}
    except Exception as ex:
        return x.handle_exception(ex)
    finally:
        pass


# Create a new user
##############################
@post("/arangodb/user")
def _():
    try:
        # Get JSON data from request body
        user_data = request.json
        
        # Validate and extract user fields from the JSON data
        user_id = user_data.get("user_id")
        user_name = user_data.get("user_name")
        user_email = user_data.get("user_email")

        # Construct user document
        user = {
            "user_id": user_id,
            "user_name": user_name,
            "user_email": user_email
        }
        
        # Insert user document into ArangoDB
        res = x.db_arango({
            "query": "INSERT @doc IN users RETURN NEW", 
            "bindVars": {"doc": user}
            })
        if res and "result" in res:
            new_user = res["result"][0]
            print("New User Added:", new_user)
            return {"status": "success", "data": new_user}
        else:
            return {"status": "failure", "message": "Failed to insert user."}
    except Exception as ex:
        return x.handle_exception(ex)
    finally:
        pass


# Update user by user_id
##############################
@put("/arangodb/user/<user_id>")
def _(user_id):
    try:
        # Fetch the user data from the request body
        user_data = request.json

        # Check if user data is provided
        if not user_data:
            response.status = 400
            return {"status": "failure", "message": "User data is required"}

        # Fetch the user from the database to check if it exists
        user = x.db_arango({
            "query": "FOR user IN users FILTER user.user_id == @user_id RETURN user",
            "bindVars": {"user_id": int(user_id)}
        })
        
        if not user or "result" not in user or not user["result"]:
            response.status = 404
            return {"status": "failure", "message": "User not found"}

        # Perform the update operation
        update_query = """
            FOR user IN users
            FILTER user.user_id == @user_id
            UPDATE user WITH @user_data IN users
            RETURN NEW
        """
        res = x.db_arango({
            "query": update_query,
            "bindVars": {
                "user_id": int(user_id),
                "user_data": user_data
            }
        })

        if res and "result" in res:
            updated_user = res["result"][0]
            return {"status": "success", "data": updated_user}
        else:
            return {"status": "failure", "message": "Failed to update user"}
    except Exception as ex:
        return x.handle_exception(ex)
    finally:
        pass


# Delete user by user_id
##############################
@delete("/arangodb/user/<user_id>")
def _(user_id):
        try:
        # Fetch the user from the database to check if it exists
            user = x.db_arango({
            "query": "FOR user IN users FILTER user.user_id == @user_id RETURN user", 
            "bindVars": {"user_id": int(user_id)}
            })

            if not user or "result" not in user or not user["result"]:
                response.status = 404
                return {"status": "failure", "message": "User not found"}

            # Perform the delete operation
            delete_query = """
            FOR user IN users
            FILTER user.user_id == @user_id
            REMOVE user IN users
            RETURN OLD
            """
            res = x.db_arango({
            "query": delete_query, 
            "bindVars": {"user_id": int(user_id)}
            })

            if res and "result" in res:
                deleted_user = res["result"][0]
                return {"status": "success", "data": deleted_user}
            else:
                return {"status": "failure", "message": "Failed to delete user"}
        except Exception as ex:
            return x.handle_exception(ex)
        finally:
            pass



# RUNNING THE SERVER
##############################

try:
    import production #type: ignore
    application = default_app()
except Exception as ex:
    print("Running local server")
    run(host="0.0.0.0", port=80, debug=True, reloader=True)