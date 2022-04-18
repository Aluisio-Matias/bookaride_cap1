
from secret import em_user, em_pass
import smtplib
from email.message import EmailMessage

EMAIL_ADDRESS = em_user
EMAIL_PASSWORD = em_pass

msg = EmailMessage()
msg['Subject'] = 'Testing email with HTML'
msg['From'] = EMAIL_ADDRESS
msg['To'] = 'aluisio.matias@live.com'
msg.set_content('This is a plain text email')

msg.add_alternative('''\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Testing</title>
</head>
<body>
    <h1 class="display-1 text-center my-3">Hello World from Python!</h1>
</body>
</html>
''', subtype='html')

with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
    smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    smtp.send_message(msg)

