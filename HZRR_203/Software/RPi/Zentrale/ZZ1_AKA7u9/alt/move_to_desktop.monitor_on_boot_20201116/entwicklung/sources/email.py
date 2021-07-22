#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Creation:    16.08.2013
# Last Update: 15.01.2017
#
# Copyright (c) 2013-2017 by Georg Kainzbauer <http://www.gtkdb.de>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#


#
# import required modules
#
from email.mime.text import MIMEText
import smtplib
import sys


#
# declaration of the default mail settings
#

# mail address of the sender
sender = 'sender@domain.de'

# fully qualified domain name of the mail server
smtpserver = 'securesmtp.t-online.de'

# username for the SMTP authentication
smtpusername = 'la8_doblinger@t-online.de'

# password for the SMTP authentication
smtppassword = 'hzRRemail*'

# use TLS encryption for the connection
usetls = True


#
# function to send a mail
#
def sendmail(recipient,subject,content):

  # generate a RFC 2822 message
  msg = MIMEText(content)
  msg['From'] = sender
  msg['To'] = recipient
  msg['Subject'] = subject

  # open SMTP connection
  server = smtplib.SMTP(smtpserver, 465) #465 t-online securesmtp; port 587 andere

  # start TLS encryption
  if usetls:
    server.starttls()    # tls Verschluesselung - ssh aktivieren

  # login with specified account
  if smtpusername and smtppassword:
    server.login(smtpusername,smtppassword)

  # send generated message
  server.sendmail(sender,recipient,msg.as_string())

  # close SMTP connection
  server.quit()


#
# main function
#
def main():

  # call sendmail() and generate a new mail with specified subject and content
  sendmail('pl@loster.com','Test','Dies ist eine Testnachricht.')

  # quit python script
  sys.exit(0)


if __name__ == '__main__':
  main()
