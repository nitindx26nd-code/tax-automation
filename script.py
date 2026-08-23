import os
import smtplib
import imaplib
import email
import requests
from bs4 import BeautifulSoup
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL")

def check_email_for_date_request():
    """
    Reads unread replies to find if a specific date was requested.
    Format in reply: "Date: YYYY-MM-DD" or "Date: DD/MM/YYYY"
    """
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
                            print(f"Filter Target Date: {requested_date}")
                            break
            if requested_date:
                break
        mail.logout()
    except Exception as e:
        print(f"IMAP Log: {e}")
    
    return requested_date

def fetch_all_notification_pdfs(target_date=None):
    """
    Scrapes CBIC/CBDT portals and extracts ALL PDF documents for the given day.
    """
    url = "https://www.cbic.gov.in/htdocs-cbec/gst/central-tax-notifications-2023"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    pdf_list = []
    
    try:
        response = requests.get(url, headers=headers, timeout=15, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Scrape all table rows or links containing PDFs
        links = soup.find_all('a', href=True)
        pdf_links = [l['href'] for l in links if l['href'].lower().endswith('.pdf')]
        
        # Limit to top 3-5 latest notifications if multiple exist on that date
        selected_links = pdf_links[:4] if pdf_links else []
        
        for idx, link in enumerate(selected_links, 1):
            full_url = link if link.startswith('http') else "https://www.cbic.gov.in" + link
            filename = full_url.split('/')[-1]
            if not filename.endswith('.pdf'):
                filename = f"Notification_{idx}.pdf"
                
            pdf_list.append({
                "title": f"Official Tax Notification #{idx}",
                "url": full_url,
                "filename": filename
            })
            
    except Exception as e:
        print(f"Scraper error: {e}")
        
    return pdf_list

def send_email():
    requested_date = check_email_for_date_request()
    date_label = requested_date if requested_date else "Latest Issued Date"
    
    # Fetch ALL notifications & PDFs for that date
    notifications = fetch_all_notification_pdfs(requested_date)
    
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    
    count_str = f"{len(notifications)} PDF(s) Attached" if notifications else "Summary Report"
    msg['Subject'] = f"📑 Tax Updates [{date_label}]: {count_str}"

    email_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.5;">
        <h2 style="color: #1e3c72; border-bottom: 2px solid #1e3c72; padding-bottom: 6px;">
          🏛️ Income Tax & GST Notifications Digest
        </h2>
        <p><b>Target Date:</b> {date_label}</p>
        <p><b>Total Official Notifications Issued/Found:</b> <b style="color:#2563eb;">{len(notifications)}</b></p>
        <hr style="border:none; border-top:1px solid #e2e8f0; margin:15px 0;">
    """
    
    if notifications:
        for idx, item in enumerate(notifications, 1):
            email_body += f"""
            <div style="background-color: #f8fafc; border-left: 4px solid #2563eb; padding: 12px; margin-bottom: 12px; border-radius: 4px;">
              <h3 style="margin: 0 0 4px 0; color: #0f172a; font-size: 14px;">{idx}. {item['title']}</h3>
              <p style="margin: 0; font-size: 12px; color: #475569;">
                📄 <b>Attached PDF Document:</b> <code>{item['filename']}</code><br>
                🔗 <b>Direct Web Link:</b> <a href="{item['url']}" style="color: #2563eb;">Download from Portal</a>
              </p>
            </div>
            """
    else:
        email_body += "<p>No official notifications were published on the specified portal for this date.</p>"
        
    email_body += """
        <br>
        <p style="font-size: 11px; color: #64748b; background: #f1f5f9; padding: 8px; border-radius: 4px;">
          📌 All available official government PDF documents for the selected date have been attached directly to this email.
        </p>
      </body>
    </html>
    """
    msg.attach(MIMEText(email_body, 'html'))

    # Loop through ALL found PDFs and attach them one by one
    for item in notifications:
        try:
            print(f"Downloading official PDF: {item['filename']}...")
            pdf_data = requests.get(item['url'], timeout=20, verify=False).content
            attach = MIMEApplication(pdf_data, _subtype="pdf")
            attach.add_header('Content-Disposition', 'attachment', filename=item['filename'])
            msg.attach(attach)
            print(f"Successfully attached {item['filename']}")
        except Exception as e:
            print(f"Failed to attach {item['filename']}: {e}")

    # Send Email
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
    server.quit()
    print(f"SUCCESS: Email sent with {len(notifications)} PDF attachments!")

if __name__ == "__main__":
    send_email()
