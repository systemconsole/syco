#! /usr/bin/env python

# Constants
BOLD = "\033[1m"
RESET = "\033[0;0m"

def remove_file(path):
  for fileName in glob.glob(path):
    print('Remove file %s' % fileName)
    os.remove('%s' % fileName)

if __name__ == "__main__":
  pass