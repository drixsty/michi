from core.database.models import Organization, User, OrganizationMember
import aiosmtplib
from email.message import EmailMessage
from core.config import settings
from loguru import logger

class EmailService:
    """
    Service gérant l'envoi des notifications par email (US 10.4).
    """

    async def send_purchase_order(
        self, 
        to_email: str, 
        po_id: str, 
        supplier_name: str, 
        product_title: str, 
        product_sku: str, 
        quantity: int,
        order_date: str,
        expected_date: str
    ):
        """
        Envoie un bon de commande professionnel au format HTML (US 16.2).
        """
        import os
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        # Charger le template HTML
        template_path = os.path.join(os.path.dirname(__file__), "templates", "purchase_order.html")
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                html_content = f.read()
        except Exception as e:
            logger.error(f"[EmailService] Template not found at {template_path}")
            return False

        # Remplacement des placeholders {{ variable }}
        replacements = {
            "{{ po_id }}": str(po_id),
            "{{ supplier_name }}": supplier_name,
            "{{ product_title }}": product_title,
            "{{ product_sku }}": product_sku,
            "{{ quantity }}": str(quantity),
            "{{ order_date }}": order_date,
            "{{ expected_date }}": expected_date
        }
        for placeholder, value in replacements.items():
            html_content = html_content.replace(placeholder, value)

        # Création du message MIME
        message = MIMEMultipart("alternative")
        message["From"] = settings.EMAIL_FROM
        message["To"] = to_email
        message["Subject"] = f"📦 Nouveau Bon de Commande Michi - PO#{po_id}"

        # Version texte brute (fallback)
        text_content = f"Nouveau Bon de Commande #{po_id} pour {product_title} ({quantity} unités)."
        message.attach(MIMEText(text_content, "plain"))
        message.attach(MIMEText(html_content, "html"))

        # Simulation en dev
        if settings.ENVIRONMENT == "development" and settings.SMTP_PASSWORD == "your_password":
            logger.info(f"[EmailService] MOCK SEND PO to {to_email}: {message['Subject']}")
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
            logger.success(f"[EmailService] PO #{po_id} sent to {to_email}")
            return True
        except Exception as e:
            logger.error(f"[EmailService] Failed to send PO to {to_email}: {str(e)}")
            return False

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

    async def send_password_reset(self, to_email: str, reset_link: str):
        """
        Envoie un email de réinitialisation de mot de passe (US 21.x).
        """
        import os
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        # On cherche le template dans le dossier templates du module inventory (centralisé pour l'instant)
        # TODO: Déplacer EmailService dans core/services et templates dans core/templates
        template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
        template_path = os.path.join(template_dir, "password_reset.html")
        
        html_content = None
        if os.path.exists(template_path):
            try:
                with open(template_path, "r", encoding="utf-8") as f:
                    html_content = f.read()
                    html_content = html_content.replace("{{ reset_link }}", reset_link)
            except Exception as e:
                logger.error(f"[EmailService] Error reading template: {str(e)}")

        message = MIMEMultipart("alternative")
        message["From"] = settings.EMAIL_FROM
        message["To"] = to_email
        message["Subject"] = "🔐 Réinitialisation de votre mot de passe Michi 道"

        text_content = f"Bonjour,\n\nVous avez demandé la réinitialisation de votre mot de passe Michi.\n\nCliquez sur le lien suivant pour choisir un nouveau mot de passe :\n{reset_link}\n\nSi vous n'êtes pas à l'origine de cette demande, vous pouvez ignorer cet email.\n\nL'équipe Michi 道"
        message.attach(MIMEText(text_content, "plain"))
        
        if html_content:
            message.attach(MIMEText(html_content, "html"))

        # Simulation en dev
        if settings.ENVIRONMENT == "development" and settings.SMTP_PASSWORD == "your_password":
            logger.info(f"[EmailService] MOCK SEND RESET to {to_email}: {reset_link}")
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
            logger.success(f"[EmailService] Reset email sent to {to_email}")
            return True
        except Exception as e:
            logger.error(f"[EmailService] Failed to send reset email to {to_email}: {str(e)}")
            return False
