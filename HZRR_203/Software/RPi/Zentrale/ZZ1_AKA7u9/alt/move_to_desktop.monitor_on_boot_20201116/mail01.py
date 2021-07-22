
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
 
fromaddr = "la8_doblinger@t-online.de"
toaddr = "pl@loster.com"

msg = MIMEMultipart()

msg['From'] = fromaddr
msg['To'] = toaddr
msg['Subject'] = "test"
 
body = "TEst"
 
msg.attach(MIMEText(body, 'plain'))
 
filename = "HK1Mod2_20170126_173031.pdf"
filepath = "Bilder/"+filename
attachment = open(filepath, "rb")
 
part = MIMEBase('application', 'octet-stream')
part.set_payload((attachment).read())
encoders.encode_base64(part)
part.add_header('Content-Disposition', "attachment; filename= %s" % filename)
 
msg.attach(part)
 
server = smtplib.SMTP('securesmtp.t-online.de', 587)
server.starttls()
server.login(fromaddr, "hzRR-la8*")
text = msg.as_string()
server.sendmail(fromaddr, toaddr, text)
server.quit()
