# 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


# https://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@github.com/henrynavntoft/exam_web.git



#########################
from bottle import default_app, get, post, run
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
  return " World!"
 
##############################
try:
  import production 
  application = default_app()
except Exception as ex:
  print("Running local server")
  run(host="127.0.0.1", port=80, debug=True, reloader=True)