# -*- coding: utf-8 -*-
"""
Created on Tue Feb 21 14:23:46 2017

@author: pi
"""
import os
import subprocess
import time


datime = time.strftime("%Y%m%d_%H%M%S",time.localtime())



"""
smtp-server: securesmtp.t-online.de
e-mail:      la8_doblinger@t-online.de
pwd:         hzRRemail*                  (für allg. login)
email-pwd:   hzRR-la8*                   (speziell für e-mail)
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def check_dir():
    a=os.path.isdir("2send")
    print("directory 2send exists:", a)
    if not a:
        print("'2send' directory does not exist - make it:")
        a=subprocess.call("mkdir 2send", shell=True)
        print(a)

def rem_old_report():
    a=os.path.isdir("2send")
    # try to remove existing files - will be replaced by new ones
    a = subprocess.call("rm -r 2send/Bericht.zip", shell=True)
    print(a)
    a = subprocess.call("/usr/bin/zip -r ./2send/Bericht.zip ./Bilder/", shell=True) # seconds
    print(a)

def call_come():
    fromaddr    = "la8_doblinger@t-online.de"
    toaddr      = "busti_ownz@yahoo.de"
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = "hz-rr la8: Bericht vom "+datime
    body = "hz-rr LA8, Bericht vom "+datime
    msg.attach(MIMEText(body, 'plain'))
    filename = "Bericht.zip"
    attachment = open("2send/Bericht.zip", "rb")
    part = MIMEBase('application', 'octet-stream')
    part.set_payload((attachment).read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', "attachment; filename= %s" % filename)
    msg.attach(part)
    server = smtplib.SMTP('securesmtp.t-online.de', 587)
    server.starttls()
    server.login("la8_doblinger@t-online.de", "hzRR-la8*")
    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)
    server.quit()


if __name__ == "__main__":
    check_dir()
    rem_old_report()
    call_come()