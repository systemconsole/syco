'''
Adapted git commands for fosh.

$ fosh git-commit "Commit comment"
Add all files in fosh folder git repo on github.

$ fosh git-clean 
Remove files that should not be added to the git-repo. For now .pyc files.
  
Changelog:
  2011-01-28 - Daniel Lindh - Added git-clean command
  2011-01-xx - Daniel Lindh - Added git-commit command

TODO:

'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The syscon project"
__maintainer__ = "Daniel Lindh"
__email__ = "daniel@cybercow.se"
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import general, app

def build_commands(commands):
  commands.add("git-commit", git_commit, "[comment]", help="Commit changes to fosh to github")
  commands.add("git-clean", git_clean, help="Remove files that should not be added to the git-repo. For now .pyc files.")
  
def git_commit(args):
  '''
  Commit the fosh folder to the github repository.
  
  '''
  comment=args[1]
  git_clean(args)
  general.shell_exec("cd " + app.fosh_path + ";git add *")
  general.shell_exec("cd " + app.fosh_path + ";git commit -a -m'%s'" % comment)
  general.shell_exec("cd " + app.fosh_path + ";git push origin")
  
def git_clean(args):
  general.shell_exec("find " + app.fosh_path + " -iname '*.pyc' -delete")
