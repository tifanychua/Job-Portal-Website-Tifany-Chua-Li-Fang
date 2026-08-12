Feature: Job Seeker Personal Information Privacy
  As a Job Seeker
  I want my personal information to only be accessible by the employer I applied to
  So that my privacy is protected from unauthorized access.

  Scenario: Employer accesses applicant personal information after application
    Given the job seeker has submitted an application to an employer
    When the employer views the applicant's profile
    Then the system should allow the employer to access the job seeker's personal information

  Scenario: Unauthorized employer attempts to access personal information
    Given the job seeker has not applied to the employer
    When the employer attempts to view the job seeker's personal information
    Then the system should deny access and prevent the employer from viewing the information

  Scenario: Job seeker controls personal information visibility
    Given the job seeker has submitted applications to multiple employers
    When the job seeker views their privacy settings
    Then the system should display the employers who are allowed to access their personal information
