Feature: Generate Transaction Report
  As an Admin
  I want to generate and download transaction reports
  So that I can review employer payment records based on selected criteria.

  Scenario: Admin opens transaction report page
    Given the admin is logged into the system
    When the admin opens the transaction report page
    Then the system should display the transaction report page

  Scenario: Report filters are displayed
    Given the admin is viewing the transaction report page
    When the report page is loaded
    Then the system should display the report filter options

  Scenario: Report preview is not initially displayed
    Given the admin opens the transaction report page
    When no report has been generated
    Then the transaction report preview should not be displayed

  Scenario: Admin generates report without filters
    Given the admin is viewing the transaction report page
    When the admin generates the report without filters
    Then the system should display the generated transaction report

  Scenario: Generated report displays transaction information
    Given the admin has generated a transaction report
    When the transaction report preview is displayed
    Then the report should display the required transaction information

  Scenario: Admin generates report for completed transactions
    Given the admin is viewing the transaction report page
    When the admin generates a report with completed status
    Then the report should contain only completed transactions

  Scenario: Admin generates report for pending transactions
    Given the admin is viewing the transaction report page
    When the admin generates a report with pending status
    Then the report should contain only pending transactions

  Scenario: Admin generates report for failed transactions
    Given the admin is viewing the transaction report page
    When the admin generates a report with failed status
    Then the report should contain only failed transactions

  Scenario: Admin generates report using lowercase status
    Given the admin is viewing the transaction report page
    When the admin generates a report using lowercase completed status
    Then the report status filter should be case insensitive

  Scenario: Admin generates report using from date
    Given transactions exist on different dates
    When the admin generates a report using a from date
    Then transactions before the from date should be excluded

  Scenario: Admin generates report using to date
    Given transactions exist on different dates
    When the admin generates a report using a to date
    Then transactions after the to date should be excluded

  Scenario: Admin generates report using a date range
    Given transactions exist inside and outside a selected date range
    When the admin generates a report using the date range
    Then only transactions within the selected date range should be included

  Scenario: Admin generates report using status and date range
    Given transactions have different dates and statuses
    When the admin generates a report using status and date filters
    Then only transactions matching all selected report criteria should be included

  Scenario: Report filters return no transactions
    Given no transactions match the report criteria
    When the admin generates the transaction report
    Then the report should display no transactions found

  Scenario: Admin supplies invalid report status
    Given the admin is viewing the transaction report page
    When an invalid report status is supplied
    Then the system should handle the invalid report status without crashing

  Scenario: Report transaction has completed date
    Given a report transaction contains a completed date
    When the report determines the transaction date
    Then the completed date should be used

  Scenario: Report transaction has no completed date
    Given a report transaction has no completed date but contains a created date
    When the report determines the transaction date
    Then the created date should be used

  Scenario: Report transaction contains no transaction date
    Given a report transaction has no completed date or created date
    When the report is generated
    Then the missing report transaction date should be handled safely

  Scenario: Report transaction references valid company
    Given a report transaction contains a valid company ID
    When the transaction report is generated
    Then the corresponding company name should be included

  Scenario: Report transaction references missing company
    Given a report transaction references a company that does not exist
    When the transaction report is generated
    Then the system should handle the missing report company safely

  Scenario: Completed transaction contributes to report revenue
    Given a completed transaction exists in the report
    When report summary values are calculated
    Then the completed transaction amount should contribute to report revenue

  Scenario: Pending transaction does not contribute to report revenue
    Given a pending transaction exists in the report
    When report summary values are calculated
    Then the pending transaction amount should not contribute to report revenue

  Scenario: Failed transaction does not contribute to report revenue
    Given a failed transaction exists in the report
    When report summary values are calculated
    Then the failed transaction amount should not contribute to report revenue

  Scenario: Report counts completed transactions
    Given completed transactions match the report criteria
    When the report summary is calculated
    Then the successful transaction count should be correct

  Scenario: Report counts pending transactions
    Given pending transactions match the report criteria
    When the report summary is calculated
    Then the pending transaction count should be correct

  Scenario: Report counts failed transactions
    Given failed transactions match the report criteria
    When the report summary is calculated
    Then the failed transaction count should be correct

  Scenario: Generated report flag enables report preview
    Given the admin is viewing the transaction report page
    When the report generate parameter is enabled
    Then the transaction report preview should be displayed

  Scenario: Admin downloads transaction report PDF
    Given the admin has generated a transaction report
    When the admin downloads the transaction report
    Then the system should return a PDF file

  Scenario: Downloaded transaction report has PDF content type
    Given the admin downloads the transaction report
    When the report download response is returned
    Then the response content type should be application pdf

  Scenario: Downloaded transaction report has PDF filename
    Given the admin downloads the transaction report
    When the report download response is returned
    Then the downloaded report filename should end with pdf

  Scenario: Admin downloads completed transaction report
    Given transactions have different payment statuses
    When the admin downloads a report filtered by completed status
    Then the PDF report should be generated successfully

  Scenario: Admin downloads report using from date
    Given transactions exist on different dates
    When the admin downloads a report using a from date
    Then the filtered PDF report should be generated successfully

  Scenario: Admin downloads report using to date
    Given transactions exist on different dates
    When the admin downloads a report using a to date
    Then the filtered PDF report should be generated successfully

  Scenario: Admin downloads report using date range
    Given transactions exist on different dates
    When the admin downloads a report using a date range
    Then the date filtered PDF report should be generated successfully

  Scenario: Admin downloads report using status and date
    Given transactions contain different dates and statuses
    When the admin downloads a report using status and date filters
    Then the combined filtered PDF report should be generated successfully

  Scenario: Admin downloads report with no matching transactions
    Given no transactions match the PDF report criteria
    When the admin downloads the transaction report
    Then the system should still generate a valid PDF report

  Scenario: PDF transaction references missing company
    Given a PDF transaction references a company that does not exist
    When the PDF transaction report is generated
    Then the missing company should be represented safely in the PDF

  Scenario: PDF transaction contains no payment date
    Given a PDF transaction does not contain a payment date
    When the PDF transaction report is generated
    Then the missing payment date should be represented with a dash

  Scenario: PDF report calculates completed revenue
    Given completed and unsuccessful transactions exist
    When the PDF transaction report is generated
    Then only completed transaction amounts should contribute to PDF report revenue

  Scenario: PDF is generated when transaction list is empty
    Given no transactions exist
    When the admin downloads the transaction report
    Then a valid PDF containing the empty report message should be generated