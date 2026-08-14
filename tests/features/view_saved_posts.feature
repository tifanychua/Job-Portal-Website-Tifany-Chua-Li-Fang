Feature: View Saved Career Advice Posts

  As a Job Seeker
  I want to view my saved Career Advice posts
  So that I can access useful career information later

  Scenario: View list of saved Career Advice posts
    Given the job seeker is logged into the system
    And the job seeker has saved Career Advice posts
    When the job seeker accesses the saved posts page
    Then the system should display all Career Advice posts saved by the job seeker

  Scenario: View saved post information
    Given the job seeker is viewing the saved posts page
    When the saved Career Advice posts are displayed
    Then the system should display the title, summary, category, publication date, and saved date of each post

  Scenario: Open a saved Career Advice post
    Given the job seeker is viewing the saved posts page
    When the job seeker selects a saved Career Advice post
    Then the system should display the selected Career Advice article

  Scenario: View an empty saved posts list
    Given the job seeker is logged into the system
    And the job seeker has not saved any Career Advice posts
    When the job seeker accesses the saved posts page
    Then the system should display a message indicating that no posts have been saved