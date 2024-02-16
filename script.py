from playwright.sync_api import sync_playwright
from utils import (
    get_args,
    get_asn_info,
    get_ssl_certificate_info,
    extract_text_from_html,
)

import base64


class PlaywrightScanner:
    def __init__(self, url):
        self.url = url
        self.cached_data = {}
        self.redirects = []

    def _handle_request(self, request):
        self.cached_data[request.url] = {"remote_address": None}

    def _handle_response(self, response):
        if response.status >= 300 and response.status < 400:
            self.redirects.append(
                {
                    "url": response.url,
                    "status": response.status,
                    "location": response.headers.get("location"),
                }
            )

    def _store_remote_address(self, response):
        url = response["url"]
        if url in self.cached_data:
            server_addr = response["remoteIPAddress"]
            if server_addr:
                self.cached_data[url]["remote_address"] = server_addr

            server_port = response["remotePort"]
            if server_port:
                self.cached_data[url]["remote_port"] = server_port

    def _store_ssl_info(self, response):
        url = response["url"]
        if url in self.cached_data:
            ssl_info = get_ssl_certificate_info(response)
            self.cached_data[url]["ssl_info"] = ssl_info

    def _process_response(self, response):
        self._store_remote_address(response)
        self._store_ssl_info(response)

    def process_url(self):
        with sync_playwright() as p:
            extracted_info = {}

            browser = p.chromium.launch()
            context = browser.new_context()
            page = context.new_page()

            page.on("request", self._handle_request)
            page.on("response", self._handle_response)

            client = context.new_cdp_session(page)
            client.send("Network.enable")
            client.on(
                "Network.responseReceived",
                lambda event: self._process_response(event["response"]),
            )

            page.goto(self.url)

            screenshot_bytes = page.screenshot(full_page=True, type="png")
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode("utf-8")
            extracted_info["screenshot"] = screenshot_base64

            page_source = page.content()
            extracted_info["page_source"] = page_source
            extracted_info["text_content"] = extract_text_from_html(page_source)

            final_url = page.url
            extracted_info["ip"] = self.cached_data[final_url]["remote_address"]

            asn, asn_description = get_asn_info(
                self.cached_data[final_url]["remote_address"]
            )
            extracted_info["asn"] = {
                asn: asn,
                asn_description: asn_description,
            }

            if len(self.redirects) > 0:
                extracted_info["source_url"] = self.url
                extracted_info["final_url"] = final_url

            extracted_info["ssl_info"] = self.cached_data[final_url]["ssl_info"]
            browser.close()

            return extracted_info


if __name__ == "__main__":
    args = get_args()
    scanner = PlaywrightScanner(args.url)
    info = scanner.process_url()

    for key, value in info.items():
        print(f"{key}: {value}")
