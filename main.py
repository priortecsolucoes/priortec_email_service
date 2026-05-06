from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from Integrations.EmailService import EmailService


app = FastAPI()

email_service = EmailService()


class EmailRequest(BaseModel):

    to: str
    subject: str
    body: str
    attachments: Optional[List[str]] = None


@app.post("/send-email")
def send_email(request: EmailRequest):

    try:

        email_service.send_email(
            to_email=request.to,
            subject=request.subject,
            body=request.body,
            attachments=request.attachments
        )

        return {
            "status": "success",
            "message": "Email enviado com sucesso"
        }

    except Exception as e:

        return {
            "status": "error",
            "message": "Erro ao enviar email",
            "details": str(e)
        }