Feature: Employer Job Expiry Notification

  Scenario: Receive notification before job posting expires
    Given the employer has an active job posting with an upcoming expiry date
    When the expiry date is approaching
    Then the system should display a notification to the employer reminding them that the job posting will expire soon

  Scenario: View job posting expiry notification details
    Given the employer has received a job posting expiry notification
    When the employer clicks on the notification
    Then the system should redirect the employer to the job posting management page