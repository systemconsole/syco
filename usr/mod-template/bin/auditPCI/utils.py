import subprocess

#
# Helper functions
#

def x(command):
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout, stderr) = p.communicate()
    if stderr:
        print '-'*80
        print 'ERROR: {0}'.format(command)
        print stderr
        print '-'*80

    return "%s\n%s" % (stdout, stderr)

