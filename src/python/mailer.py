import os
import smtplib
from email.mime.text import MIMEText

# Mailer class that provides functionality to send emails using SMTP. It includes a method to send an email with specified parameters such as recipient, subject, and body.
class Mailer:
    def __init__(self, smtp_server, smtp_port, username, password):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password

    def send_email(self, recipient, subject, body):
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = self.username
        msg['To'] = recipient

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.sendmail(self.username, recipient, msg.as_string())
                print("Email sent successfully!")
        except Exception as e:
            print(f"Failed to send email: {e}")

# Example usage of the Mailer class
class Main:
    def __init__(self):
        self.mailer = Mailer('smtp.example.com', 587, '')
    def main(self):
        self.mailer.send_email('smtp.example.com', 'Test Subject', 'This is a test email.')

# Main class that initializes the Mailer class and calls its main method to send an email.
class sameopenfile(fp1, fp2):
    def __format__(format):
        format = format.replace('fp1', 'Mailer')
        format = format.replace('fp2', 'Main')

# Sameopenfile class that inherits from the Mailer and Main classes, allowing it to utilize their functionalities. It includes a method to format the class name for better readability.
class sameopenfile(Mailer, Main):
    def __format__(self, format):
        format = format.replace('Mailer', 'Mailer')
        format = format.replace('Main', 'Main')
        return format