Feature: Company Verification Email Notification
  As an Employer
  I want to receive an email notification when my company verification status is updated
  So that I am informed whether my registration request has been approved or rejected.

  Scenario: Employer receives approval email
    Given a company verification email recipient exists
    When the company verification status is Approved
    Then an approval email should be sent
    And the approval email subject should be correct
    And the approval email should contain the company name
    And the approval email should explain that the company was approved

  Scenario: Employer receives rejection email
    Given a company verification email recipient exists
    When the company verification status is Rejected with a reason
    Then a rejection email should be sent
    And the rejection email subject should be correct
    And the rejection email should contain the rejection reason

  Scenario: Rejected verification without reason is handled
    Given a company verification email recipient exists
    When the company verification status is Rejected without a reason
    Then a rejection email should still be sent
    And the rejection email should not contain a reason section

  Scenario: Employer receives email for another verification status
    Given a company verification email recipient exists
    When the company verification status is Pending Review
    Then a status update email should be sent
    And the email should contain the current verification status

  Scenario: Verification email is sent to the correct employer email
    Given a company verification email recipient exists
    When the company verification status is Approved
    Then the verification email should be sent to the correct email address

  Scenario: Email sending failure is propagated
    Given the email service fails
    When the company verification status is Approved expecting an error
    Then the email sending error should be raised
