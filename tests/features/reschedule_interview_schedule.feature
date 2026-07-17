Feature: Reschedule Interview

  As an Employer
  I want to reschedule interviews with shortlisted job seekers
  So that I can adjust interview timings when there are changes in availability


  Scenario: Employer updates interview schedule
    Given the employer has a scheduled interview
    When the employer changes the interview date and time
    And confirms the reschedule request
    Then the interview schedule should be updated successfully


  Scenario: Save updated interview schedule
    Given the employer has rescheduled an interview
    When the update process is completed
    Then the new interview details should be saved in the database


  Scenario: Employer reschedules interview with invalid information
    Given the employer is updating a scheduled interview
    When the employer submits incomplete interview details
    Then the system should display an error message