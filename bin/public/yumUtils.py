import app
from general import x, use_original_file
import install

import ConfigParser
import re
import os

def build_commands(commands):
    commands.add("cleanup-external-repos", disable_external_repos, help="Disable all external repos.")


def disable_external_repos():
    '''
    Disable all external repos by setting "enabled = 1" in relevant config-sections. Consequence is that
    yum update will not update universe-repos (unless using the --enablerepo parameter). Used to avoid
    accidental conflicts between rpmforge/epel and updates to unverified package-versions. 

    '''
    repofiles = _get_external_repo_files()
    for repofile in repofiles:
        _disable_all_repos_in_file(repofile) 


def _disable_all_repos_in_file(repofile):
    '''
    Disable all repos in a config file by setting "enabled" to 0 in config section. 

    '''
    # Parse the configuration-file
    c = ConfigParser.SafeConfigParser()
    c.read(repofile)

    # Set "enabled" to 0 for every section in config file (one section per repo defined.) 
    for section in c.sections():
        back = c.set(section,"enabled","0")
        app.print_verbose("Disabled [{0}] in file :{1}".format(section,repofile))
    
    # Flush configparser writes to file. 
    # Make a backup of original file, just in case transacion fails
    use_original_file(repofile)
    with open(repofile, 'wb') as repofile:
        c.write(repofile)



def _get_external_repo_files(repopath = "/etc/yum.repos.d/"):
    '''
    Get a list of filepaths to yum repo definition files, usually located in the repos.d folder. 

    '''
    for repofilename in os.listdir("/etc/yum.repos.d/"):
        # Exclude things that do not end with ".repo" such as mirror lists. 
        # Exclude the Centos repos (base, updates etc) which are not external. 
        if re.match(r'.*repo$', repofilename) and not re.match(r'CentOS', repofilename):
            yield "{0}{1}".format(repopath , repofilename)
           



    
    
