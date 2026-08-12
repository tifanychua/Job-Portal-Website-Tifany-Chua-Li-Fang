Feature: Company Verification Email Notification

  Scenario: Receive email notification when company verification is approved
    Given the employer has submitted a company registration request
    When the admin approves the company verification request
    Then the system should send an email notification to the employer informing them that the registration request has been approved

  Scenario: Receive email notification when company verification is rejected
    Given the employer has submitted a company registration request
    When the admin rejects the company verification request
    Then the system should send an email notification to the employer informing them that the registration request has been rejected

  Scenario: Email notification contains verification status details
    Given the employer has received a company verification status email
    When the employer opens the email notification
    Then the email should display the verification status company information and relevant remarks if provided

  Scenario: No email notification is sent before verification update
    Given the employer company registration request is still pending review
    When the verification status has not been updated
    Then the system should not send any approval or rejection email notification