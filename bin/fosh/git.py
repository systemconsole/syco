#! /usr/bin/env python

import general, app

def git_commit(comment):
  '''
  Commit the fosh folder to the github repository.
  '''
  general.shell_exec("find " + app.fosh_path + " -iname '*.pyc' -delete")
  general.shell_exec("cd " + app.fosh_path + ";git add *")
  general.shell_exec("cd " + app.fosh_path + ";git commit -a -m'%s'" % comment)
  general.shell_exec("git push origin")