import smtplib
from email.message import EmailMessage
from ..config import settings


def otp_verification_html_format(email: str, otp_code: str) -> str:
  """
  Generates the HTML format for the email.

  Args:
      email (str): Email address of the recipient.
      otp_code (str): OTP code to be sent to the recipient.

  Returns:
      str: HTML format for the email.
  """

  return f"""<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f6f6f6; padding:40px 0;">
    <tr>
      <td align="center">

        <table role="presentation" width="480" cellpadding="0" cellspacing="0"
          style="background-color:#ffffff; border:1px solid #e0e0e0; border-radius:8px; padding:40px;">

          <!-- Logo / Brand -->
          <tr>
            <td align="center" style="padding-bottom:24px;">
              <span style="font-size:28px; font-weight:bold; color:#2DC653;">Tuon</span>
            </td>
          </tr>

          <!-- Heading -->
          <tr>
            <td align="center" style="padding-bottom:24px;">
              <h1 style="font-size:24px; font-weight:400; color:#202124; margin:0;">
                Verify your email
              </h1>
            </td>
          </tr>

          <!-- Divider -->
          <tr>
            <td style="border-top:1px solid #e8e8e8; padding-bottom:24px;"></td>
          </tr>

          <!-- Body text -->
          <tr>
            <td style="font-size:14px; line-height:22px; padding-bottom:20px;">
              Use this code to verify <strong style="color:#2DC653">{email}</strong> and finish signing in to <strong>Tuon</strong>:
            </td>
          </tr>

          <!-- OTP Code -->
          <tr>
            <td align="center" style="padding:16px 0 24px 0;">
              <span style="font-size:36px; letter-spacing:8px; font-weight:600; color:#202124;">
                {otp_code}
              </span>
            </td>
          </tr>

          <!-- Expiry note -->
          <tr>
            <td style="font-size:13px; color:#5f6368; padding-bottom:24px;">
              This code will expire in 5 minutes.
            </td>
          </tr>

          <!-- Footer note -->
          <tr>
            <td style="border-top:1px solid #e8e8e8; padding-top:20px; font-size:12px; color:#80868b; line-height:18px;">
              If you didn't request this code, you can safely ignore this email — no changes will be made to your account.
            </td>
          </tr>

        </table>

        <!-- Outer footer -->
        <table role="presentation" width="480" cellpadding="0" cellspacing="0">
          <tr>
            <td align="center" style="padding-top:20px; font-size:12px; color:#9aa0a6;">
              © 2026 Tuon Dev Team. · This is an automated message, please do not reply.
            </td>
          </tr>
        </table>

      </td>
    </tr>
  </table>
  """


def send_email(email: str, otp_code: str) -> None:
  """
  Send an email to the recipient with the given OTP code.

  Args:
    email (str): Email address of the recipient.
    otp_code (str): OTP code to be sent to the recipient.

  Returns:
    None
  
  Raises:
    Exception: If the email fails to send.
  """
  try:
    msg = EmailMessage()
    msg['Subject'] = 'Verify your email address'
    msg['From'] = settings.BREVO_SMTP_FROM
    msg['To'] = email
    msg.set_content(otp_verification_html_format(email, otp_code), subtype='html')

    with smtplib.SMTP(settings.BREVO_SMTP_SERVER, settings.BREVO_SMTP_PORT) as server:
      server.starttls()
      server.login(settings.BREVO_SMTP_USERNAME, settings.BREVO_SMTP_PASSWORD)
      server.send_message(msg)
      server.quit()
  except Exception as e:
    raise Exception(f"Failed to send email: {e}")