# 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
# https://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@github.com/henrynavntoft/exam_web.git


#########################
from bottle import default_app, get, post, request, response, run, static_file, template
import x
from icecream import ic
import bcrypt
import json
import credentials
import git
 
@post('/secret')
def git_update():
  repo = git.Repo('./exam_web')
  origin = repo.remotes.origin
  repo.create_head('main', origin.refs.main).set_tracking_branch(origin.refs.main).checkout()
  origin.pull()
  return ""
 
 
##############################
@get("/")
def _():
  return " Hello Tobias, hope it works!"
 



##############################
@get("/app.css")
def _():
    return static_file("app.css", ".")


##############################
@get("/<file_name>.js")
def _(file_name):
    return static_file(file_name+".js", ".")


##############################
@get("/test")
def _():
    return [{"name":"one"}]


##############################
@get("/images/<item_splash_image>")
def _(item_splash_image):
    return static_file(item_splash_image, "images")


# ##############################
# @get("/")
# def _():
#     try:
#         db = x.db()
#         q = db.execute("SELECT * FROM items ORDER BY item_created_at LIMIT 0, ?", (x.ITEMS_PER_PAGE,))
#         items = q.fetchall()
#         ic(items)
#         is_logged = False
#         try:    
#             x.validate_user_logged()
#             is_logged = True
#         except:
#             pass

#         return template("index.html", items=items, mapbox_token=credentials.mapbox_token, 
#                         is_logged=is_logged)
#     except Exception as ex:
#         ic(ex)
#         return ex
#     finally:
#         if "db" in locals(): db.close()


##############################
@get("/items/page/<page_number>")
def _(page_number):
    try:
        db = x.db()
        next_page = int(page_number) + 1
        offset = (int(page_number) - 1) * x.ITEMS_PER_PAGE
        q = db.execute(f"""     SELECT * FROM items 
                                ORDER BY item_created_at 
                                LIMIT ? OFFSET {offset}
                        """, (x.ITEMS_PER_PAGE,))
        items = q.fetchall()
        ic(items)

        is_logged = False
        try:
            x.validate_user_logged()
            is_logged = True
        except:
            pass

        html = ""
        for item in items: 
            html += template("_item", item=item, is_logged=is_logged)
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
        <template mix-function="test">{json.dumps(items)}</template>
        """
    except Exception as ex:
        ic(ex)
        return "ups..."
    finally:
        if "db" in locals(): db.close()


##############################
@get("/login")
def _():
    x.no_cache()
    return template("login.html")


##############################
@get("/profile")
def _():
    try:
        x.no_cache()
        x.validate_user_logged()
        db = x.db()
        q = db.execute("SELECT * FROM items ORDER BY item_created_at LIMIT 0, ?", (x.ITEMS_PER_PAGE,))
        items = q.fetchall()
        ic(items)    
        return template("profile.html", is_logged=True, items=items)
    except Exception as ex:
        ic(ex)
        response.status = 303 
        response.set_header('Location', '/login')
        return
    finally:
        if "db" in locals(): db.close()


##############################
@get("/logout")
def _():
    response.delete_cookie("user")
    response.status = 303
    response.set_header('Location', '/login')
    return


##############################
@get("/api")
def _():
    return x.test()


##############################
@post("/signup")
def _():
    # password = b'password'
    # # Adding the salt to password
    # salt = bcrypt.gensalt()
    # # Hashing the password
    # hashed = bcrypt.hashpw(password, salt)
    # # printing the salt
    # print("Salt :")
    # print(salt)
    
    # # printing the hashed
    # print("Hashed")
    # print(hashed)    
    return "signup"


##############################
@post("/login")
def _():
    try:
        user_email = x.validate_email()
        user_password = x.validate_password()
        db = x.db()
        q = db.execute("SELECT * FROM users WHERE user_email = ? LIMIT 1", (user_email,))
        user = q.fetchone()
        if not user: raise Exception("user not found", 400)
        if not bcrypt.checkpw(user_password.encode(), user["user_password"].encode()): raise Exception("Invalid credentials", 400)
        user.pop("user_password") # Do not put the user's password in the cookie
        ic(user)
        try:
            import production 
            is_cookie_https = True
        except:
            is_cookie_https = False        
        response.set_cookie("user", user, secret=x.COOKIE_SECRET, httponly=True, secure=is_cookie_https)
        
        frm_login = template("__frm_login")
        return f"""
        <template mix-target="frm_login" mix-replace>
            {frm_login}
        </template>
        <template mix-redirect="/profile">
        </template>
        """
    except Exception as ex:
        try:
            response.status = ex.args[1]
            return f"""
            <template mix-target="#toast">
                <div mix-ttl="3000" class="error">
                    {ex.args[0]}
                </div>
            </template>
            """
        except Exception as ex:
            ic(ex)
            response.status = 500
            return f"""
            <template mix-target="#toast">
                <div mix-ttl="3000" class="error">
                   System under maintainance
                </div>
            </template>
            """
        

    finally:
        if "db" in locals(): db.close()


##############################
@post("/toogle_item_block")
def _():
    try:
        item_id = request.forms.get("item_id", '')
        return f"""
        <template mix-target="[id='{item_id}']" mix-replace>
            xxxxx
        </template>
        """
    except Exception as ex:
        pass
    finally:
        if "db" in locals(): db.close()



##############################
try:
  import production 
  application = default_app()
except Exception as ex:
  print("Running local server")
  run(host="0.0.0.0", port=80, debug=True, reloader=True)

