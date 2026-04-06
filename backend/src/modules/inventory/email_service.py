import aiosmtplib
from email.message import EmailMessage
from src.core.config import settings
from loguru import logger

class EmailService:
    """
    Service gérant l'envoi des notifications par email (US 10.4).
    """

    async def send_stockout_warning(self, to_email: str, product_title: str, days_left: int):
        """
        Envoie un email d'alerte pour une rupture de stock imminente.
        """
        message = EmailMessage()
        message["From"] = settings.EMAIL_FROM
        message["To"] = to_email
        message["Subject"] = f"⚠️ [Michi] Alerte de rupture : {product_title}"

        content = f"""
        Bonjour,

        Votre outil Michi 道 a détecté un risque de rupture pour le produit suivant :
        📦 Produit : {product_title}
        ⏳ Temps restant estimé : {days_left} jours

        Il est recommandé de passer commande dès maintenant pour couvrir votre délai de réapprovisionnement.

        Consultez votre analyse complète ici : http://localhost:3000/dashboard

        L'équipe Michi
        道💜
        """
        message.set_content(content)

        # Mock send in development if no SMTP password
        if settings.ENVIRONMENT == "development" and settings.SMTP_PASSWORD == "your_password":
            logger.info(f"[EmailService] MOCK SEND to {to_email}: {message['Subject']}")
            return True

        try:
            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                use_tls=True if settings.SMTP_PORT == 465 else False,
                start_tls=True if settings.SMTP_PORT == 587 else False,
            )
            logger.success(f"[EmailService] Email sent to {to_email} for {product_title}")
            return True
        except Exception as e:
            logger.error(f"[EmailService] Failed to send email to {to_email}: {str(e)}")
            return False
