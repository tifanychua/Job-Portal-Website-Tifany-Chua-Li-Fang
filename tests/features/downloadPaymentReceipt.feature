Feature: Download Payment Receipt

  Scenario: Employer downloads a valid payment receipt PDF
    Given a completed card payment exists for the current company
    When the employer downloads the payment receipt
    Then the system should return a PDF receipt

  Scenario: Downloaded receipt has PDF filename
    Given a completed card payment exists for the current company
    When the employer downloads the payment receipt
    Then the downloaded receipt filename should contain the receipt number

  Scenario: Downloaded receipt has PDF content type
    Given a completed card payment exists for the current company
    When the employer downloads the payment receipt
    Then the downloaded receipt content type should be application pdf

  Scenario: PDF download does not allow another company's receipt
    Given a completed payment belongs to another company
    When the employer downloads the payment receipt expecting an error
    Then receipt access should be denied

  Scenario: PDF download rejects pending payment
    Given a pending card payment exists for the current company
    When the employer downloads the payment receipt expecting an error
    Then completed payment receipt should be required

  Scenario: PDF download rejects failed payment
    Given a failed card payment exists for the current company
    When the employer downloads the payment receipt expecting an error
    Then completed payment receipt should be required

  Scenario: PDF download handles missing date safely
    Given a completed card payment has no completed date
    When the employer downloads the payment receipt
    Then the PDF receipt should still be generated successfully

  Scenario: PDF download handles missing package safely
    Given a completed card payment has no package
    When the employer downloads the payment receipt
    Then the PDF receipt should still be generated successfully

  Scenario: PDF download handles missing amount safely
    Given a completed card payment has no amount
    When the employer downloads the payment receipt
    Then the PDF receipt should still be generated successfully