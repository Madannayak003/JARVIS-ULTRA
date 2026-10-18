import urllib.parse
import time

from skills.browser.browser_controller import browser


class NavigationEngine:

    def open(self, url):

        if not url:
            return False

        url = str(url).strip()

        if not url:
            return False

        if not urllib.parse.urlparse(url).scheme:
            url = "https://" + url

        started_at = time.monotonic()
        print(f"[NAVIGATION] Requested URL: {url}")

        try:
            result = browser.open(url)
            if result is not True:
                print(
                    "[NAVIGATION FAILED] Browser open returned "
                    f"{result!r} | elapsed={time.monotonic() - started_at:.2f}s"
                )
                return False

            print(
                "[NAVIGATION COMPLETE] "
                f"{url} | elapsed={time.monotonic() - started_at:.2f}s"
            )
            return True

        except Exception as error:
            print(
                "[NAVIGATION ERROR] "
                f"{type(error).__name__}: {error} | "
                f"elapsed={time.monotonic() - started_at:.2f}s"
            )
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
