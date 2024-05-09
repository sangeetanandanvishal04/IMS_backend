from passlib.context import CryptContext
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from .config import settings

pwd_context = CryptContext(schemes=["bcrypt"],deprecated="auto")

def hash(password: str):
    return pwd_context.hash(password)

def verify(plain_password, hashed_password):
    return pwd_context.verify(plain_password,hashed_password)

def generate_otp():
    return str(random.randint(1000, 9999))

def send_email(email: str, otp: str):
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    sender_email = settings.email
    password = settings.smtp_password

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = email
    msg['Subject'] = 'Password Reset OTP'
    
    disclaimer = "This is a system-generated email. Please do not respond."
    body = f'Your OTP for password reset in IIITAOne+ App is: {otp}\n\n{disclaimer}'
    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(sender_email, password)
        text = msg.as_string()
        server.sendmail(sender_email, email, text)