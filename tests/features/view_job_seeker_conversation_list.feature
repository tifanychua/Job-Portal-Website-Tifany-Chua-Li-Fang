Feature: View Job Seeker Conversation List

  As a Job Seeker,
  I want to view a list of my conversations with employers,
  so that I can access previous communications, check interview updates,
  and respond to employers during the hiring process.


  Scenario: View conversation list
    Given the job seeker is logged in and has existing conversations with employers
    When the job seeker opens the Messages page
    Then the system should display the list of conversations with employers


  Scenario: Display latest conversation information
    Given the job seeker is viewing the conversation list
    When the conversations are loaded
    Then the system should display the latest message and conversation details


  Scenario: No conversations available
    Given the job seeker has no conversations with employers
    When the job seeker opens the Messages page
    Then the system should display a "No conversations available" message