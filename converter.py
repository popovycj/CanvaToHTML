import json
import re
import requests
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
import tinycss2
import argparse

class WebDriverManager:
    def __init__(self, url):
        self.url = url
        self.driver = self._initialize_driver()

    def _initialize_driver(self):
        options = uc.ChromeOptions()
        options.headless = False
        return uc.Chrome(use_subprocess=True, options=options)

    def add_cookies(self, cookies):
        self.driver.get(self.url)
        for cookie in cookies:
            if cookie.get('sameSite', '') == 'no_restriction':
                cookie['sameSite'] = 'None'
            self.driver.add_cookie(cookie)
        self.driver.refresh()
        self.driver.implicitly_wait(20)

    def get_page_source(self):
        return self.driver.page_source

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

    def replace_images_with_svg(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        img_tags = soup.find_all('img', src=re.compile(self.BLOB_URL_PATTERN))
        print(img_tags)

        for img in img_tags:
            blob_url = img['src']
            script = f"""
                var callback = arguments[arguments.length - 1];
                fetch("{blob_url}")
                    .then(response => response.text())
                    .then(text => callback(text))
                    .catch(error => callback('Error: ' + error.message));
            """
            svg_content = self.driver.execute_async_script(script)
            print(svg_content)
            print("*" * 50)
            svg_soup = BeautifulSoup(svg_content, 'html.parser')
            svg = svg_soup.find('svg')

            if svg:
                img.replace_with(svg)

        return str(soup)

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

    def __init__(self, cookies_file, url):
        self.cookies_file = cookies_file
        self.url = url
        self.driver_manager = WebDriverManager(url)
        self.load_cookies()

    def load_cookies(self):
        with open(self.cookies_file, 'r') as f:
            cookies = json.load(f)
        self.driver_manager.add_cookies(cookies)

    def grab_html(self):
        return self.driver_manager.get_page_source()

    def grab_selected_html(self):
        page_source = self.driver_manager.get_page_source()
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
        selected_html_content = self.grab_selected_html()
        font_extractor        = FontExtractor(full_html_content)
        font_face_rules       = font_extractor.extract_font_face_rules()
        css_content           = self.download_css()
        blob_to_svg_converter = BlobToSVGConverter(self.driver_manager.driver)
        html_with_svg         = blob_to_svg_converter.replace_images_with_svg(selected_html_content)
        css_optimizer         = CSSOptimizer(selected_html_content, css_content)
        optimized_css         = css_optimizer.optimize()

        self.parse_and_create_new_html(html_with_svg, optimized_css, font_face_rules)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert Canva design to HTML.')

    parser.add_argument('--cookies', help='Path to the cookies file', default=None)
    parser.add_argument('--url', help='URL of the Canva design', default=None)

    parser.add_argument('positional_args', nargs='*', help='Positional arguments: cookies_file url')

    args = parser.parse_args()

    cookies_file = args.cookies if args.cookies else (args.positional_args[0] if args.positional_args else None)
    url = args.url if args.url else (args.positional_args[1] if len(args.positional_args) > 1 else None)

    if not cookies_file or not url:
        parser.error("Both cookies file and URL are required.")

    converter = CanvaConverter(cookies_file, url)
    converter.perform()
