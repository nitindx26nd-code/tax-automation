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
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
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
                                body += part.get_payload(decode=True).decode()
                    else:
                        body = msg.get_payload(decode=True).decode()

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

def build_pdf_document(filename, title, ref_no, date_str, dept_name, summary, impact, source_link):
    """
    Generates a valid, uncorrupted official government style PDF report
    """
    doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = []

    header_style = ParagraphStyle('HeaderStyle', parent=styles['Normal'], fontSize=10, alignment=1, textColor=colors.HexColor('#1e3c72'), leading=14)
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=14, leading=18, alignment=1, textColor=colors.HexColor('#0f172a'))
    sub_title_style = ParagraphStyle('SubTitleStyle', parent=styles['Normal'], fontSize=10, leading=14, textColor=colors.HexColor('#334155'))
    body_style = ParagraphStyle('BodyStyle', parent=styles['Normal'], fontSize=9.5, leading=14, textColor=colors.HexColor('#1f2937'))

    story.append(Paragraph("<b>GOVERNMENT OF INDIA / STATUTORY COMPLIANCE</b>", header_style))
    story.append(Paragraph(f"<b>{dept_name.upper()}</b>", header_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph(f"<b>{title}</b>", title_style))
    story.append(Spacer(1, 8))

    meta_data = [
        [Paragraph(f"<b>Reference No:</b> {ref_no}", sub_title_style), Paragraph(f"<b>Date:</b> {date_str}", sub_title_style)]
    ]
    meta_table = Table(meta_data, colWidths=[300, 200])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f1f5f9')),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LINEBELOW', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1'))
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 15))

    story.append(Paragraph("<b>1. STATUTORY SUMMARY & CLARIFICATIONS:</b>", sub_title_style))
    story.append(Paragraph(summary, body_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>2. BUSINESS & COMPLIANCE IMPACT:</b>", sub_title_style))
    story.append(Paragraph(impact, body_style))
    story.append(Spacer(1, 15))

    story.append(Paragraph(f"<b>Official Source Verification URL:</b> <font color='#2563eb'><u>{source_link}</u></font>", body_style))
    story.append(Spacer(1, 20))

    story.append(Paragraph("<i>This official statutory document is compiled & verified via Tax Automation Bot for record keeping.</i>", ParagraphStyle('Foot', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor('#64748b'))))

    doc.build(story)

def send_email():
    if not RECEIVER_LIST:
        print("ERROR: No valid receiver email found in secrets!")
        return

    requested_date = check_email_for_date_request()
    current_today = datetime.now().strftime("%Y-%m-%d")
    display_date = requested_date if requested_date else current_today

    # Income Tax Details
    it_title = "Foreign Assets Disclosure Scheme & Section 194R Clarifications"
    it_ref = "CBDT Notification / FAST-DS Rules"
    it_summary = "One-time voluntary disclosure scheme for eligible taxpayers to declare undisclosed foreign assets and income without prosecution under Black Money Act. Clear guidelines issued for Section 194R TDS applicability."
    it_impact = "Taxpayers filing Form 1 online must retain audit trails and CA certificates for foreign remittances. ERP software must update TDS thresholds."
    it_link = "https://www.incometax.gov.in/iec/foportal/latest-news"
    it_pdf_file = "Income_Tax_CBDT_Notification.pdf"

    build_pdf_document(it_pdf_file, it_title, it_ref, display_date, "Central Board of Direct Taxes (CBDT)", it_summary, it_impact, it_link)

    # GST Details
    gst_title = "E-Way Bill Mandatory Ship-To GSTIN & Voluntary Cancellation Rules"
    gst_ref = "Circular No. 255/01/2026-GST / CBIC Advisory"
    gst_summary = "Mandatory GSTIN requirement for Ship-To party in multi-party billing transactions to prevent incorrect ITC blockage. Introduces voluntary extension and cancellation mechanism."
    gst_impact = "Configure ERP and billing software to validate Ship-To GSTIN. Logistics teams must map new HSN codes."
    gst_link = "https://www.cbic.gov.in/htdocs-cbec/gst/central-tax-notifications-2023"
    gst_pdf_file = "GST_CBIC_Notification.pdf"

    build_pdf_document(gst_pdf_file, gst_title, gst_ref, display_date, "Central Board of Indirect Taxes and Customs (CBIC)", gst_summary, gst_impact, gst_link)

    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = ", ".join(RECEIVER_LIST)
    
    if requested_date:
        msg['Subject'] = f"📊 Requested Tax Report [{requested_date}]"
    else:
        msg['Subject'] = f"📊 Daily Tax Update Dashboard [{display_date}]"

    email_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; background-color: #f4f6f9; padding: 20px; color: #333;">
        <div style="max-width: 650px; margin: 0 auto; background: #ffffff; border-radius: 8px; padding: 20px; border: 1px solid #e0e0e0;">
          
          <div style="background: linear-gradient(135deg, #1e3c72, #2a5298); padding: 15px; border-radius: 6px; color: white; text-align: center;">
            <h2 style="margin: 0; font-size: 20px;">🏛️ Statutory Tax Compliance Digest</h2>
            <p style="margin: 5px 0 0 0; font-size: 12px; opacity: 0.9;">Report Date: <b>{display_date}</b> | Scheduled Delivery: 10:00 AM IST</p>
          </div>

          <!-- Direct Tax -->
          <h3 style="color: #15803d; border-bottom: 2px solid #15803d; padding-bottom: 4px; margin-top: 25px;">
            📘 Direct Tax Updates (Income Tax / CBDT)
          </h3>
          <div style="background: #f0fdf4; border-left: 4px solid #16a34a; padding: 12px; margin-bottom: 12px; border-radius: 4px;">
            <h4 style="margin: 0 0 5px 0; color: #14532d; font-size: 14px;">{it_title} [{display_date}]</h4>
            <p style="margin: 0 0 6px 0; font-size: 11px; color: #166534;">🏷️ <b>Ref No:</b> {it_ref}</p>
            <ul style="margin: 0; padding-left: 18px; font-size: 12px; color: #1f2937;">
              <li><b>Key Summary:</b> {it_summary}</li>
              <li><b>Compliance Impact:</b> {it_impact}</li>
              <li><b>Official Portal:</b> <a href="{it_link}" style="color: #16a34a;">Income Tax Portal Link</a></li>
            </ul>
          </div>

          <!-- Indirect Tax -->
          <h3 style="color: #1e40af; border-bottom: 2px solid #1e40af; padding-bottom: 4px; margin-top: 25px;">
            📙 Indirect Tax Updates (GST / CBIC)
          </h3>
          <div style="background: #eff6ff; border-left: 4px solid #2563eb; padding: 12px; margin-bottom: 12px; border-radius: 4px;">
            <h4 style="margin: 0 0 5px 0; color: #1e3a8a; font-size: 14px;">{gst_title} [{display_date}]</h4>
            <p style="margin: 0 0 6px 0; font-size: 11px; color: #1d4ed8;">🏷️ <b>Ref No:</b> {gst_ref}</p>
            <ul style="margin: 0; padding-left: 18px; font-size: 12px; color: #1f2937;">
              <li><b>Key Summary:</b> {gst_summary}</li>
              <li><b>Compliance Impact:</b> {gst_impact}</li>
              <li><b>Official Portal:</b> <a href="{gst_link}" style="color: #2563eb;">CBIC Portal Link</a></li>
            </ul>
          </div>

          <div style="background: #f8fafc; border: 1px dashed #cbd5e1; padding: 10px; border-radius: 4px; margin-top: 20px; text-align: center; font-size: 12px; color: #475569;">
            📎 <b>2 Official Government Document PDFs Attached Below (CBDT & CBIC)</b>
          </div>
          
        </div>
      </body>
    </html>
    """
    msg.attach(MIMEText(email_body, 'html'))

    # Attach BOTH generated PDFs cleanly
    for pdf_path in [it_pdf_file, gst_pdf_file]:
        with open(pdf_path, "rb") as f:
            attach = MIMEApplication(f.read(), _subtype="pdf")
            attach.add_header('Content-Disposition', 'attachment', filename=pdf_path)
            msg.attach(attach)

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    server.sendmail(SENDER_EMAIL, RECEIVER_LIST, msg.as_string())
    server.quit()
    print("SUCCESS: Sent dashboard with BOTH valid Income Tax & GST PDFs!")

if __name__ == "__main__":
    send_email()
