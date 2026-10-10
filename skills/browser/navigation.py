import urllib.parse

from skills.browser.browser_controller import browser


class NavigationEngine:

    def open(self, url):

        if not url:
            return False

        url = str(url).strip()

        if not url:
            return False

        print(f"[NAVIGATION] {url}")

        try:
            browser.open(url)
            return True

        except Exception as e:
            print(f"[NAVIGATION ERROR] {e}")
            return False


    def google(self, query):

        if not query:
            return False

        url = (
            "https://www.google.com/search?q="
            + urllib.parse.quote(str(query))
        )

        return self.open(url)


    def youtube(self, query):

        if not query:
            return False

        url = (
            "https://www.youtube.com/results?search_query="
            + urllib.parse.quote(str(query))
        )

        return self.open(url)


    def github(self, query):

        if not query:
            return False

        url = (
            "https://github.com/search?q="
            + urllib.parse.quote(str(query))
        )

        return self.open(url)


    def chatgpt(self, query):

        if not query:
            return False

        url = (
            "https://chat.openai.com/?q="
            + urllib.parse.quote(str(query))
        )

        return self.open(url)


navigation = NavigationEngine()