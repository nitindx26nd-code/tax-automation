import requests


def fetch_gst_portal_news():
    # GST Portal ka official News & Updates public endpoint
    url = "https://services.gst.gov.in/services/api/get/news"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()

        # Latest updates extract karne ke liye
        news_list = []
        for item in data.get("news", [])[:5]:  # Top 5 latest news
            title = item.get("title")
            date = item.get("date")
            link = f"https://www.gst.gov.in/newsandupdates/read/{item.get('id')}"
            news_list.append({"title": title, "date": date, "link": link})

        return news_list
    except Exception as e:
        print(f"Error fetching GST news: {e}")
        return []
