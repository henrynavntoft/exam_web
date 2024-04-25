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
  return "PA AWESOME asd"
 
##############################
try:
  import production #type: ignore
  application = default_app()
except Exception as ex:
  print("Running local server")
  run(host="127.0.0.1", port=80, debug=True, reloader=True)