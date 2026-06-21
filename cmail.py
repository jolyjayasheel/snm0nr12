import smtplib

from email.message import EmailMessage
def send_mail(to,subject,body):
    try:
        server=smtplib.SMTP_SSL("smtp.gmail.com",465)
        server.login('jolyjayasheel@gmail.com','oote qfhl icqx gorr')
        msg=EmailMessage()
        msg['FROM']='jolyjayasheel@gmail.com'
        msg['TO']=to
        msg['SUBJECT']=subject
        msg.set_content(body)
        server.send_message(msg)
        print('Mail sent')
        server.close()
    except Exception as e:
        print('FUll ERROR',repr(e))
