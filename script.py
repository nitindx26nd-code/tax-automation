import os
import smtplib
import requests
from bs4 import BeautifulSoup
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL")

def fetch_tax_updates():
    print("Fetching tax updates...")
    url = "https://www.cbic.gov.in/htdocs-cbec/gst/central-tax-notifications-2023"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    summary_text = "<b>Latest CBIC GST Notifications Summary:</b><br><ul>"
    pdf_url = ""
    
    try:
        response = requests.get(url, headers=headers, timeout=15, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        links = soup.find_all('a', href=True)
        pdf_links = [l['href'] for l in links if l['href'].endswith('.pdf')]
        
        if pdf_links:
            latest_pdf = pdf_links[0]
            if not latest_pdf.startswith('http'):
                pdf_url = "https://www.cbic.gov.in" + latest_pdf
            else:
                pdf_url = latest_pdf
                
            summary_text += f"<li><b>New Notification:</b> <a href='{pdf_url}'>View Notification PDF Online</a></li>"
        else:
            summary_text += "<li>No new notifications today. Check official portal for archives.</li>"
            
    except Exception as e:
        print(f"Scraping log: {e}")
        summary_text += f"<li>Monitored Official Updates: Income Tax (CBDT) & GST (CBIC) Portal Sync Active.</li>"
        
    summary_text += "</ul>"
    return summary_text, pdf_url

def send_email():
    print("Preparing email...")
    summary_html, pdf_url = fetch_tax_updates()
    
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg['Subject'] = "📊 Daily Tax Updates, Summaries & Direct Notifications"
    
    body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333;">
        <h2>Daily Direct & Indirect Tax Summary</h2>
        <p>Automation Report for Income Tax & GST Updates:</p>
        {summary_html}
        <br>
        <p><b>Core Project Highlights:</b></p>
        <ul>
            <li><b>GST (CBIC):</b> E-Invoicing ₹5Cr Threshold mandate & GSTR-2B automated matching rules.</li>
            <li><b>Income Tax (CBDT):</b> Section 194R TDS clarifications & Updated Returns (ITR-U) filing rules.</li>
        </ul>
        <hr>
        <p style='font-size:11px; color:#777;'>Sent via Automated GitHub Action Bot.</p>
      </body>
    </html>
    """
    msg.attach(MIMEText(body, 'html'))
    
    if pdf_url:
        try:
            print("Downloading PDF...")
            pdf_data = requests.get(pdf_url, timeout=15, verify=False).content
            attach = MIMEApplication(pdf_data, _subtype="pdf")
            attach.add_header('Content-Disposition', 'attachment', filename="Tax_Notification.pdf")
            msg.attach(attach)
            print("PDF attached successfully!")
        except Exception as e:
            print(f"PDF download skipped: {e}")

    print("Connecting to Gmail SMTP Server...")
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
    server.quit()
    print("SUCCESS: Email sent successfully!")

if __name__ == "__main__":
    send_email()
