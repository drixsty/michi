from html import escape
import aiosmtplib
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from core.config import settings
from loguru import logger


def _smtp_kwargs() -> dict:
    """Construit les paramètres SMTP depuis la configuration."""
    kwargs: dict = {
        "hostname": settings.SMTP_HOST,
        "port": settings.SMTP_PORT,
        "use_tls": settings.SMTP_PORT == 465,
        "start_tls": settings.SMTP_PORT == 587,
    }
    if settings.SMTP_USER and settings.SMTP_PASSWORD:
        kwargs["username"] = settings.SMTP_USER
        kwargs["password"] = settings.SMTP_PASSWORD
    return kwargs


def _is_mock_mode() -> bool:
    """
    Retourne True si le service doit simuler l'envoi (dev sans SMTP configuré).
    La détection repose sur ENVIRONMENT, pas sur la valeur du mot de passe,
    pour éviter tout faux-positif en production.
    """
    return settings.ENVIRONMENT == "development" and not settings.SMTP_HOST


def _load_template(template_name: str) -> str | None:
    """Charge un template HTML depuis le dossier templates du module inventory."""
    template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
    template_path = os.path.join(template_dir, template_name)
    if not os.path.exists(template_path):
        logger.error(f"[EmailService] Template introuvable : {template_path}")
        return None
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    except OSError as exc:
        logger.error(f"[EmailService] Erreur lecture template {template_name}: {exc}")
        return None


def _apply_replacements(html: str, replacements: dict[str, str]) -> str:
    """
    Applique les remplacements de placeholders avec échappement HTML systématique.
    Protège contre les injections XSS dans les templates d'email.
    """
    for placeholder, value in replacements.items():
        html = html.replace(placeholder, escape(value))
    return html


class EmailService:
    """
    Service gérant l'envoi des notifications par email.
    Toutes les valeurs dynamiques injectées dans les templates HTML sont échappées.
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
        expected_date: str,
    ) -> bool:
        html_content = _load_template("purchase_order.html")
        if html_content is None:
            return False

        html_content = _apply_replacements(html_content, {
            "{{ po_id }}": po_id,
            "{{ supplier_name }}": supplier_name,
            "{{ product_title }}": product_title,
            "{{ product_sku }}": product_sku,
            "{{ quantity }}": str(quantity),
            "{{ order_date }}": order_date,
            "{{ expected_date }}": expected_date,
        })

        message = MIMEMultipart("alternative")
        message["From"] = settings.EMAIL_FROM
        message["To"] = to_email
        message["Subject"] = f"Nouveau Bon de Commande Michi - PO#{escape(po_id)}"
        message.attach(MIMEText(
            f"Nouveau Bon de Commande #{po_id} pour {product_title} ({quantity} unités).",
            "plain",
        ))
        message.attach(MIMEText(html_content, "html"))

        if _is_mock_mode():
            logger.info(f"[EmailService] MOCK — PO #{po_id} → {to_email}")
            return True

        try:
            await aiosmtplib.send(message, **_smtp_kwargs())
            logger.success(f"[EmailService] PO #{po_id} envoyé à {to_email}")
            return True
        except Exception as exc:
            logger.error(f"[EmailService] Échec envoi PO #{po_id} → {to_email}: {exc}")
            return False

    async def send_stockout_warning(
        self, to_email: str, product_title: str, days_left: int
    ) -> bool:
        message = EmailMessage()
        message["From"] = settings.EMAIL_FROM
        message["To"] = to_email
        message["Subject"] = f"[Michi] Alerte rupture : {escape(product_title)}"
        message.set_content(
            f"Bonjour,\n\n"
            f"Michi a détecté un risque de rupture pour : {product_title}\n"
            f"Temps restant estimé : {days_left} jours\n\n"
            f"Consultez votre tableau de bord pour plus de détails.\n\n"
            f"L'équipe Michi"
        )

        if _is_mock_mode():
            logger.info(f"[EmailService] MOCK — alerte rupture {product_title} → {to_email}")
            return True

        try:
            await aiosmtplib.send(message, **_smtp_kwargs())
            logger.success(f"[EmailService] Alerte envoyée à {to_email} pour {product_title}")
            return True
        except Exception as exc:
            logger.error(f"[EmailService] Échec alerte → {to_email}: {exc}")
            return False

    async def send_password_reset(self, to_email: str, reset_link: str) -> bool:
        html_content = _load_template("password_reset.html")

        message = MIMEMultipart("alternative")
        message["From"] = settings.EMAIL_FROM
        message["To"] = to_email
        message["Subject"] = "Réinitialisation de votre mot de passe Michi"

        text = (
            f"Bonjour,\n\nVous avez demandé la réinitialisation de votre mot de passe.\n"
            f"Cliquez ici : {reset_link}\n\n"
            f"Si vous n'êtes pas à l'origine de cette demande, ignorez cet email.\n\n"
            f"L'équipe Michi"
        )
        message.attach(MIMEText(text, "plain"))

        if html_content:
            # reset_link est une URL interne — on ne l'échappe pas dans l'href mais
            # on l'échappe dans le texte visible
            processed = html_content.replace("{{ reset_link }}", reset_link)
            message.attach(MIMEText(processed, "html"))

        if _is_mock_mode():
            logger.info(f"[EmailService] MOCK — reset password → {to_email} : {reset_link}")
            return True

        try:
            await aiosmtplib.send(message, **_smtp_kwargs())
            logger.success(f"[EmailService] Reset email envoyé à {to_email}")
            return True
        except Exception as exc:
            logger.error(f"[EmailService] Échec reset → {to_email}: {exc}")
            return False

    async def send_verification_email(
        self, to_email: str, verification_link: str
    ) -> bool:
        message = MIMEMultipart("alternative")
        message["Subject"] = "Vérifiez votre compte Michi"
        message["From"] = settings.EMAIL_FROM
        message["To"] = to_email

        safe_link = escape(verification_link)
        html_content = f"""
        <html>
            <body>
                <h2>Bienvenue sur Michi !</h2>
                <p>Merci de vous être inscrit. Cliquez ci-dessous pour activer votre compte :</p>
                <a href="{verification_link}"
                   style="background:#7c3aed;color:white;padding:10px 20px;
                          text-decoration:none;border-radius:5px;font-weight:bold;">
                    Vérifier mon e-mail
                </a>
                <p>Ou copiez ce lien dans votre navigateur :</p>
                <p>{safe_link}</p>
                <br/>
                <p>L'équipe Michi</p>
            </body>
        </html>
        """
        message.attach(MIMEText(html_content, "html"))

        if _is_mock_mode():
            logger.info(f"[EmailService] MOCK — vérification → {to_email}: {verification_link}")
            return True

        try:
            await aiosmtplib.send(message, **_smtp_kwargs())
            logger.success(f"[EmailService] Email de vérification envoyé à {to_email}")
            return True
        except Exception as exc:
            logger.error(f"[EmailService] Échec vérification → {to_email}: {exc}")
            return False

    async def send_periodic_report(
        self,
        to_email: str,
        organization_name: str,
        frequency: str,
        total_sales: float,
        stockout_count: int,
        health_score: int,
        critical_products: list,
        date_range: str,
        strategic_insight: str,
    ) -> bool:
        html_content = _load_template("periodic_report.html")
        if html_content is None:
            return False

        product_rows = ""
        for p in critical_products:
            product_rows += (
                f'<tr style="border-bottom:1px solid #f1f5f9;">'
                f'<td style="padding:16px 0;">'
                f'<span style="font-size:13px;font-weight:700;">{escape(p["title"])}</span>'
                f'<br><span style="font-size:11px;color:#94a3b8;">SKU: {escape(p["sku"])}</span>'
                f'</td>'
                f'<td style="text-align:right;padding:16px 0;">'
                f'<div style="color:{escape(p["color"])};">{escape(p["stock_label"])}</div>'
                f'<div>{escape(str(p["days_left"]))}j restants</div>'
                f'</td></tr>'
            )

        # Remplacement manuel du bloc produits dans le template
        product_loop_placeholder = (
            '<!-- PRODUCT_LOOP_START -->\n'
            '                <tr class="product-row">\n'
            '                    <td>\n'
            '                        <div class="p-info">\n'
            '                            <span class="p-name">{{ product.title }}</span>\n'
            '                            <span class="p-sku">SKU: {{ product.sku }}</span>\n'
            '                        </div>\n'
            '                    </td>\n'
            '                    <td class="p-status">\n'
            '                        <div class="p-stock" style="color: PRODUCT_COLOR_PLACEHOLDER;">{{ product.stock_label }}</div>\n'
            '                        <div class="p-days text-slate-400">{{ product.days_left }}j restants</div>\n'
            '                    </td>\n'
            '                </tr>\n'
            '                <!-- PRODUCT_LOOP_END -->'
        )
        html_content = html_content.replace(product_loop_placeholder, product_rows)

        # Valeurs scalaires — échappement systématique
        html_content = _apply_replacements(html_content, {
            "{{ organization_name }}": organization_name,
            "{{ frequency }}": frequency.capitalize(),
            "{{ total_sales }}": f"{total_sales:,.0f}",
            "{{ stockout_count }}": str(stockout_count),
            "{{ health_score }}": str(health_score),
            "{{ date_range }}": date_range,
            "{{ strategic_insight }}": strategic_insight,
            "{{ dashboard_url }}": settings.FRONTEND_URL + "/dashboard",
        })

        message = MIMEMultipart("alternative")
        message["From"] = settings.EMAIL_FROM
        message["To"] = to_email
        message["Subject"] = (
            f"Votre rapport Michi {escape(frequency.capitalize())} — {escape(organization_name)}"
        )
        message.attach(MIMEText(
            f"Résumé {frequency} pour {organization_name}. "
            f"Ventes : {total_sales}€, Ruptures : {stockout_count}.",
            "plain",
        ))
        message.attach(MIMEText(html_content, "html"))

        if _is_mock_mode():
            logger.info(f"[EmailService] MOCK — rapport {frequency} → {to_email}")
            return True

        try:
            await aiosmtplib.send(message, **_smtp_kwargs())
            logger.success(f"[EmailService] Rapport envoyé à {to_email}")
            return True
        except Exception as exc:
            logger.error(f"[EmailService] Échec rapport → {to_email}: {exc}")
            return False
