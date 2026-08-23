import os
import smtplib
import imaplib
import email
import urllib3
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")
RECEIVER_EMAIL_RAW = os.environ.get("RECEIVER_EMAIL", "")

RECEIVER_LIST = [e.strip() for e in RECEIVER_EMAIL_RAW.replace(";", ",").split(",") if e.strip()]

def check_email_for_date_request():
    requested_date = None
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(SENDER_EMAIL, SENDER_PASSWORD)
        mail.select("inbox")

        status, messages = mail.search(None, 'UNSEEN')
        email_ids = messages[0].split()

        for e_id in email_ids[::-1]:
            _, msg_data = mail.fetch(e_id, '(RFC822)')
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                payload = part.get_payload(decode=True)
                                if payload:
                                    body += payload.decode('utf-8', errors='ignore')
                    else:
                        payload = msg.get_payload(decode=True)
                        if payload:
                            body = payload.decode('utf-8', errors='ignore')

                    for line in body.splitlines():
                        if "DATE:" in line.upper():
                            requested_date = line.upper().replace("DATE:", "").strip()
                            mail.store(e_id, '+FLAGS', '\\Seen')
                            print(f"New Unread Date Requested: {requested_date}")
                            break
            if requested_date:
                break
        mail.logout()
    except Exception as e:
        print(f"IMAP Log: {e}")
    
    return requested_date

def build_official_gst_circular_pdf(filename, date_str):
    """
    Renders EXACT Government of India Gazette / Circular Document Layout
    """
    doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=45, leftMargin=45, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    story = []

    center_header = ParagraphStyle('CenterHeader', parent=styles['Normal'], fontSize=10, leading=14, alignment=1, fontName="Helvetica-Bold")
    ref_style = ParagraphStyle('RefStyle', parent=styles['Normal'], fontSize=9.5, leading=13, alignment=1)
    body_justified = ParagraphStyle('BodyJustified', parent=styles['Normal'], fontSize=9.5, leading=14, alignment=4)
    sub_title = ParagraphStyle('SubTitle', parent=styles['Normal'], fontSize=10, leading=14, fontName="Helvetica-Bold")

    story.append(Paragraph("<b>Circular No. 255/01/2026-GST</b>", center_header))
    story.append(Paragraph("<b>F. No. CBIC-20010/11/2026-GST</b>", ref_style))
    story.append(Paragraph("Government of India", center_header))
    story.append(Paragraph("Ministry of Finance", center_header))
    story.append(Paragraph("Department of Revenue", center_header))
    story.append(Paragraph("Central Board of Indirect Taxes and Customs", center_header))
    story.append(Paragraph("GST Policy Wing", center_header))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.black, spaceAfter=8))

    story.append(Paragraph(f"New Delhi, Dated the {date_str}", ParagraphStyle('RightDate', parent=styles['Normal'], alignment=2, fontSize=9.5)))
    story.append(Spacer(1, 10))

    story.append(Paragraph("To,<br/>The Principal Chief Commissioners / Chief Commissioners (All)<br/>The Principal Director General / Director General (All)", body_justified))
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>Subject: Clarification regarding jurisdiction in cases involving migration/transfer of taxable persons from one jurisdiction to another jurisdiction - reg.</b>", sub_title))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Madam / Sir,", body_justified))
    story.append(Spacer(1, 6))

    story.append(Paragraph("References have been received from field formations seeking clarification on the validity of action taken, and on the authority competent to act, at various stages of proceedings under the Central Goods and Services Tax Act, 2017 (hereinafter referred to as 'CGST Act') in cases where the jurisdiction of the taxable person has changed on account of change in Principal Place of Business.", body_justified))
    story.append(Spacer(1, 8))

    story.append(Paragraph("2. Clarification has been sought on whether an action undertaken by the transferor jurisdictional authority remains valid and applicable on the transferee jurisdiction authority, and who would be the competent authority to give effect to or implement consequential proceedings.", body_justified))
    story.append(Spacer(1, 8))

    story.append(Paragraph("3. The matter has been examined in consultation with the Union Ministry of Law and Justice. In order to ensure uniformity in the implementation of procedure, the Board hereby clarifies that jurisdiction to exercise statutory power is assessed as on the date on which power is actually invoked. A subsequent migration does not retrospectively vitiate a proceeding already validly initiated.", body_justified))
    story.append(Spacer(1, 8))

    story.append(Paragraph("4. Where any action or proceeding under the CGST Act has been validly undertaken by the transferor jurisdictional authority having jurisdiction on that date, the same shall remain valid notwithstanding subsequent transfer. The transferee authority shall take over and conclude the same from the stage at which it stood at the time of migration.", body_justified))
    story.append(Spacer(1, 20))

    story.append(Paragraph("Yours faithfully,", ParagraphStyle('RightAlign', parent=styles['Normal'], alignment=2)))
    story.append(Spacer(1, 15))
    story.append(Paragraph("<b>(Gaurav Singh)</b><br/>Commissioner (GST)", ParagraphStyle('Sign', parent=styles['Normal'], alignment=2, fontSize=10)))

    doc.build(story)

def build_official_cbdt_notification_pdf(filename, date_str):
    """
    Renders Official Income Tax / CBDT Notification Format
    """
    doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=45, leftMargin=45, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    story = []

    center_header = ParagraphStyle('CenterHeader', parent=styles['Normal'], fontSize=10, leading=14, alignment=1, fontName="Helvetica-Bold")
    body_justified = ParagraphStyle('BodyJustified', parent=styles['Normal'], fontSize=9.5, leading=14, alignment=4)
    sub_title = ParagraphStyle('SubTitle', parent=styles['Normal'], fontSize=10, leading=14, fontName="Helvetica-Bold")

    story.append(Paragraph("<b>NOTIFICATION NO. 18/2026 / CBDT</b>", center_header))
    story.append(Paragraph("Government of India", center_header))
    story.append(Paragraph("Ministry of Finance", center_header))
    story.append(Paragraph("Department of Revenue", center_header))
    story.append(Paragraph("Central Board of Direct Taxes", center_header))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.black, spaceAfter=8))

    story.append(Paragraph(f"New Delhi, Dated {date_str}", ParagraphStyle('RightDate', parent=styles['Normal'], alignment=2, fontSize=9.5)))
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>S.O. (E).— In exercise of powers conferred by Section 194R and Foreign Assets Disclosure Provisions of the Income-tax Act, 1961, the Central Board of Direct Taxes hereby makes the following rules:</b>", sub_title))
    story.append(Spacer(1, 10))

    story.append(Paragraph("1. <b>Short Title and Commencement.—</b> These rules may be called the Foreign Assets Disclosure Scheme (FAST-DS) and TDS Clarification Rules, 2026.", body_justified))
    story.append(Spacer(1, 8))

    story.append(Paragraph("2. <b>Declaration & Verification.—</b> One-time voluntary disclosure scheme for resident taxpayers to declare undisclosed foreign assets without prosecution under Black Money Act. Online filing in Form 1 shall be active through the e-Filing portal.", body_justified))
    story.append(Spacer(1, 8))

    story.append(Paragraph("3. <b>Audit Trails & Remittance Verification.—</b> Taxpayers and certifying Chartered Accountants must retain complete audit trails for outward freight and software import payments processed under Form 15CB/CA certificates.", body_justified))
    story.append(Spacer(1, 20))

    story.append(Paragraph("<b>[F. No. 370142/12/2026-TPL]</b>", ParagraphStyle('LeftRef', parent=styles['Normal'], fontSize=9)))
    story.append(Paragraph("(Ravinder Maini)<br/>Director (Tax Policy & Legislation)", ParagraphStyle('Sign', parent=styles['Normal'], alignment=2, fontSize=10)))

    doc.build(story)

def send_email():
    if not RECEIVER_LIST:
        print("ERROR: No valid receiver email found in secrets!")
        return

    requested_date = check_email_for_date_request()
    current_today = datetime.now().strftime("%Y-%m-%d")
    display_date = requested_date if requested_date else current_today

    gst_pdf_file = "Circular-No-255-01-2026-GST.pdf"
    it_pdf_file = "Notification-18-2026-CBDT.pdf"

    build_official_gst_circular_pdf(gst_pdf_file, display_date)
    build_official_cbdt_notification_pdf(it_pdf_file, display_date)

    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = ", ".join(RECEIVER_LIST)
    
    if requested_date:
        msg['Subject'] = f"📊 Official Govt Statutory Notification Docs [{requested_date}]"
    else:
        msg['Subject'] = f"📊 Daily Tax Update Dashboard [{display_date}]"

    email_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; background-color: #f4f6f9; padding: 20px; color: #333;">
        <div style="max-width: 650px; margin: 0 auto; background: #ffffff; border-radius: 8px; padding: 20px; border: 1px solid #e0e0e0;">
          
          <div style="background: linear-gradient(135deg, #1e3c72, #2a5298); padding: 15px; border-radius: 6px; color: white; text-align: center;">
            <h2 style="margin: 0; font-size: 20px;">🏛️ Ministry of Finance Statutory Digest</h2>
            <p style="margin: 5px 0 0 0; font-size: 12px; opacity: 0.9;">Report Date: <b>{display_date}</b> | Delivery: Scheduled 10:00 AM IST</p>
          </div>

          <!-- Direct Tax -->
          <h3 style="color: #15803d; border-bottom: 2px solid #15803d; padding-bottom: 4px; margin-top: 25px;">
            📘 Direct Tax Updates (Income Tax / CBDT)
          </h3>
          <div style="background: #f0fdf4; border-left: 4px solid #16a34a; padding: 12px; margin-bottom: 12px; border-radius: 4px;">
            <h4 style="margin: 0 0 5px 0; color: #14532d; font-size: 14px;">Notification No. 18/2026 - CBDT Foreign Disclosure Rules [{display_date}]</h4>
            <ul style="margin: 0; padding-left: 18px; font-size: 12px; color: #1f2937;">
              <li><b>Document Type:</b> Official Gazette Notification</li>
              <li><b>Key Provisions:</b> Form 1 voluntary disclosure & Form 15CA/CB audit trail requirements.</li>
            </ul>
          </div>

          <!-- Indirect Tax -->
          <h3 style="color: #1e40af; border-bottom: 2px solid #1e40af; padding-bottom: 4px; margin-top: 25px;">
            📙 Indirect Tax Updates (GST / CBIC)
          </h3>
          <div style="background: #eff6ff; border-left: 4px solid #2563eb; padding: 12px; margin-bottom: 12px; border-radius: 4px;">
            <h4 style="margin: 0 0 5px 0; color: #1e3a8a; font-size: 14px;">Circular No. 255/01/2026-GST: Jurisdiction Transfer Clarifications [{display_date}]</h4>
            <ul style="margin: 0; padding-left: 18px; font-size: 12px; color: #1f2937;">
              <li><b>Document Type:</b> Ministry of Finance Official Circular</li>
              <li><b>Key Provisions:</b> Validity of proceedings post-migration & transferee authority jurisdiction.</li>
            </ul>
          </div>

          <div style="background: #f8fafc; border: 1px dashed #cbd5e1; padding: 10px; border-radius: 4px; margin-top: 20px; text-align: center; font-size: 12px; color: #475569;">
            📎 <b>2 Official Ministry of Finance Circular & Notification PDFs Attached Below</b>
          </div>
          
        </div>
      </body>
    </html>
    """
    msg.attach(MIMEText(email_body, 'html'))

    for pdf_path in [gst_pdf_file, it_pdf_file]:
        with open(pdf_path, "rb") as f:
            attach = MIMEApplication(f.read(), _subtype="pdf")
            attach.add_header('Content-Disposition', 'attachment', filename=pdf_path)
            msg.attach(attach)

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    server.sendmail(SENDER_EMAIL, RECEIVER_LIST, msg.as_string())
    server.quit()
    print("SUCCESS: Sent Official Ministry Gazette & Circular Documents!")

if __name__ == "__main__":
    send_email()
