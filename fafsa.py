import csv
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchWindowException

# -----------------------------
# Helper function to extract table rows from the current page
def extract_table_data(soup, header_extracted):
    table = soup.find("table")
    if table is None:
        print("Table not found on the current page!")
        return [], header_extracted
    
    # Look for a <tbody>; if not present, get all <tr> elements directly from the table.
    tbody = table.find("tbody")
    if tbody:
        rows = tbody.find_all("tr")
    else:
        rows = table.find_all("tr")
    
    data = []
    # If the header has not been extracted yet, extract the header row.
    if not header_extracted and rows:
        header_cells = rows[0].find_all(['th', 'td'])
        header = [cell.get_text(strip=True) for cell in header_cells]
        data.append(header)
        header_extracted = True
        rows = rows[1:]  # Skip the header on subsequent extractions

    # Extract the rest of the rows (skipping any that are hidden).
    for row in rows:
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
    # Wait until the URL indicates login is complete (e.g., includes "dashboard")
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
    # Attempt to get the current page source; if the window is closed, break the loop.
    try:
        page_source = driver.page_source
    except NoSuchWindowException:
        print("Browser window closed; ending extraction loop.")
        break

    soup = BeautifulSoup(page_source, 'html.parser')
    
    # Extract table data from the current page.
    new_rows, header_extracted = extract_table_data(soup, header_extracted)
    print(f"Extracted {len(new_rows)} rows from current page.")
    
    # Append extracted rows to all_data.
    if new_rows:
        if header_extracted and all_data:
            # Skip header if already collected.
            all_data.extend(new_rows[1:])
        else:
            all_data.extend(new_rows)
    
    # -----------------------------
    # 3. Locate and click the "Next" control.
    try:
        next_button = driver.find_element(By.ID, "fsa_Button_PaginationPaymentHistory_Next")
    except Exception as e:
        print("No Next button found; assuming last page reached.", e)
        break
    
    # Check if the Next button is displayed and enabled.
    if not next_button.is_displayed() or not next_button.is_enabled():
        print("Next button is not clickable; reached the last page.")
        break
    else:
        print("Clicking on the Next button...")
        try:
            driver.execute_script("arguments[0].click();", next_button)
        except Exception as e:
            print("Error clicking on Next button; breaking loop:", e)
            break
        # Wait for new content to load.
        time.sleep(5)

# -----------------------------
# 4. Save the accumulated data to a CSV file.
csv_filename = "payment_history.csv"
with open(csv_filename, "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    for row in all_data:
        writer.writerow(row)

print(f"Data extraction complete! Extracted {len(all_data)} rows and saved to '{csv_filename}'.")
try:
    driver.quit()
except Exception:
    pass
