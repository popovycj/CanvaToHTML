# Canva to HTML/CSS Converter

## Introduction
This Python project enables users to convert Canva templates into HTML and CSS code. It's particularly useful for web developers and designers who want to use Canva's design capabilities within web applications. The converter supports extracting fonts.

## Installation

### Prerequisites
- Python 3.x
- pip (Python package manager)
- ChromeDriver

### Setup
1. **Clone the repository:**
   ```bash
   git clone https://github.com/popovycj/CanvaToHTML.git
2. **Navigate to project directory:**
   ```bash
   cd CanvaToHTML/
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt

## Usage

### Basic Conversion

1. **Prepare your Canva URL and Cookies JSON file:**
   - Save the cookies from your browser session while logged into Canva.
   - The cookies should be in a JSON format.
2. **Run the Converter:**
   ```bash
   python converter.py --cookies path/to/cookies.json --url "https://www.canva.com/design/[designID]/"

### Using with Jinja Templating

To programmatically edit the converted Canva template, you can use a templating engine like Jinja.
1. **Install Jinja:**
   ```bash
   pip install Jinja2
2. **Create a Jinja Template:**
   - Edit the generated HTML file to include Jinja template variables where you want dynamic content.
   - For example, replace a text field with **{{ my_variable }}**.
3. **Render Template with Variables:**
   Use Jinja to render the template with your desired variables.
   ```python
   from jinja2 import Template

   # Load your template
   with open('path/to/generated_template.html') as file:
       template = Template(file.read())
  
   # Render the template with your variables
   rendered_html = template.render(my_variable="Dynamic Content")
  
   # Save or use the rendered HTML

## Extending Functionality
- **Custom CSS and JS:** You can add additional CSS or JavaScript to the generated HTML to further customize the design.
- **Automating with APIs:** Consider integrating with APIs to automate the fetching and updating of content within the template.

## Contributing
Contributions to the project are welcome! Please follow the standard fork and pull request workflow.




