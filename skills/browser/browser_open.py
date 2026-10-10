import webbrowser
from urllib.parse import quote_plus


class BrowserOpen:

    def open(self, url):

        if not url.startswith("http"):
            url = "https://" + url

        webbrowser.open_new_tab(url)

    def google(self):

        self.open("https://www.google.com")

    def youtube(self):

        self.open("https://www.youtube.com")

    def gmail(self):

        self.open("https://mail.google.com")

    def search_google(self, query):

        self.open(
            f"https://www.google.com/search?q={quote_plus(query)}"
        )

    def search_youtube(self, query):

        self.open(
            f"https://www.youtube.com/results?search_query={quote_plus(query)}"
        )