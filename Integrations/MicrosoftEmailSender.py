import os
import base64
import requests
from msal import ConfidentialClientApplication


class MicrosoftEmailSender:
    def __init__(self, client_id, client_secret, tenant_id, user_email):
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self.user_email = user_email
        
        self.app = ConfidentialClientApplication(
            client_id=self.client_id,
            authority=f'https://login.microsoftonline.com/{self.tenant_id}',
            client_credential=self.client_secret
        )
        self.scope = ['https://graph.microsoft.com/.default']

    def get_access_token(self):
        result = self.app.acquire_token_for_client(scopes=self.scope)
        if "access_token" in result:
            return result['access_token']
        else:
            raise Exception("Erro ao obter token de acesso: " + str(result.get("error_description")))

    def encode_attachment(self, file_path, is_image=False, content_id=None):
        with open(file_path, "rb") as f:
            content_bytes = f.read()
            content_encoded = base64.b64encode(content_bytes).decode('utf-8')
        
        filename = os.path.basename(file_path)
        file_extension = os.path.splitext(filename)[1].lower()
        
        content_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
        
        content_type = content_types.get(file_extension, 'application/octet-stream')
        
        attachment = {
            "@odata.type": "#microsoft.graph.fileAttachment",
            "name": filename,
            "contentType": content_type,
            "contentBytes": content_encoded
        }
        
        if is_image and content_id:
            attachment["contentId"] = content_id
            attachment["isInline"] = True
            
        return attachment

    def send_email(self, subject, body_text, to_recipients, attachment_files=None, 
                  inline_image_path=None, inline_image_cid="logo"):
        access_token = self.get_access_token()
        url = f'https://graph.microsoft.com/v1.0/users/{self.user_email}/sendMail'
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        attachments = []

        # Processar anexos regulares (PDFs, etc.)
        if attachment_files:
            if not isinstance(attachment_files, (list, tuple)):
                attachment_files = [attachment_files]
            
            for file_path in attachment_files:
                # Verificar se é imagem para decidir se é inline ou anexo
                file_ext = os.path.splitext(file_path)[1].lower()
                if file_ext in ['.jpg', '.jpeg', '.png', '.gif']:
                    # Se já existe uma imagem inline, trata outras imagens como anexos
                    if inline_image_path and os.path.abspath(file_path) != os.path.abspath(inline_image_path):
                        attachments.append(self.encode_attachment(file_path, is_image=False))
                else:
                    # PDFs e outros arquivos como anexos regulares
                    attachments.append(self.encode_attachment(file_path, is_image=False))

        # Adicionar imagem inline (logo)
        if inline_image_path and os.path.exists(inline_image_path):
            attachments.append(
                self.encode_attachment(
                    inline_image_path, 
                    is_image=True, 
                    content_id=inline_image_cid
                )
            )
        
        # Verificar o tipo de conteúdo do body_text
        has_html_tags = any(tag in body_text for tag in ['<br>', '<br/>', '<p>', '<div>', '<span>'])
        
        if has_html_tags:
            # Tem tags HTML básicas - criar um HTML completo em torno do conteúdo
            body_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        margin: 0;
                        padding: 20px;
                        background-color: #f9f9f9;
                    }}
                    .email-container {{
                        max-width: 600px;
                        margin: 0 auto;
                        background-color: #ffffff;
                        padding: 30px;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }}
                    .content {{
                        margin-bottom: 25px;
                    }}
                    .signature {{
                        margin-top: 25px;
                        padding-top: 20px;
                        border-top: 2px solid #e0e0e0;
                        text-align: center;
                    }}
                    .logo {{
                        max-width: 180px;
                        height: auto;
                        margin-top: 15px;
                    }}
                    .footer {{
                        margin-top: 20px;
                        font-size: 12px;
                        color: #666;
                        text-align: center;
                    }}
                </style>
            </head>
            <body>
                <div class="email-container">
                    <div class="content">
                        {body_text}
                    </div>
                    <div class="signature">
                        <p><strong>Atenciosamente,</strong></p>
                        <img src="cid:{inline_image_cid}" alt="Logo da Empresa" class="logo">
                    </div>
                    <div class="footer">
                        Este e-mail foi enviado automaticamente. Por favor, não responda.
                    </div>
                </div>
            </body>
            </html>
            """
        else:
            # É texto puro - converter quebras de linha para <br>
            formatted_body = body_text.replace('\n', '<br>')
            
            body_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        margin: 0;
                        padding: 20px;
                        background-color: #f9f9f9;
                    }}
                    .email-container {{
                        max-width: 600px;
                        margin: 0 auto;
                        background-color: #ffffff;
                        padding: 30px;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }}
                    .content {{
                        margin-bottom: 25px;
                    }}
                    .signature {{
                        margin-top: 25px;
                        padding-top: 20px;
                        border-top: 2px solid #e0e0e0;
                        text-align: center;
                    }}
                    .logo {{
                        max-width: 180px;
                        height: auto;
                        margin-top: 15px;
                    }}
                    .footer {{
                        margin-top: 20px;
                        font-size: 12px;
                        color: #666;
                        text-align: center;
                    }}
                </style>
            </head>
            <body>
                <div class="email-container">
                    <div class="content">
                        {formatted_body}
                    </div>
                    <div class="signature">
                        <p><strong>Atenciosamente,</strong></p>
                        <img src="cid:{inline_image_cid}" alt="Logo da Empresa" class="logo">
                    </div>
                    <div class="footer">
                        Este e-mail foi enviado automaticamente. Por favor, não responda.
                    </div>
                </div>
            </body>
            </html>
            """

        body = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "HTML",
                    "content": body_html
                },
                "toRecipients": [{"emailAddress": {"address": addr}} for addr in to_recipients]
            }
        }
        
        if attachments:
            body["message"]["attachments"] = attachments
        
        response = requests.post(url, headers=headers, json=body)
        return response.status_code, response.text