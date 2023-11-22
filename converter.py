import json
import re
import requests
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
import tinycss2
import argparse


class FontExtractor:
    FONT_BASE_URL = 'https://font-public.canva.com/'
    WEIGHT_MAP = {
        'Thin': 100,
        'ExtraLight': 200,
        'Light': 300,
        'Regular': 400,
        'Medium': 500,
        'SemiBold': 600,
        'Bold': 700,
        'ExtraBold': 800,
        'Black': 900
    }
    STYLE_MAP = {
        'Italic': 'italic',
        'Normal': 'normal'
    }
    FONT_FORMATS = ['woff2', 'ttf', 'woff']

    def __init__(self, html_content):
        self.html_content = html_content

    def extract_font_face_rules(self):
        soup = BeautifulSoup(self.html_content, 'html.parser')
        font_face_rules = []

        for element in soup.find_all(style=True):
            font_family = self._extract_font_family(element['style'])
            if font_family:
                print(f"Found font family: {font_family}")
                font_links = self._find_font_links(font_family)
                for link, weight, style, format in font_links:
                    print(f"{font_family} {weight} {style} {format}")
                    font_face_rules.append(
                        f"@font-face {{\n"
                        f"  font-family: '{font_family}';\n"
                        f"  src: url('{link}') format('{format}');\n"
                        f"  font-weight: {weight};\n"
                        f"  font-style: {style};\n"
                        f"}}\n"
                    )
                    print("*" * 50)
        return font_face_rules

    def _extract_font_family(self, style):
        match = re.search(r"font-family:\s*\"([^']+)\"", style)
        return match.group(1) if match else None

    def _find_font_links(self, font_family):
        font_family_encoded = font_family.replace(' ', '/')
        font_links = []

        pattern = re.compile(rf"{re.escape(self.FONT_BASE_URL + font_family_encoded)}/[^\s/]+\.({'|'.join(self.FONT_FORMATS)})")

        for match in pattern.finditer(self.html_content):
            href = match.group(0)
            weight, style = self._extract_font_weight_and_style(href)
            format = href.split('.')[-1]
            font_links.append((href, weight, style, format))

        return font_links

    def _extract_font_weight_and_style(self, font_filename):
        weight = 'normal'
        style = 'normal'
        for weight_name, weight_value in FontExtractor.WEIGHT_MAP.items():
            if weight_name in font_filename:
                weight = weight_value
                break
        for style_name, style_value in FontExtractor.STYLE_MAP.items():
            if style_name in font_filename:
                style = style_value
                break
        return weight, style

class BlobToSVGConverter:
    BLOB_URL_PATTERN = r'blob:https://www.canva.com/'

    def __init__(self, driver):
        self.driver = driver

    def replace_images_with_svg_or_base64(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        img_tags = soup.find_all('img', src=re.compile(self.BLOB_URL_PATTERN))

        for img in img_tags:
            blob_url = img['src']
            content, is_svg = self._fetch_blob_content(blob_url)

            if is_svg:
                svg_soup = BeautifulSoup(content, 'html.parser')
                svg = svg_soup.find('svg')
                if svg:
                    img.replace_with(svg)
            else:
                img['src'] = content

        return str(soup)

    def _fetch_blob_content(self, blob_url):
        script = f"""
            var callback = arguments[arguments.length - 1];
            fetch("{blob_url}")
                .then(response => response.blob())
                .then(blob => {{
                    var reader = new FileReader();
                    reader.onloadend = () => callback([reader.result, blob.type === 'image/svg+xml']);
                    if (blob.type === 'image/svg+xml') {{
                        reader.readAsText(blob);
                    }} else {{
                        reader.readAsDataURL(blob);
                    }}
                }})
                .catch(error => callback(['Error: ' + error.message, false]));
        """
        return self.driver.execute_async_script(script)

class CSSOptimizer:
    def __init__(self, html_content, css_content):
        self.html_content = html_content
        self.css_content = css_content

    def get_html_selectors(self):
        soup = BeautifulSoup(self.html_content, 'html.parser')
        selectors = set()
        for element in soup.find_all(True):
            selectors.add(element.name)
            for class_ in element.get("class", []):
                selectors.add(f".{class_}")
            for id_ in element.get("id", []):
                selectors.add(f"#{id_}")
        return selectors

    def get_css_rules(self):
        rules = tinycss2.parse_stylesheet(self.css_content, skip_comments=True)
        return [rule for rule in rules if rule.type == 'qualified-rule']

    def filter_css_rules(self, css_rules, html_selectors):
        optimized_rules = []
        for rule in css_rules:
            prelude = tinycss2.serialize(rule.prelude)
            content = tinycss2.serialize(rule.content)
            if any(selector in prelude for selector in html_selectors):
                optimized_rules.append(prelude + ' {' + content + '}')
        return optimized_rules

    def optimize(self):
        html_selectors = self.get_html_selectors()
        css_rules = self.get_css_rules()
        optimized_rules = self.filter_css_rules(css_rules, html_selectors)
        return '\n'.join(optimized_rules)

class CanvaConverter:
    CSS_URL = 'https://static.canva.com/web/36b99f3659b2c9ed.ltr.css'
    TEMPLATE_SELECTOR = '.uPeMFQ'

    def __init__(self, driver, url):
        self.driver = driver
        self.url = url

    def grab_html(self):
        self.driver.get(self.url)
        self.driver.implicitly_wait(20)
        return self.driver.page_source

    def grab_selected_html(self, page_source):
        soup = BeautifulSoup(page_source, 'html.parser')
        element = soup.select_one(self.TEMPLATE_SELECTOR)
        return str(element) if element else ''

    def download_css(self):
        return requests.get(self.CSS_URL).text

    def parse_and_create_new_html(self, selected_html_content, css_content, font_face_rules):
        new_html_content = (
            f"<html><head><style>{''.join(font_face_rules)}{css_content}</style></head>"
            f"<body>{selected_html_content}</body></html>"
        )
        with open('new_page.html', 'w') as f:
            f.write(new_html_content)

    def perform(self):
        full_html_content     = self.grab_html()
        selected_html_content = self.grab_selected_html(full_html_content)
        font_extractor        = FontExtractor(full_html_content)
        font_face_rules       = font_extractor.extract_font_face_rules()
        css_content           = self.download_css()
        blob_to_svg_converter = BlobToSVGConverter(self.driver)
        html_with_svg         = blob_to_svg_converter.replace_images_with_svg_or_base64(selected_html_content)
        css_optimizer         = CSSOptimizer(selected_html_content, css_content)
        optimized_css         = css_optimizer.optimize()

        self.parse_and_create_new_html(html_with_svg, optimized_css, font_face_rules)


def parse_and_validate_arguments():
    parser = argparse.ArgumentParser(description='Convert Canva design to HTML.')
    parser.add_argument('--cookies', help='Path to the cookies file', required=True)
    parser.add_argument('--url', help='URL of the Canva design', required=True)
    args = parser.parse_args()

    return args.cookies, args.url

def initialize_driver():
    options = uc.ChromeOptions()
    options.headless = False
    return uc.Chrome(use_subprocess=True, options=options)

def load_cookies(driver, cookies_file, url):
    driver.get(url)

    try:
        with open(cookies_file, 'r') as f:
            cookies = json.load(f)
    except FileNotFoundError:
        driver.quit()
        print(f"Error: The file '{cookies_file}' was not found.")
        exit(1)

    for cookie in cookies:
        if cookie.get('sameSite', '') == 'no_restriction':
            cookie['sameSite'] = 'None'
        driver.add_cookie(cookie)


if __name__ == '__main__':
    cookies_file, url = parse_and_validate_arguments()
    driver = initialize_driver()
    load_cookies(driver, cookies_file, 'https://www.canva.com/')

    converter = CanvaConverter(driver, url)
    converter.perform()

    driver.quit()
