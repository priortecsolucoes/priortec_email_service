import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv


class EmailService:

    def __init__(self):

        load_dotenv()

        self.sender_email = os.getenv("EMAIL_FROM")
        self.smtp_server = os.getenv("SMTP_SERVER")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.password = os.getenv("EMAIL_PASSWORD")

        if not self.sender_email:
            raise Exception("EMAIL_FROM não configurado no .env")

        if not self.smtp_server:
            raise Exception("SMTP_SERVER não configurado no .env")

        if not self.password:
            raise Exception("EMAIL_PASSWORD não configurado no .env")

    def send_email(self, to_email: str, subject: str, body: str, attachments=None):

        try:

            if attachments is None:
                attachments = []

            message = MIMEMultipart()
            message["From"] = self.sender_email
            message["To"] = to_email
            message["Subject"] = subject

            message.attach(MIMEText(body, "html"))

            for file_path in attachments:

                if not os.path.exists(file_path):
                    raise Exception(f"Arquivo de anexo não encontrado: {file_path}")

                with open(file_path, "rb") as file:

                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(file.read())

                encoders.encode_base64(part)

                filename = os.path.basename(file_path)

                part.add_header(
                    "Content-Disposition",
                    f'attachment; filename="{filename}"'
                )

                message.attach(part)

            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30) as server:

                server.starttls()
                server.login(self.sender_email, self.password)

                recipients = [e.strip() for e in to_email.replace(",", ";").split(";")]

                server.sendmail(
                    self.sender_email,
                    recipients,
                    message.as_string()
                )

            return True

        except smtplib.SMTPAuthenticationError as e:
            raise Exception(f"Erro de autenticação SMTP: {str(e)}")

        except smtplib.SMTPConnectError as e:
            raise Exception(f"Erro de conexão SMTP: {str(e)}")

        except smtplib.SMTPException as e:
            raise Exception(f"Erro SMTP: {str(e)}")

        except Exception as e:
            raise Exception(f"Erro ao enviar email: {str(e)}")