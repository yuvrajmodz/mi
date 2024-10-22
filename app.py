from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import os

app = Flask(__name__)

@app.route('/imei', methods=['GET'])
def check_imei():
    # Get the IMEI from the request parameters
    imei = request.args.get('check')
    
    # Validate the IMEI
    if not imei or len(imei) != 15:
        return jsonify({"error": "Invalid IMEI number"}), 400

    # Start Playwright to scrape the data
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # Set headless=False for debugging
        page = browser.new_page()

        # Navigate to the IMEI checker page
        page.goto("https://www.ca.go.ke/imei-checker")

        try:
            # Wait for the input field to be visible and input the IMEI number
            page.wait_for_selector('input#imei', timeout=60000)
            page.fill('input#imei', imei)

            # Click the "Check IMEI" button
            page.click('button.btn-primary')

            # Wait for the modal with the result to appear
            page.wait_for_selector('div#modalBody', timeout=60000)

            # Get the page content after the IMEI check
            content = page.content()

            # Close the browser
            browser.close()

            # Parse the page content with BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')

            # Scrape the required data
            modal_body = soup.find('div', {'id': 'modalBody'})
            if modal_body:
                # Extract information
                customer_info = modal_body.find('h5').text if modal_body.find('h5') else 'Unknown'
                model_info = modal_body.find_all('p')[1].text.split(": ")[1] if len(modal_body.find_all('p')) > 1 else 'Unknown'
                created_at = modal_body.find_all('p')[2].text.split(": ")[1] if len(modal_body.find_all('p')) > 2 else 'Unknown'
                imei_info = modal_body.find_all('p')[3].text.split(": ")[1] if len(modal_body.find_all('p')) > 3 else 'Unknown'

                # Return the data in JSON format
                return jsonify({
                    "customer": customer_info,
                    "model": model_info,
                    "created_at": created_at,
                    "imei": imei_info
                })
            else:
                return jsonify({"error": "IMEI check failed or no data found"}), 404

        except Exception as e:
            browser.close()
            return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5016))
    app.run(host='0.0.0.0', port=port, debug=True)