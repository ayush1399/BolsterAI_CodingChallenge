from bs4 import BeautifulSoup
from datetime import datetime
from ipwhois import IPWhois

import validators
import argparse


def validate_url(url):
    try:
        if validators.url(url):
            return url
        raise argparse.ArgumentTypeError(f"Invalid URL: {url}")
    except validators.ValidationError as error:
        raise argparse.ArgumentTypeError(f"Invalid URL: {error}")


def get_asn_info(ip_address):
    obj = IPWhois(ip_address)
    results = obj.lookup_whois()

    asn = results.get("asn")
    asn_description = results.get("asn_description")
    return asn, asn_description


def get_ssl_certificate_info(response):
    if not response["url"].startswith("https://"):
        return None

    info = {}
    security_details = response.get("securityDetails", {})

    info["protocol"] = security_details.get("protocol", "N/A")
    info["subjectName"] = security_details.get("subjectName", "N/A")
    info["issuer"] = security_details.get("issuer", "N/A")
    info["validFrom"] = security_details.get("validFrom", 0)
    info["validTo"] = security_details.get("validTo", 0)

    info["validFrom"] = datetime.utcfromtimestamp(info["validFrom"]).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    info["validTo"] = datetime.utcfromtimestamp(info["validTo"]).strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    return info


def extract_text_from_html(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    text = soup.get_text(separator=" ", strip=True)
    return text


def get_args():
    parser = argparse.ArgumentParser(description="URL Scanning Webservice")
    parser.add_argument("url", type=validate_url, help="URL to scan")
    parser.add_argument(
        "--dir", type=str, default="./data", help="Directory to save the scan results"
    )

    return parser.parse_args()
