#!/usr/bin/env python
#
#  Mattias Hemmingsson
#  matte@elino.se
#
# Script for reminder friend when to bet
# Uses and csv file and send email to remind when its time to bet.
#
# 
import csv
import smtplib
import sys
from datetime import datetime, timedelta, date



#Get users and send email to users
sender = "sycoreply@fareoffice.com"
emailto = "sysop@fareoffice.com"
emails =[]
better = ""
template_dir="/opt/syco/usr/syco-private/var/email_reminder/"

def save_to_file(name):
  '''
  Saves the oncall to file
  '''
  f = open("/tmp/oncall.txt", "w")
  f.write(name)
  f.close()


def read_file():
  '''
  read the oncall to file
  '''
  f = open("/tmp/oncall.txt", "r")
  return int(f.readline()) + 1
  f.close()


def send_oncall():
    '''
    Send an reminder ho is oncall
    '''

    #Get cont on oncall staff and next oncall
    numeroncall =  str(int(len(open(template_dir+"people.csv").readlines())) +1)
    nextoncall = str(read_file())
    
    
    #Loop to begning of file 
    if nextoncall == numeroncall:
      nextoncall = '1'
      
    #Send email to oncall staff
    emails=[]

    #Get how is oncall
    with open(template_dir+'people.csv', 'rb') as f:
        reader = csv.reader(f)
        for row in reader:
            emails.append(row[2])
            if row[0] == nextoncall:
              oncall = row[1]
              #Save oncall to file
              save_to_file(row[0])

        
    #Open file depending on type
    f = open(template_dir+"oncall.txt")
    #Takes firt line in file to subject
    Subject = f.readline().replace("\n","")
    #Gets the rest of file for messages
    file_text = f.read()
    file_in = file_text.replace("$(ONCALL)",oncall)
    message = file_in.replace('$(DATE)',str(date.today().year)+"-"+str(datetime.today().isocalendar()[1]))
    #Send email
    send_email(emails,message)


def schedule(when):
  '''
  Script to run every week to remind to update week report and
  to update docs in redmine
  '''
  f = open(template_dir+when+".txt")
  #Takes firt line in file to subje  Subject = f.readline().replace("\n","")
  #Gets the rest of file for messages
  file_in = f.read()
  message = file_in.replace('$(DATE)',str(date.today().year)+"-"+str(datetime.today().isocalendar()[1]))
  emails = emailto
  
  #Send email
  send_email(emails,message)


#Sending the email
def send_email(emails,message):
      '''
      Send the email
      '''
      try:
         smtpObj = smtplib.SMTP('localhost')
         smtpObj.sendmail(sender, emails, message)         
         print "Successfully sent email"
      except:
         print "Error: unable to send email"
 

if str(sys.argv[1])=="oncall":
  '''
  run the oncall function
  '''
  send_oncall()

else:
  schedule(str(sys.argv[1]))