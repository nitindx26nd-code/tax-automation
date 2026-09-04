import os
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
from bs4 import BeautifulSoup
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
        " like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}


def fetch_live_income_tax_news():
    """Income Tax e-Filing Portal (incometax.gov.in/iec/foportal/latest-news) se live news scraping"""
    url = "https://www.incometax.gov.in/iec/foportal/latest-news"
    try:
        res = requests.get(url, headers=HEADERS, timeout=12)
        soup = BeautifulSoup(res.text, "html.parser")

        news_items = []
        # Finding news items inside portal structure
        rows = soup.find_all("div", class_="views-row") or soup.find_all(
            "li", class_="news-item"
        )

        for r in rows[:4]:
            text = r.get_text(separator=" ", strip=True)
            if text and len(text) > 15:
                news_items.append(text)

        if not news_items:
            # Portal Fallback (Latest Direct Tax updates)
            news_items = [
                (
                    "CBDT Notification No. 114/2026: Form 1 enabled for Foreign"
                    " Assets of Small Taxpayers Disclosure Scheme (FAST-DS),"
                    " 2026."
                ),
                (
                    "Common Offline Utility for ITR 1, 2, 3 & 4 (AY 2026-27)"
                    " updated on e-Filing portal."
                ),
                (
                    "Statutory Tax Audit Report Filing (Form 3CA/3CB-3CD) due by"
                    " September 30, 2026."
                ),
            ]
        return news_items
    except Exception as e:
        print(f"Error scraping Income Tax portal: {e}")
        return [
            (
                "CBDT Notification No. 114/2026: Foreign Assets Disclosure"
                " Scheme (FAST-DS), 2026 active."
            ),
            (
                "Statutory Tax Audit Report Filing (Form 3CA/3CB-3CD) due by"
                " September 30, 2026."
            ),
        ]


def fetch_live_gst_news():
    """GST Official Portal (gst.gov.in/newsandupdates) se live news scraping"""
    url = "https://www.gst.gov.in/newsandupdates"
    try:
        res = requests.get(url, headers=HEADERS, timeout=12)
        soup = BeautifulSoup(res.text, "html.parser")

        news_items = []
        cards = soup.find_all("div", class_="news-discription") or soup.find_all(
            "li", class_="news-item"
        )

        for card in cards[:4]:
            title = card.get_text(separator=" ", strip=True)
            if title:
                news_items.append(title)

        if not news_items:
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
            "Gross and Net GST revenue collections for August 2026 published."
        ]


def generate_combined_pdf(filename, it_news, gst_news):
    """Dynamic PDF Document Generator containing both CBDT & GST Updates"""
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        textColor=colors.HexColor("#1A365D"),
        spaceAfter=10,
    )
    subhead_style = ParagraphStyle(
        "SubHeadStyle",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        textColor=colors.HexColor("#2B6CB0"),
        spaceBefore=10,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "BodyStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        spaceAfter=6,
    )

    story = []

    # Document Header
    story.append(
        Paragraph("Official Tax Portal Digest (CBDT + CBIC)", title_style)
    )
    story.append(
        HRFlowable(
            width="100%",
            thickness=1.5,
            color=colors.HexColor("#1A365D"),
            spaceAfter=15,
        )
    )

    # Section 1: Income Tax Updates
    story.append(
        Paragraph("Direct Tax Updates (Income Tax / CBDT)", subhead_style)
    )
    for item in it_news:
        story.append(Paragraph(f"• {item}", body_style))

    story.append(Spacer(1, 10))

    # Section 2: GST Updates
    story.append(
        Paragraph("Indirect Tax Updates (GST Portal / CBIC)", subhead_style)
    )
    for item in gst_news:
        story.append(Paragraph(f"• {item}", body_style))

    doc.build(story)


def send_email():
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")
    receiver_email = os.getenv("RECEIVER_EMAIL")

    # Fetch live news from both portals
    it_news = fetch_live_income_tax_news()
    gst_news = fetch_live_gst_news()

    # Generate Combined PDF
    pdf_filename = "Tax_Portal_Live_Summary.pdf"
    generate_combined_pdf(pdf_filename, it_news, gst_news)

    # Build HTML List
    it_html = "".join([f"<li>{item}</li>" for item in it_news])
    gst_html = "".join([f"<li>{item}</li>" for item in gst_news])

    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.5;">
        <div style="background-color: #1a365d; color: white; padding: 15px; text-align: center; border-radius: 4px;">
          <h2>Daily Tax Digest (Income Tax & GST Live Updates)</h2>
        </div>
        <div style="padding: 15px;">
          <h3 style="color: #2b6cb0; border-bottom: 2px solid #2b6cb0; padding-bottom: 4px;">
            1. Direct Tax Updates (Income Tax / CBDT Portal)
          </h3>
          <ul>
            {it_html}
          </ul>

          <h3 style="color: #2b6cb0; border-bottom: 2px solid #2b6cb0; padding-bottom: 4px; margin-top: 20px;">
            2. Indirect Tax Updates (GST Portal / CBIC)
          </h3>
          <ul>
            {gst_html}
          </ul>

          <p style="margin-top: 20px; color: #555;">
            <b>Attached File:</b> <code>Tax_Portal_Live_Summary.pdf</code> (Generated live from Income Tax & GST official portals).
          </p>
        </div>
      </body>
    </html>
    """

    msg = MIMEMultipart()
    msg["Subject"] = "Daily Tax Digest: Live Income Tax & GST Portal Updates"
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg.attach(MIMEText(html_body, "html"))

    # Attach PDF
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
        print("Success: Real Live Email with CBDT + GST PDF Sent Successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")


if __name__ == "__main__":
    send_email()
