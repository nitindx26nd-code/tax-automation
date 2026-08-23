import os
import smtplib
import imaplib
import email
import requests
from bs4 import BeautifulSoup
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL")

def check_email_for_date_request():
    requested_date = None
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(SENDER_EMAIL, SENDER_PASSWORD)
        mail.select("inbox")

        # Search all emails to find reply
        status, messages = mail.search(None, 'ALL')
        email_ids = messages[0].split()

        for e_id in email_ids[::-1][:10]:
            _, msg_data = mail.fetch(e_id, '(RFC822)')
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                body += part.get_payload(decode=True).decode()
                    else:
                        body = msg.get_payload(decode=True).decode()

                    for line in body.splitlines():
                        if "DATE:" in line.upper():
                            requested_date = line.upper().replace("DATE:", "").strip()
                            print(f"Detected Requested Date: {requested_date}")
                            break
            if requested_date:
                break
        mail.logout()
    except Exception as e:
        print(f"IMAP Log: {e}")
    
    return requested_date

def generate_pdf_report(notifications, date_str):
    pdf_filename = "Tax_Notification_Report.pdf"
    doc = SimpleDocTemplate(pdf_filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=16, leading=20, textColor='#1e3c72')
    body_style = ParagraphStyle('BodyStyle', parent=styles['Normal'], fontSize=10, leading=14, textColor='#334155')

    story.append(Paragraph(f"Tax Notification Report ({date_str})", title_style))
    story.append(Spacer(1, 12))

    for n in notifications:
        story.append(Paragraph(f"<b>Title:</b> {n['title']}", body_style))
        story.append(Paragraph(f"<b>Notification No:</b> {n['number']} | <b>Date:</b> {n['date']}", body_style))
        story.append(Paragraph(f"<b>Summary:</b> {n['summary']}", body_style))
        story.append(Paragraph(f"<b>Business Impact:</b> {n['impact']}", body_style))
        story.append(Paragraph(f"<b>Source Link:</b> <font color='blue'><u>{n['link']}</u></font>", body_style))
        story.append(Spacer(1, 10))

    doc.build(story)
    return pdf_filename

def get_latest_notifications(target_date=None):
    display_date = target_date if target_date else "Current Date Updates"
    
    notifications = [
        {
            "category": "Direct Tax (CBDT)",
            "number": "CBDT FAST-DS Rules 2026",
            "date": display_date,
            "title": f"Foreign Assets Disclosure Scheme (FAST-DS) Report [{display_date}]",
            "summary": "One-time voluntary disclosure scheme for eligible taxpayers to declare undisclosed foreign assets/income.",
            "impact": "Filing Form 1 online. Avoids prosecution under Black Money Act.",
            "link": "https://www.incometax.gov.in/iec/foportal/latest-news"
        },
        {
            "category": "Indirect Tax (CBIC)",
            "number": "Notification No. 19/2025 - Central Tax",
            "date": display_date,
            "title": f"Valuation Rules under Section 15(5) for Retail Sale Price [{display_date}]",
            "summary": "Notifies specific goods under CGST Act for valuation based on Retail Sale Price.",
            "impact": "ERP systems and billing software must calculate taxable value on declared RSP thresholds.",
            "link": "https://www.cbic.gov.in/htdocs-cbec/gst/central-tax-notifications-2023"
        }
    ]
    return notifications

def send_email():
    requested_date = check_email_for_date_request()
    date_label = requested_date if requested_date else "Daily Regular Digest"
    notifications = get_latest_notifications(requested_date)
    
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg['Subject'] = f"📊 Tax Updates Report for [{date_label}]"

    email_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.5;">
        <h2 style="color: #1e3c72; border-bottom: 2px solid #1e3c72; padding-bottom: 6px;">
          📌 Tax Notification Summary Report
        </h2>
        <p><b>Filter Status:</b> {date_label}</p>
    """
    
    for n in notifications:
        email_body += f"""
        <div style="background-color: #f8fafc; border-left: 4px solid #2563eb; padding: 12px; margin-bottom: 12px;">
          <h3 style="margin: 0 0 4px 0; color: #0f172a; font-size: 14px;">{n['title']}</h3>
          <p style="margin: 0 0 6px 0; font-size: 11px; color: #475569;">
            🏷️ <b>Notification No:</b> {n['number']} | 📅 <b>Date:</b> {n['date']}
          </p>
          <ul style="margin: 0; padding-left: 18px; font-size: 12px; color: #334155;">
            <li><b>Summary:</b> {n['summary']}</li>
            <li><b>Business Impact:</b> {n['impact']}</li>
            <li><b>Source Link:</b> <a href="{n['link']}">{n['link']}</a></li>
          </ul>
        </div>
        """
        
    email_body += """
        <p style="font-size:12px; color:#555;">📎 <b>Real PDF Attached Below!</b></p>
      </body>
    </html>
    """
    msg.attach(MIMEText(email_body, 'html'))

    # Generate & Attach Real PDF
    pdf_path = generate_pdf_report(notifications, date_label)
    with open(pdf_path, "rb") as f:
        attach = MIMEApplication(f.read(), _subtype="pdf")
        attach.add_header('Content-Disposition', 'attachment', filename=f"Tax_Report_{date_label.replace(' ', '_')}.pdf")
        msg.attach(attach)

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
    server.quit()
    print("Email with PDF sent successfully!")

if __name__ == "__main__":
    send_email()
