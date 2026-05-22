import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path

logger = logging.getLogger(__name__)

SMTP_TEMPLATES = {
    "gmail":   {"host": "smtp.gmail.com",   "port": 587, "tls": True},
    "outlook": {"host": "smtp-mail.outlook.com", "port": 587, "tls": True},
    "yahoo":   {"host": "smtp.mail.yahoo.com",   "port": 587, "tls": True},
}


def send_report(
    to_email: str,
    subject: str,
    body: str,
    attachments: list[str] = None,
    smtp_host: str = "smtp.gmail.com",
    smtp_port: int = 587,
    smtp_user: str = None,
    smtp_password: str = None,
    use_tls: bool = True,
) -> tuple[bool, str]:
    if not smtp_user or not smtp_password:
        return False, "SMTP no configurado. Define EURICLES_SMTP_USER y EURICLES_SMTP_PASSWORD."

    try:
        msg = MIMEMultipart()
        msg["From"] = smtp_user
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))

        for path in (attachments or []):
            p = Path(path)
            if not p.exists():
                continue
            with open(p, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header("Content-Disposition", f'attachment; filename="{p.name}"')
                msg.attach(part)

        server = smtplib.SMTP(smtp_host, smtp_port, timeout=20)
        if use_tls:
            server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()
        return True, "Correo enviado correctamente"
    except smtplib.SMTPAuthenticationError:
        return False, "Error de autenticación SMTP. Usa una contraseña de aplicación (no la normal)."
    except smtplib.SMTPException as e:
        return False, f"Error SMTP: {e}"
    except Exception as e:
        return False, f"Error inesperado: {e}"
