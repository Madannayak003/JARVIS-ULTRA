from playwright.sync_api import sync_playwright
import threading
import time
from concurrent.futures import ThreadPoolExecutor
import re
from urllib.parse import urlsplit, urlunsplit

from skills.browser.browser_config import BrowserConfigurationError
from skills.browser.browser_resolver import BrowserExecutableNotFoundError
from skills.browser.browser_runtime import BrowserRuntime, BrowserRuntimeError

# * =========================================================
# * GLOBAL BROWSER LOCK
# * =========================================================

_browser_lock = threading.RLock()


# * =========================================================
# * BROWSER WORKER
# * =========================================================
#
# ! IMPORTANT:
#
# ! Playwright Sync API must NOT execute inside Gemini Live's
# * asyncio event loop.
#
# * All browser operations are therefore routed through ONE
# * dedicated worker thread.
#
# * This worker permanently owns:
#
# * Playwright
# * Browser
# * Page
#
# * This also keeps Playwright objects on the same thread.
# * =========================================================

class BrowserWorker:

    def __init__(self):

        self.executor = ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix="JARVIS-BrowserWorker",
        )

        self.worker_thread_id = None

    def run(self, function, *args, **kwargs):

        # * -------------------------------------------------
        # * Already inside browser worker
        # * -------------------------------------------------

        if (
            self.worker_thread_id
            == threading.get_ident()
        ):

            return function(
                *args,
                **kwargs,
            )

        # * -------------------------------------------------
        # * Send operation to dedicated browser thread
        # * -------------------------------------------------

        future = self.executor.submit(
            self._execute,
            function,
            args,
            kwargs,
        )

        return future.result()

    def _execute(
        self,
        function,
        args,
        kwargs,
    ):

        self.worker_thread_id = threading.get_ident()

        return function(
            *args,
            **kwargs,
        )

    def shutdown(self):

        try:

            self.executor.shutdown(
                wait=False,
                cancel_futures=True,
            )

        except Exception:

            pass


_browser_worker = BrowserWorker()


# * =========================================================
# * BROWSER CONTROLLER
# * =========================================================

class BrowserController:

    def __init__(self):

        # * -------------------------------------------------
        # * Playwright state belongs to browser worker thread
        # * -------------------------------------------------

        self.playwright = None
        self.browser = None
        self.page = None
        self.runtime = None
        
        # * -------------------------------------------------
        # * Previous browser page
        # * -------------------------------------------------
        #
        # * Used when JARVIS opens a new tab and the user says
        # * "go back". A newly-created tab has no history, so
        # * JARVIS should return to the previous tab.
        #
        self.previous_page = None
        
    # * =====================================================
    # * BROWSER CONTEXT SYNCHRONIZATION
    # * =====================================================

    def _sync_context(self):

        try:

            from core.browser_context import browser_context

            if (
                not self.page
                or self.page.is_closed()
            ):

                return

            url = self.page.url or ""

            title = ""

            try:

                title = self.page.title()

            except Exception:

                pass

            site = ""

            if "youtube.com" in url:

                site = "youtube"

            elif "google.com" in url:

                site = "google"

            elif "github.com" in url:

                site = "github"

            elif "gmail.com" in url:

                site = "gmail"

            elif "spotify.com" in url:

                site = "spotify"

            elif url:

                site = url.split(
                    "://",
                    1
                )[-1].split(
                    "/",
                    1
                )[0]

            browser_context.set_page(
                url=url,
                site=site,
                title=title,
            )

        except Exception as error:

            print(
                "[Browser Context] "
                f"Sync failed: {error}"
            )

    # * =====================================================
    # * INTERNAL EXECUTION
    # * =====================================================

    def _run_browser(
        self,
        function,
        *args,
        **kwargs,
    ):

        return _browser_worker.run(
            function,
            *args,
            **kwargs,
        )

    # * =====================================================
    # * START
    # * =====================================================

    def start(self):

        return self._run_browser(
            self._start_impl
        )

    def _start_impl(self):

        print(
            f"[Browser THREAD] "
            f"{threading.current_thread().name} | "
            f"ID: {threading.get_ident()}"
        )

        # * -------------------------------------------------
        # * Already connected
        # * -------------------------------------------------

        try:

            if (
                self.browser
                and self.browser.is_connected()
                and self.page
                and not self.page.is_closed()
            ):

                return True

        except Exception:

            pass

        # ! This runtime owns a dedicated browser process. It never attaches to
        # * an arbitrary CDP endpoint that happens to already use a local port.
        try:

            if self.runtime is None:
                self.runtime = BrowserRuntime()

            endpoint = self.runtime.ensure_running()

            print(
                "[Browser] Starting __ASSISTANT_NAME__ Browser..."
            )

        except (
            BrowserConfigurationError,
            BrowserExecutableNotFoundError,
            BrowserRuntimeError,
            OSError,
            ValueError,
        ) as error:

            print(
                "[Browser ERROR] "
                f"{error}"
            )

            if self.runtime:
                self.runtime.stop()
            self.runtime = None

            return False

        # * -------------------------------------------------
        # * Start Playwright only after the owned CDP endpoint is ready.
        # * -------------------------------------------------

        if not self.playwright:

            print(
                "[Browser] Starting Playwright..."
            )

            self.playwright = (
                sync_playwright().start()
            )

        # * -------------------------------------------------
        # * Connect through CDP
        # * -------------------------------------------------

        try:

            self.browser = (
                self.playwright
                .chromium
                .connect_over_cdp(
                    endpoint
                )
            )

            print(
                "[Browser] Connected to __ASSISTANT_NAME__ Chrome"
            )

            # * -------------------------------------------------
            # * Find existing YouTube tab
            # * -------------------------------------------------

            for context in self.browser.contexts:

                for page in context.pages:

                    try:

                        if "youtube.com" in page.url:

                            self.page = page

                            print(
                                "[Browser] "
                                "YouTube tab attached"
                            )

                            return True

                    except Exception:

                        continue

            # * -------------------------------------------------
            # * Use first available page
            # * -------------------------------------------------

            if not self.browser.contexts:

                print(
                    "[Browser ERROR] "
                    "No browser context available"
                )

                return False

            context = self.browser.contexts[0]

            if context.pages:

                self.page = context.pages[0]

            else:

                self.page = context.new_page()

            print(
                "[Browser] Chrome attached"
            )

            return True

        except Exception as e:

            print(
                "[Browser ERROR] "
                f"CDP connection failed: {e}"
            )

            self.browser = None
            self.page = None
            if self.runtime:
                self.runtime.stop()

            return False

    # * =====================================================
    # * OPEN
    # * =====================================================

    def open(self, url):

        return self._run_browser(
            self._open_impl,
            url,
        )

    def _open_impl(self, url):

        if not url:

            return False

        print(
            f"[Browser OPEN THREAD] "
            f"{threading.current_thread().name} | "
            f"{threading.get_ident()}"
        )

        with _browser_lock:

            try:

                if not self._start_impl():

                    print(
                        "[Browser] "
                        "Browser could not start"
                    )

                    return False

                if not self.browser or not self.page:

                    print(
                        "[Browser] "
                        "Browser not connected"
                    )

                    return False

                print(
                    f"[Browser] Opening: {url}"
                )

                self.page.goto(
                    str(url),
                    wait_until="domcontentloaded",
                    timeout=15000,
                )
                
                print(
                    f"[Browser OPEN DEBUG] "
                    f"GOTO COMPLETE | URL: {self.page.url} | "
                    f"TITLE: {self.page.title()}"
                )

                self.page.bring_to_front()

                self._sync_context()

                print(
                    "[Browser] "
                    "Page opened in __ASSISTANT_NAME__ Chrome"
                )

                return True
            
            except Exception as e:

                print(
                    "[Browser ERROR] "
                    f"Open failed: {e}"
                )

                return False

    # * =====================================================
    # * READ CURRENT PAGE
    # * =====================================================

    def read_current_page(self, max_chars=12000, timeout_ms=10000):
        """Extract readable text from the existing current page.

        This deliberately uses the existing browser worker and page. It never
        creates a tab or starts another browser runtime.
        """
        return self._run_browser(
            self._read_current_page_impl,
            max_chars,
            timeout_ms,
        )

    @staticmethod
    def _safe_page_url(url):
        """Remove credentials, query strings, and fragments from a URL."""
        raw = str(url or "").strip()
        if not raw:
            return ""
        try:
            parsed = urlsplit(raw)
            hostname = parsed.hostname or ""
            netloc = hostname
            if parsed.port:
                netloc = f"{hostname}:{parsed.port}"
            return urlunsplit((parsed.scheme, netloc, parsed.path, "", ""))
        except Exception:
            return raw.split("?", 1)[0].split("#", 1)[0]

    @staticmethod
    def _redact_page_text(text):
        """Redact common inline secret assignments from extracted text."""
        pattern = re.compile(
            r"(?im)\b(password|passcode|api[_ -]?key|access[_ -]?token|"
            r"refresh[_ -]?token|authorization|cookie|secret)\b\s*[:=]\s*[^\s,;]+"
        )
        return pattern.sub(r"\1: [REDACTED]", text)

    def _read_current_page_impl(self, max_chars=12000, timeout_ms=10000):
        with _browser_lock:
            try:
                max_chars = max(1, min(int(max_chars), 50000))
                timeout_ms = max(1000, min(int(timeout_ms), 15000))

                if not self._start_impl() or not self.page:
                    return {
                        "ok": False,
                        "status": "unavailable",
                        "extraction_status": "unavailable",
                        "url": "",
                        "title": "",
                        "content": "",
                        "message": "No browser page is available to read.",
                    }

                if self.page.is_closed():
                    return {
                        "ok": False,
                        "status": "unavailable",
                        "extraction_status": "unavailable",
                        "url": "",
                        "title": "",
                        "content": "",
                        "message": "The current browser page is closed.",
                    }

                safe_url = self._safe_page_url(getattr(self.page, "url", ""))
                try:
                    title = str(self.page.title() or "").strip()[:500]
                except Exception:
                    title = ""

                body = self.page.locator("body")
                text = str(body.inner_text(timeout=timeout_ms) or "")
                text = self._redact_page_text(text)
                text = text.strip()
                truncated = len(text) > max_chars
                text = text[:max_chars]

                if not text:
                    return {
                        "ok": False,
                        "status": "empty_content",
                        "extraction_status": "empty",
                        "url": safe_url,
                        "title": title,
                        "content": "",
                        "truncated": False,
                        "message": "The page opened, but no readable text was extracted.",
                    }

                self._sync_context()
                return {
                    "ok": True,
                    "status": "extracted",
                    "extraction_status": "success",
                    "url": safe_url,
                    "title": title,
                    "content": text,
                    "content_length": len(text),
                    "truncated": truncated,
                    "message": "Readable page content extracted successfully.",
                }
            except Exception as exc:
                return {
                    "ok": False,
                    "status": "extraction_failed",
                    "extraction_status": "failed",
                    "url": self._safe_page_url(getattr(self.page, "url", "")) if self.page else "",
                    "title": "",
                    "content": "",
                    "message": f"Page content extraction failed: {exc}",
                }

    # * =====================================================
    # * GOOGLE SEARCH
    # * =====================================================

    def search_google(self, query):

        return self._run_browser(
            self._search_google_impl,
            query,
        )

    def _search_google_impl(self, query):

        print(
            f"[Browser GOOGLE THREAD] "
            f"{threading.current_thread().name} | "
            f"{threading.get_ident()}"
        )

        if not query:

            return False

        with _browser_lock:

            try:

                import urllib.parse

                encoded_query = (
                    urllib.parse.quote(
                        str(query)
                    )
                )

                if not self._start_impl():

                    print(
                        "[Google] "
                        "Browser not connected"
                    )

                    return False

                if not self.browser or not self.page:

                    return False

                url = (
                    "https://www.google.com/search?q="
                    + encoded_query
                )

                print(
                    f"[Google] Searching: {query}"
                )

                print(
                    f"[Google DEBUG] BEFORE GOTO | URL: {self.page.url}"
                )

                print(
                    "[Google DEBUG] GOTO START"
                )

                self.page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=15000,
                )

                print(
                    f"[Google DEBUG] GOTO COMPLETE | URL: {self.page.url}"
                )

                self.page.bring_to_front()

                print(
                    f"[Google DEBUG] AFTER BRING TO FRONT | URL: {self.page.url}"
                )

                self._sync_context()

                print(
                    f"[Google DEBUG] AFTER SYNC | URL: {self.page.url}"
                )

                # * =========================================================
                # * GOOGLE SEARCH RESULT EXTRACTION
                # * =========================================================

                results = []

                try:

                    links = self.page.locator(
                        "div.MjjYud a:has(h3)"
                    )

                    count = links.count()

                    print(
                        f"[Google] Found {count} candidate result link(s)"
                    )

                    for index in range(
                        min(count, 10)
                    ):

                        try:

                            link = links.nth(index)

                            href = link.get_attribute(
                                "href",
                                timeout=2000,
                            )

                            title = link.locator(
                                "h3"
                            ).inner_text(
                                timeout=2000
                            )

                            if not href or not title:

                                continue

                            results.append({
                                "title": title.strip(),
                                "url": href.strip(),
                                "platform": "google",
                                "result_type": "search",
                            })

                        except Exception:

                            continue

                except Exception as e:

                    print(
                        "[Google] "
                        f"Result extraction failed: {e}"
                    )


                # * =========================================================
                # * SAVE RESULTS
                # * =========================================================

                from core.browser_context import browser_context

                browser_context.set_search(
                    query=query,
                    platform="google",
                    results=results,
                )

                print(
                    f"[Google] Captured "
                    f"{len(results)} search result(s)"
                )

                print(
                    "[Google] "
                    "Search opened in __ASSISTANT_NAME__ Chrome"
                )

                return True

            except Exception as e:

                print(
                    "[Google ERROR] "
                    f"Search failed: {e}"
                )

                return False

    # * =====================================================
    # * YOUTUBE SEARCH
    # * =====================================================

    def search_youtube(self, query):

        return self._run_browser(
            self._search_youtube_impl,
            query,
        )

    def _search_youtube_impl(self, query):

        print(
            f"[Browser SEARCH THREAD] "
            f"{threading.current_thread().name} | "
            f"{threading.get_ident()}"
        )

        if not query:

            return False

        with _browser_lock:

            try:

                if not self._start_impl():

                    print(
                        "[YouTube] "
                        "Browser not connected"
                    )

                    return False

                if not self.browser or not self.page:

                    print(
                        "[YouTube] "
                        "Browser not connected"
                    )

                    return False

                import urllib.parse

                encoded_query = (
                    urllib.parse.quote(
                        str(query)
                    )
                )

                url = (
                    "https://www.youtube.com/results"
                    "?search_query="
                    + encoded_query
                )

                print(
                    f"[YouTube] Searching: {query}"
                )

                self.page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=15000,
                )

                self.page.bring_to_front()
                
                self._sync_context()

                print(
                    "[YouTube] "
                    "Search opened in __ASSISTANT_NAME__ Chrome"
                )

                return True

            except Exception as e:

                print(
                    "[YouTube ERROR] "
                    f"Search failed: {e}"
                )

                return False

    # * =====================================================
    # * GITHUB SEARCH
    # * =====================================================

    def search_github(self, query):

        return self._run_browser(
            self._search_github_impl,
            query,
        )

    def _search_github_impl(self, query):

        print(
            f"[Browser GITHUB THREAD] "
            f"{threading.current_thread().name} | "
            f"{threading.get_ident()}"
        )

        if not query:

            return False

        try:

            if not self._start_impl():

                return False

            if not self.browser or not self.page:

                return False

            import urllib.parse

            url = (
                "https://github.com/search?q="
                + urllib.parse.quote(
                    str(query)
                )
            )

            print(
                f"[GitHub] Searching: {query}"
            )

            self.page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=15000,
            )

            self.page.bring_to_front()
            
            self._sync_context()

            print(
                "[GitHub] "
                "Search opened in __ASSISTANT_NAME__ Chrome"
            )

            return True

        except Exception as e:

            print(
                f"[GitHub ERROR] {e}"
            )

            return False

    # * =====================================================
    # * PLAY VIDEO
    # * =====================================================

    def play_video(self, video_id):

        return self._run_browser(
            self._play_video_impl,
            video_id,
        )

    def _play_video_impl(self, video_id):

        if not video_id:

            return False

        with _browser_lock:

            return self._play_video_locked(
                video_id
            )

    def _play_video_locked(self, video_id):

        print(
            f"[Browser PLAY THREAD] "
            f"{threading.current_thread().name} | "
            f"{threading.get_ident()}"
        )

        url = (
            "https://www.youtube.com/watch?v="
            f"{video_id}"
        )

        print(
            "[YouTube] "
            f"Opening in __ASSISTANT_NAME__ Chrome: {url}"
        )

        try:

            if not self._start_impl():

                return False

            if not self.browser:

                return False

            context = (
                self.browser.contexts[0]
            )

            youtube_page = None

            for page in context.pages:

                try:

                    if "youtube.com" in page.url:

                        youtube_page = page

                        break

                except Exception:

                    continue

            if not youtube_page:

                youtube_page = (
                    context.new_page()
                )

            self.page = youtube_page

            self.page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=15000,
            )

            self.page.bring_to_front()
            
            self._sync_context()

            print(
                "[YouTube] "
                "Video opened in __ASSISTANT_NAME__ Chrome"
            )

            self._skip_ad_impl()

            return True

        except Exception as e:

            print(
                f"[YouTube ERROR] {e}"
            )

            return False

    # * =====================================================
    # * PLAY FIRST VIDEO
    # * =====================================================

    def play_first_video(self):

        return self._run_browser(
            self._play_first_video_impl
        )

    def _play_first_video_impl(self):

        try:

            if not self._start_impl():

                return False

            if not self.browser or not self.page:

                print(
                    "[YouTube] "
                    "Browser not connected"
                )

                return False

            if "youtube.com" not in self.page.url:

                print(
                    "[YouTube] "
                    "Current page is not YouTube"
                )

                return False

            first_video = (
                self.page
                .locator(
                    "ytd-video-renderer "
                    "a#video-title"
                )
                .first
            )

            if not first_video.is_visible():

                print(
                    "[YouTube] "
                    "First video not found"
                )

                return False

            first_video.click()

            self.page.bring_to_front()

            print(
                "[YouTube] "
                "First video opened in __ASSISTANT_NAME__ Chrome"
            )

            return True

        except Exception as e:

            print(
                "[YouTube ERROR] "
                f"First video failed: {e}"
            )

            return False

    # * =====================================================
    # * SKIP AD
    # * =====================================================

    def skip_ad(self):

        return self._run_browser(
            self._skip_ad_impl
        )

    def _skip_ad_impl(self):

        print(
            f"[Browser AD THREAD] "
            f"{threading.current_thread().name} | "
            f"{threading.get_ident()}"
        )

        if not self.page:

            return False

        try:

            for _ in range(20):

                button = (
                    self.page.get_by_text(
                        "Skip",
                        exact=True,
                    )
                )

                if button.count() > 0:

                    button.first.click()

                    print(
                        "[YouTube] Ad skipped"
                    )

                    return True

                time.sleep(0.25)

        except Exception as e:

            print(
                "[YouTube] "
                f"Skip ad failed: {e}"
            )

        print(
            "[YouTube] "
            "No skippable ad found"
        )

        return False

    # * =====================================================
    # * YOUTUBE KEY
    # * =====================================================

    def youtube_key(self, key):

        return self._run_browser(
            self._youtube_key_impl,
            key,
        )

    def _youtube_key_impl(self, key):

        print(
            f"[Browser KEY THREAD] "
            f"{threading.current_thread().name} | "
            f"{threading.get_ident()}"
        )

        try:

            if not self._start_impl():

                return False

            if not self.browser:

                print(
                    "[YouTube] "
                    "Browser not connected"
                )

                return False

            youtube_page = None

            # * -------------------------------------------------
            # * Prefer tracked page
            # * -------------------------------------------------

            try:

                if (
                    self.page
                    and not self.page.is_closed()
                    and "youtube.com" in self.page.url
                ):

                    youtube_page = self.page

            except Exception:

                youtube_page = None

            # * -------------------------------------------------
            # * Find YouTube video page
            # * -------------------------------------------------

            if not youtube_page:

                for context in self.browser.contexts:

                    for page in context.pages:

                        try:

                            if (
                                "youtube.com/watch"
                                in page.url
                                and not page.is_closed()
                            ):

                                youtube_page = page

                                break

                        except Exception:

                            continue

                    if youtube_page:

                        break

            if not youtube_page:

                print(
                    "[YouTube] "
                    "YouTube video page not found"
                )

                return False

            self.page = youtube_page

            self.page.bring_to_front()

            self.page.keyboard.press(
                key
            )

            print(
                "[YouTube] "
                f"Key sent to YouTube page: {key}"
            )

            return True

        except Exception as e:

            print(
                "[YouTube CONTROL ERROR] "
                f"{e}"
            )

            return False

    # * =====================================================
    # * PAUSE / RESUME
    # * =====================================================

    def pause_video(self):

        return self.youtube_key("k")

    def resume_video(self):

        return self.youtube_key("k")

    def fullscreen(self):

        return self.youtube_key("f")

    # * =====================================================
    # * NEXT VIDEO
    # * =====================================================

    def next_video(self):

        return self._run_browser(
            self._next_video_impl
        )

    def _next_video_impl(self):

        try:

            if not self._start_impl():

                return False

            if not self.browser:

                return False

            youtube_page = None

            for context in self.browser.contexts:

                for page in context.pages:

                    try:

                        if (
                            "youtube.com/watch"
                            in page.url
                        ):

                            youtube_page = page

                            break

                    except Exception:

                        continue

                if youtube_page:

                    break

            if not youtube_page:

                print(
                    "[YouTube] "
                    "YouTube video page not found"
                )

                return False

            self.page = youtube_page

            self.page.bring_to_front()

            self.page.keyboard.press(
                "Shift+n"
            )

            print(
                "[YouTube] "
                "Next video command sent"
            )

            return True

        except Exception as e:

            print(
                f"[YouTube NEXT ERROR] {e}"
            )

            return False

    # * =====================================================
    # * PREVIOUS VIDEO
    # * =====================================================

    def previous_video(self):

        return self._run_browser(
            self._previous_video_impl
        )

    def _previous_video_impl(self):

        try:

            if not self._start_impl():

                return False

            if not self.browser:

                return False

            youtube_page = None

            for context in self.browser.contexts:

                for page in context.pages:

                    try:

                        if (
                            "youtube.com/watch"
                            in page.url
                        ):

                            youtube_page = page

                            break

                    except Exception:

                        continue

                if youtube_page:

                    break

            if not youtube_page:

                print(
                    "[YouTube] "
                    "YouTube video page not found"
                )

                return False

            self.page = youtube_page

            self.page.bring_to_front()

            self.page.keyboard.press(
                "Shift+P"
            )

            print(
                "[YouTube] "
                "Previous video command sent"
            )

            return True

        except Exception as e:

            print(
                f"[YouTube PREVIOUS ERROR] {e}"
            )

            return False

    # * =====================================================
    # * NEW TAB
    # * =====================================================

    def new_tab(self):

        return self._run_browser(
            self._new_tab_impl
        )

    def _new_tab_impl(self):

        try:

            if not self._start_impl():

                return False

            if not self.browser:

                return False

            context = self.browser.contexts[0]

            # * -------------------------------------------------
            # * Remember current tab
            # * -------------------------------------------------

            old_page = self.page

            if (
                old_page
                and not old_page.is_closed()
            ):

                self.previous_page = old_page

            # * -------------------------------------------------
            # * Create new tab
            # * -------------------------------------------------

            new_page = context.new_page()

            self.page = new_page

            self.page.bring_to_front()

            # * -------------------------------------------------
            # * Load Chrome's normal new-tab page
            # * -------------------------------------------------

            try:

                self.page.goto(
                    "https://www.google.com",
                    wait_until="domcontentloaded",
                    timeout=10000,
                )

            except Exception as e:

                print(
                    f"[Browser NEW TAB] "
                    f"New-tab navigation notice: {e}"
                )
                
            self._sync_context()

            print(
                "[Browser] "
                "New tab opened"
            )

            return True

        except Exception as e:

            print(
                f"[Browser NEW TAB ERROR] {e}"
            )

            return False

    # * =====================================================
    # * CLOSE TAB
    # * =====================================================

    def close_tab(self):

        return self._run_browser(
            self._close_tab_impl
        )

    def _close_tab_impl(self):

        try:

            if not self.page:

                return False

            closing_page = self.page

            closing_page.close()

            # * -------------------------------------------------
            # * Restore previous tab if available
            # * -------------------------------------------------

            if (
                self.previous_page
                and not self.previous_page.is_closed()
            ):

                self.page = self.previous_page
                self.previous_page = None

                self.page.bring_to_front()
                
                self._sync_context()

                print(
                    "[Browser] "
                    "Returned to previous tab"
                )

            else:

                self.page = None

            return True

        except Exception as e:

            print(
                f"[Browser CLOSE TAB ERROR] {e}"
            )

            return False

    # * =====================================================
    # * REFRESH
    # * =====================================================

    def refresh(self):

        return self._run_browser(
            self._refresh_impl
        )

    def _refresh_impl(self):

        try:

            if not self.page:

                return False

            self.page.reload()
            
            self._sync_context()

            return True

        except Exception as e:

            print(
                f"[Browser REFRESH ERROR] {e}"
            )

            return False

    # * =====================================================
    # * BACK
    # * =====================================================

    def back(self):

        return self._run_browser(
            self._back_impl
        )

    def _back_impl(self):

        try:

            if not self.page:

                return False

            # * -------------------------------------------------
            # * First: normal browser history
            # * -------------------------------------------------

            try:

                self.page.go_back(
                    wait_until="commit",
                    timeout=5000,
                )

            except Exception as error:

                print(
                    f"[Browser BACK WARNING] {error}"
                )

            self.page.bring_to_front()

            self._sync_context()

            print(
                "[Browser] Navigated back"
            )

            return True

        except Exception as e:

            print(
                f"[Browser BACK ERROR] {e}"
            )

            # * -------------------------------------------------
            # * No usable browser history.
            #
            # * Return to the previous JARVIS tab.
            # * -------------------------------------------------

            if (
                self.previous_page
                and not self.previous_page.is_closed()
            ):

                current_page = self.page

                self.page = self.previous_page

                self.previous_page = None

                self.page.bring_to_front()

                self._sync_context()

                print(
                    "[Browser] "
                    "Returned to previous tab"
                )

                # * -------------------------------------------------
                # * Close temporary tab.
                # * -------------------------------------------------

                try:

                    if (
                        current_page
                        and not current_page.is_closed()
                        and current_page != self.page
                    ):

                        current_page.close()

                except Exception:

                    pass

                return True

            print(
                "[Browser] "
                "No browser history or previous tab"
            )

            return False

        except Exception as e:

            print(
                f"[Browser BACK ERROR] {e}"
            )

            return False

    # * =====================================================
    # * FORWARD
    # * =====================================================

    def forward(self):

        return self._run_browser(
            self._forward_impl
        )

    def _forward_impl(self):

        try:

            if not self.page:

                return False

            try:

                self.page.go_forward(
                    wait_until="commit",
                    timeout=5000,
                )

            except Exception as error:

                print(
                    f"[Browser FORWARD WARNING] {error}"
                )

            self.page.bring_to_front()

            self._sync_context()

            print(
                "[Browser] Navigated forward"
            )

            return True

        except Exception as e:

            print(
                f"[Browser FORWARD ERROR] {e}"
            )

            return False

    # * =====================================================
    # * SCROLL DOWN
    # * =====================================================

    def scroll_down(self):

        return self._run_browser(
            self._scroll_down_impl
        )

    def _scroll_down_impl(self):

        try:

            if not self.page:

                return False

            self.page.mouse.wheel(
                0,
                1000,
            )

            return True

        except Exception as e:

            print(
                f"[Browser SCROLL ERROR] {e}"
            )

            return False

    # * =====================================================
    # * SCROLL UP
    # * =====================================================

    def scroll_up(self):

        return self._run_browser(
            self._scroll_up_impl
        )

    def _scroll_up_impl(self):

        try:

            if not self.page:

                return False

            self.page.mouse.wheel(
                0,
                -1000,
            )

            return True

        except Exception as e:

            print(
                f"[Browser SCROLL ERROR] {e}"
            )

            return False

    # * =====================================================
    # * CLOSE
    # * =====================================================

    def close(self):

        return self._run_browser(
            self._close_impl
        )

    def _close_impl(self):

        try:

            # * The runtime owns Chromium. Stop its whole owned process tree
            # * before dropping the CDP connection.
            if self.runtime:
                self.runtime.stop()

            if self.page:

                try:

                    self.page.close()

                except Exception:

                    pass

            if self.browser:

                try:

                    self.browser.close()

                except Exception:

                    pass

            if self.playwright:

                try:

                    self.playwright.stop()

                except Exception:

                    pass

        finally:

            self.page = None
            self.previous_page = None
            self.browser = None
            self.playwright = None
            self.runtime = None

        return True


# * =========================================================
# * GLOBAL BROWSER INSTANCE
# * =========================================================

browser = BrowserController()
