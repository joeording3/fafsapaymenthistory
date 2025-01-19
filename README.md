# fafsapaymenthistory
Script to Save Federal Student Loan Payment History from studentaid.gov

Their website doesn't have an export functionality, and only displays 10 entries at a time. This script will open the page (will be 404), wait for you to login/2fa, and then navigate to the Payment History page and save the values in the table to a CSV. It will click 'next' until it reaches the end of the table. It doesn't detect when it reaches the end and keeps trying to click 'next' forever; just close the browser or click to a different page to end the script and it will write to a csv.

This works on MacOS 15.2, not tested anywhere else.
