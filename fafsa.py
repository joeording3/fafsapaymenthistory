import csv
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# -----------------------------
# Helper function to extract table rows from the current page
def extract_table_data(soup, header_extracted):
    table = soup.find("table")
    if table is None:
        print("Table not found on the current page!")
        return [], header_extracted
    
    # Try to find a <tbody>; if none, get the <tr> directly from the table.
    tbody = table.find("tbody")
    if tbody:
        rows = tbody.find_all("tr")
    else:
        rows = table.find_all("tr")
    
    data = []
    # If header not yet extracted, extract the header row.
    if not header_extracted and rows:
        header_cells = rows[0].find_all(['th', 'td'])
        header = [cell.get_text(strip=True) for cell in header_cells]
        data.append(header)
        header_extracted = True
        rows = rows[1:]  # Skip the header on subsequent extraction

    # Extract data from every non-hidden row.
    for row in rows:
        # Some rows might have the attribute "hidden" or similar.
        if row.has_attr("hidden"):
            continue
        cells = row.find_all("td")
        if cells:
            row_data = [cell.get_text(strip=True) for cell in cells]
            data.append(row_data)
    return data, header_extracted

# -----------------------------
# Initialize Selenium with webdriver_manager
service = Service(ChromeDriverManager("132.0.6834.83").install())
driver = webdriver.Chrome(service=service)

# -----------------------------
# 1. Log in
driver.get('https://studentaid.gov/signin/')
print("Please complete the login in the opened browser window. Waiting up to 3 minutes...")
try:
    # Wait until the URL indicates login is complete (e.g., when it includes "dashboard")
    WebDriverWait(driver, 180).until(lambda d: "dashboard" in d.current_url)
    print("Login detected. Current URL:", driver.current_url)
except Exception as e:
    print("Timed out waiting for login (URL change):", e)
    driver.quit()
    exit()

# -----------------------------
# 2. Navigate to the payment history page
driver.get('https://studentaid.gov/aid-summary/idr-loan-forgiveness/payment-history')
time.sleep(5)  # Allow extra time for dynamic content to load

all_data = []             # To collect rows from all pages
header_extracted = False  # Flag to add header only once

while True:
    # Get the current page source and parse with BeautifulSoup
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')
    
    # Extract table data from the current page
    new_rows, header_extracted = extract_table_data(soup, header_extracted)
    print(f"Extracted {len(new_rows)} rows from current page.")
    
    # Append the rows (skip appending the header if it's already in all_data)
    if new_rows:
        if header_extracted and all_data:
            all_data.extend(new_rows[1:])
        else:
            all_data.extend(new_rows)
    
    # -----------------------------
    # 3. Locate and click the "Next" control.
    try:
        # Use the ID to locate the Next span
        next_button = driver.find_element(By.ID, "fsa_Button_PaginationPaymentHistory_Next")
        # Check if the Next button is displayed and enabled
        if not next_button.is_displayed() or not next_button.is_enabled():
            print("Next button is not clickable; reached the last page.")
            break
        else:
            print("Clicking on the Next button...")
            # Sometimes clicking via JavaScript is more reliable on non-button elements.
            driver.execute_script("arguments[0].click();", next_button)
            # Wait for the new table content to load (adjust if necessary)
            time.sleep(5)
    except Exception as e:
        print("No Next button found or an error occurred; assuming last page reached.", e)
        break

# -----------------------------
# 4. Save the data to a CSV file
csv_filename = "payment_history.csv"
with open(csv_filename, "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    for row in all_data:
        writer.writerow(row)

print(f"Data extraction complete! Extracted {len(all_data)} rows and saved to '{csv_filename}'.")
driver.quit()