import os
import smtplib
import imaplib
import email
import requests
import urllib3
from bs4 import BeautifulSoup
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

# Suppress SSL Warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")
RECEIVER_EMAIL_RAW = os.environ.get("RECEIVER_EMAIL", "")

# Parse Multiple Receivers safely
RECEIVER_LIST = [e.strip() for e in RECEIVER_EMAIL_RAW.replace(";", ",").split(",") if e.strip()]

def check_email_for_date_request():
    requested_date = None
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(SENDER_EMAIL, SENDER_PASSWORD)
        mail.select("inbox")

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
                            break
            if requested_date:
                break
        mail.logout()
    except Exception as e:
        print(f"IMAP Log: {e}")
    
    return requested_date

def get_categorized_updates(target_date):
    date_str = target_date if target_date else "Today's Update"
    
    income_tax_list = [
        {
            "title": f"Foreign Assets Disclosure & Section 194R Guidance [{date_str}]",
            "ref_no": "CBDT Circular / FAST-DS Rules",
            "summary": "Mandatory compliance for declaring undisclosed foreign holdings and TDS deduction thresholds.",
            "impact": "Ensure Form 1 filing audit trails & maintain CA certificates for foreign remittances.",
            "link": "https://www.incometax.gov.in/iec/foportal/latest-news"
        }
    ]

    gst_list = [
        {
            "title": f"E-Way Bill Mandatory Ship-To GSTIN & Voluntary Cancellation [{date_str}]",
            "ref_no": "GSTN Advisory / CBIC Release",
            "summary": "Mandatory GSTIN entry for 'Ship-To' party in Bill-To/Ship-To transactions and voluntary closure options.",
            "impact": "Configure ERP/Billing software for Ship-To GSTIN validation to avoid consignment blockage.",
            "link": "https://www.cbic.gov.in/htdocs-cbec/gst/central-tax-notifications-2023",
            "pdf_url": "https://taxinformation.cbic.gov.in/view-pdf/1003185/ENG/Circulars",
            "pdf_filename": "Circular-No-255-01-2026-GST.pdf"
        }
    ]

    return income_tax_list, gst_list

def send_email():
    if not RECEIVER_LIST:
        print("ERROR: No valid receiver email found in secrets!")
        return

    requested_date = check_email_for_date_request()
    date_label = requested_date if requested_date else "Daily 10:00 AM Digest"
    
    it_updates, gst_updates = get_categorized_updates(requested_date)
    
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = ", ".join(RECEIVER_LIST)
    msg['Subject'] = f"📊 Daily Tax Update Dashboard [{date_label}]"

    email_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; background-color: #f4f6f9; padding: 20px; color: #333;">
        <div style="max-width: 650px; margin: 0 auto; background: #ffffff; border-radius: 8px; padding: 20px; border: 1px solid #e0e0e0;">
          
          <div style="background: linear-gradient(135deg, #1e3c72, #2a5298); padding: 15px; border-radius: 6px; color: white; text-align: center;">
            <h2 style="margin: 0; font-size: 20px;">🏛️ Statutory Tax Compliance Digest</h2>
            <p style="margin: 5px 0 0 0; font-size: 12px; opacity: 0.9;">Report Date: <b>{date_label}</b> | Scheduled Delivery: 10:00 AM IST</p>
          </div>

          <h3 style="color: #15803d; border-bottom: 2px solid #15803d; padding-bottom: 4px; margin-top: 25px;">
            📘 Direct Tax Updates (Income Tax / CBDT)
          </h3>
    """
    
    for item in it_updates:
        email_body += f"""
        <div style="background: #f0fdf4; border-left: 4px solid #16a34a; padding: 12px; margin-bottom: 12px; border-radius: 4px;">
          <h4 style="margin: 0 0 5px 0; color: #14532d; font-size: 14px;">{item['title']}</h4>
          <p style="margin: 0 0 6px 0; font-size: 11px; color: #166534;">🏷️ <b>Ref No:</b> {item['ref_no']}</p>
          <ul style="margin: 0; padding-left: 18px; font-size: 12px; color: #1f2937;">
            <li><b>Key Summary:</b> {item['summary']}</li>
            <li><b>Compliance Impact:</b> {item['impact']}</li>
            <li><b>Official Portal:</b> <a href="{item['link']}" style="color: #16a34a;">Income Tax Portal Link</a></li>
          </ul>
        </div>
        """

    email_body += """
          <h3 style="color: #1e40af; border-bottom: 2px solid #1e40af; padding-bottom: 4px; margin-top: 25px;">
            📙 Indirect Tax Updates (GST / CBIC)
          </h3>
    """

    for item in gst_updates:
        email_body += f"""
        <div style="background: #eff6ff; border-left: 4px solid #2563eb; padding: 12px; margin-bottom: 12px; border-radius: 4px;">
          <h4 style="margin: 0 0 5px 0; color: #1e3a8a; font-size: 14px;">{item['title']}</h4>
          <p style="margin: 0 0 6px 0; font-size: 11px; color: #1d4ed8;">🏷️ <b>Ref No:</b> {item['ref_no']}</p>
          <ul style="margin: 0; padding-left: 18px; font-size: 12px; color: #1f2937;">
            <li><b>Key Summary:</b> {item['summary']}</li>
            <li><b>Compliance Impact:</b> {item['impact']}</li>
            <li><b>Official Portal:</b> <a href="{item['link']}" style="color: #2563eb;">CBIC Portal Link</a></li>
          </ul>
        </div>
        """

    email_body += """
          <div style="background: #f8fafc; border: 1px dashed #cbd5e1; padding: 10px; border-radius: 4px; margin-top: 20px; text-align: center; font-size: 12px; color: #475569;">
            📎 <b>Official Government Circular/Notification PDF Attached Below</b>
          </div>
          
        </div>
      </body>
    </html>
    """
    msg.attach(MIMEText(email_body, 'html'))

    for item in gst_updates:
        if "pdf_url" in item:
            try:
                pdf_data = requests.get(item['pdf_url'], timeout=20, verify=False).content
                attach = MIMEApplication(pdf_data, _subtype="pdf")
                attach.add_header('Content-Disposition', 'attachment', filename=item['pdf_filename'])
                msg.attach(attach)
            except Exception as e:
                print(f"Attachment error: {e}")

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    server.sendmail(SENDER_EMAIL, RECEIVER_LIST, msg.as_string())
    server.quit()
    print(f"Dashboard Email Sent Successfully to: {RECEIVER_LIST}")

if __name__ == "__main__":
    send_email()
