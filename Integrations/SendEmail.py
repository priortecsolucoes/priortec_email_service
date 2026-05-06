import os
import smtplib
from Integrations.MicrosoftEmailSender import MicrosoftEmailSender
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from datetime import datetime
from email.mime.image import MIMEImage
from email import encoders
from dotenv import load_dotenv

class SendEmail:
    """
    Classe responsável pelo envio de emails com anexos.
    """

    def __init__(self, log_module=None):
        load_dotenv()

        self.sender_email = os.getenv("SENDER_EMAIL")
        self.sender_password = os.getenv("SENDER_PASSWORD")
        self.server_smtp = os.getenv("SERVER_SMTP")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.signature = os.getenv("EMAIL_SIGNATURE", "")
        self.logo_path = os.getenv("LOGO_PATH")
        self.email_body_template = os.getenv("EMAIL_BODY", "")

        self.app_id = os.getenv("APP_ID")
        self.directory_id = os.getenv("DIRECTORY_ID")

        # Log externo (planilha)
        self.log_module = log_module

    def _build_email_signature(self):
        return f"{self.signature}"

    # ================================================
    # Public Method
    # ================================================
    def send_email(self, email, attachment_paths, service_description, item, record_id,due_date):
        """
        Envia o email, tenta novamente caso falhe e registra em planilha se necessário.
        """
        self.due_date = due_date
        try:
            # Garantir lista
            if isinstance(attachment_paths, str):
                print("attachment_paths veio como string. Convertendo para lista...")
                attachment_paths = [attachment_paths]
            elif attachment_paths is None:
                attachment_paths = []
            elif not isinstance(attachment_paths, list):
                raise Exception("attachment_paths deve ser string ou lista.")

            email_body = self._set_email_body(item)

            print("Tentando enviar e-mail (1ª tentativa)...")

            sent = self._try_send(email, attachment_paths, service_description, email_body)

            if sent:
                print("E-mail enviado com sucesso na primeira tentativa!")
                return True

            print("Falha detectada. Tentando enviar e-mail novamente (2ª tentativa)...")

            sent = self._try_send(email, attachment_paths, service_description, email_body)

            if sent:
                print("E-mail enviado com sucesso na segunda tentativa!")
                return True

            # Se chegou aqui, falhou nas 2 tentativas
            print("Falha ao enviar e-mail após duas tentativas.")

            if self.log_module:
                self.log_module.write_value(record_id, "ERRO", "Falha ao enviar o e-mail após 2 tentativas")

            return False

        except Exception as e:
            print(f"Erro inesperado no envio de e-mail: {e}")
            if self.log_module:
                self.log_module.write_value(record_id, "ERRO", f"Erro inesperado: {e}")
            return False

    # ================================================
    # Core send logic with verification
    # ================================================
    def _try_send(self, email, attachment_paths, subject, email_body):
        """
        Executa o envio real e retorna True se realmente foi enviado.
        """
        try:
            # Microsoft Graph
            if self.server_smtp and "office365" in self.server_smtp.lower():
                microsoft_sender = MicrosoftEmailSender(
                    client_id=self.app_id,
                    client_secret=self.sender_password,
                    tenant_id=self.directory_id,
                    user_email=self.sender_email
                )

                status_code, response = microsoft_sender.send_email(
                    subject=subject,
                    body_text=email_body,
                    to_recipients=[email],
                    attachment_files=attachment_paths,
                    inline_image_path=self.logo_path,
                    inline_image_cid="logo"
                )

                print(f"Microsoft Graph Status: {status_code}")

                # Sucesso real
                return 200 <= status_code < 300

            # SMTP tradicional
            return self._send_smtp_email(email, attachment_paths, subject, self.logo_path, email_body)

        except Exception as err:
            print(f"Erro durante envio: {err}")
            return False

    # ================================================
    # SMTP Send + Verification
    # ================================================
    def _send_smtp_email(self, email, attachment_paths, subject, logo_path, email_body):

        message = MIMEMultipart("related")
        message["From"] = self.sender_email
        message["To"] = email
        message["Subject"] = subject

        alternative = MIMEMultipart("alternative")
        message.attach(alternative)
        alternative.attach(MIMEText(email_body, "html"))

        # Logo
        if logo_path and os.path.exists(logo_path):
            try:
                with open(logo_path, "rb") as f:
                    logo_img = MIMEImage(f.read())
                    logo_img.add_header("Content-ID", "<logo_mve>")
                    message.attach(logo_img)
            except:
                print("Aviso: Não foi possível anexar o logo.")

        # Attachments
        for path in attachment_paths:
            if os.path.exists(path):
                with open(path, "rb") as f:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(f.read())

                encoders.encode_base64(part)
                part.add_header("Content-Disposition", f'attachment; filename="{os.path.basename(path)}"')
                message.attach(part)
            else:
                print(f"Arquivo não encontrado: {path}")
                return False

        try:
            with smtplib.SMTP(self.server_smtp, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)

                cleaned = email.replace(",", ";").replace(" ", "")
                recipients = [e.strip() for e in cleaned.split(";")]

                # Envio real com verificação
                response = server.sendmail(self.sender_email, recipients, message.as_string())

                # A biblioteca retorna {} quando NADA falhou → SUCESSO
                if response == {}:
                    return True

                print(f"Resposta SMTP indicando falha: {response}")
                return False

        except Exception as smtp_error:
            print(f"Erro SMTP: {smtp_error}")
            return False
        
        
    def get_greeting():
        hora_atual = datetime.now().hour
        if 5 <= hora_atual < 12:
            return "Bom dia"
        elif 12 <= hora_atual < 18:
            return "Boa tarde"
        else:
            return "Boa noite"

    # ================================================
    # Build Email Body
    # ================================================
    def _set_email_body(self, item):
        try:
            if not self.email_body_template:
                print("EMAIL_BODY não configurado no .env")
                return ""

            vencimento = self.due_date

            greeting = self.get_greeting()
            body = self.email_body_template.replace("#DATA", vencimento).replace('#GREETING',greeting)

            # Insere a logo inline ANTES do texto
            email_html = f"""
                <div style="font-family: Arial, sans-serif; font-size: 14px;">
                    <p>{body}</p>
                    <img src="cid:logo_mve" style="width: 150px; margin-bottom: 20px;" />
                </div>
            """

            # Assinatura (se existir)
            if self.signature:
                email_html += f"<br><br>{self.signature}"

            return email_html

        except Exception as e:
            print(f"Erro ao montar o corpo do e-mail: {e}")
            return ""

