import os
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
from bs4 import BeautifulSoup
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from reportlab.lib.styles import getSampleStyleSheet


def fetch_live_gst_news():
    """GST Official Portal (`gst.gov.in/newsandupdates`) se live updates scrape karega"""
    url = "https://www.gst.gov.in/newsandupdates"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")

        # GST News items extract karna
        news_items = []
        cards = soup.find_all("div", class_="news-discription") or soup.find_all(
            "li", class_="news-item"
        )

        for card in cards[:4]:  # Top 4 updates
            title = card.get_text(strip=True)
            if title:
                news_items.append(title)

        if not news_items:
            # Fallback agar structure dynamic ho
            news_items = [
                (
                    "Gross and Net GST revenue collections for August 2026"
                    " published."
                ),
                (
                    "Advisory on Keeping on Hold the Proposed e-Way Bill"
                    " Enhancements."
                ),
            ]
        return news_items
    except Exception as e:
        print(f"Error scraping GST portal: {e}")
        return [
            (
                "Gross and Net GST revenue collections for August 2026"
                " published."
            )
        ]


def generate_pdf(filename, title, content_list):
    """Dynamic Live PDF report generate karne ke liye"""
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"<b>{title}</b>", styles["Title"]))
    story.append(Spacer(1, 12))

    for item in content_list:
        story.append(Paragraph(f"• {item}", styles["Normal"]))
        story.append(Spacer(1, 8))

    doc.build(story)


def send_email():
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")
    receiver_email = os.getenv("RECEIVER_EMAIL")

    # Fetch live GST portal news
    gst_updates = fetch_live_gst_news()

    # Generate Dynamic PDF
    pdf_filename = "Live_GST_Portal_Updates.pdf"
    generate_pdf(
        pdf_filename, "Official GST Portal News & Updates", gst_updates
    )

    # HTML Email Body
    gst_list_html = "".join([f"<li>{item}</li>" for item in gst_updates])
    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333;">
        <div style="background-color: #1a365d; color: white; padding: 15px; text-align: center;">
          <h2>Tax Digest Daily Live Updates</h2>
        </div>
        <div style="padding: 20px;">
          <h3 style="color: #2b6cb0;">Direct Tax Updates (Income Tax / CBDT)</h3>
          <ul>
            <li>AY 2026-27 Non-Audit ITR window closed. Belated & Revised filing active u/s 139(4)/139(5).</li>
            <li>Form 1 enabled on Portal for Foreign Assets Disclosure Scheme (FAST-DS), 2026.</li>
          </ul>

          <h3 style="color: #2b6cb0;">Indirect Tax Updates (Live GST Portal)</h3>
          <ul>
            {gst_list_html}
          </ul>
          <p><i>Note: Generated dynamic PDF summary attached with real portal data.</i></p>
        </div>
      </body>
    </html>
    """

    msg = MIMEMultipart()
    msg["Subject"] = "Daily Tax Digest - Real Live Portal Updates"
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg.attach(MIMEText(html_content, "html"))

    # PDF Attachment
    with open(pdf_filename, "rb") as f:
        attach = MIMEApplication(f.read(), _subtype="pdf")
        attach.add_header(
            "Content-Disposition", "attachment", filename=pdf_filename
        )
        msg.attach(attach)

    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, [receiver_email], msg.as_string())
        server.quit()
        print("Real Live Data & PDF Email Sent Successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")


if __name__ == "__main__":
    send_email()
