import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests


def get_live_gst_news():
    """GST Portal (`services.gst.gov.in`) se live official updates fetch karega"""
    url = "https://services.gst.gov.in/services/api/get/news"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        res = requests.get(url, headers=headers, timeout=10)
        data = res.json()
        news_items = data.get("news", [])[:3]  # Top 3 latest updates

        updates = []
        for item in news_items:
            title = item.get("title", "GST Portal Update")
            date = item.get("date", "Latest")
            updates.append(f"<li><b>[{date}]</b> {title}</li>")

        return "".join(updates) if updates else "<li>No new updates today.</li>"
    except Exception as e:
        print(f"Error fetching GST updates: {e}")
        return "<li>Unable to fetch live GST updates right now.</li>"


def send_email():
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")
    receiver_email = os.getenv("RECEIVER_EMAIL")

    gst_updates_html = get_live_gst_news()

    # Dynamic Real HTML Content (Hardcoded Notifications Removed)
    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333;">
        <div style="background-color: #1a365d; color: white; padding: 15px; text-align: center;">
          <h2>Tax Digest Daily Live Updates</h2>
        </div>
        <div style="padding: 20px;">
          <h3 style="color: #2b6cb0;">Direct Tax Updates (Income Tax / CBDT)</h3>
          <ul>
            <li>Please refer to the <a href="https://www.incometax.gov.in/iec/foportal/latest-news">Income Tax Portal</a> for the latest AY 2026-27 compliance advisories.</li>
          </ul>

          <h3 style="color: #2b6cb0;">Indirect Tax Updates (GST Portal / CBIC)</h3>
          <ul>
            {gst_updates_html}
          </ul>
        </div>
      </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Daily Tax Digest - Real Portal Updates"
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg.attach(MIMEText(html_content, "html"))

    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, [receiver_email], msg.as_string())
        server.quit()
        print("Real Live Data Email Sent Successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")


if __name__ == "__main__":
    send_email()
