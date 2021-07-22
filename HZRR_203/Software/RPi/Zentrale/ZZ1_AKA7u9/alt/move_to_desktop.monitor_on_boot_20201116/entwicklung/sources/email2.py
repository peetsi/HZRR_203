#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 17 19:08:24 2017

@author: pl
"""

import smtplib


HOST = "securesmtp.t-online.de"
SUBJECT = "test"
TO = "pl@loster.com"
FROM = "la8_doblinger@t-online.de"
text = "this is a test from the pi"
BODY = "from: %s to: %s Subject: %s \r\n\
                              %s\r\n"%(FROM,TO,SUBJECT,text)
print(BODY) 


#string.join(("from: %s" %FROM, "to: %s" %TO,"Subject: %s" %SUBJECT, "     ", text), "\r\n")
s = smtplib.SMTP("securesmtp.t-online.de",465) #587)
s.set_debuglevel(1)
s.ehlo()
s.starttls()
s.login("securesmtp.t-online.de", "hzRR-la8*")
s.sendmail(FROM,[TO],BODY)
s.quit