Feature: Share Career Advice Article

  As a Job Seeker
  I want to share a Career Advice article
  So that I can provide useful career information to others

  Scenario: Share a Career Advice article using the device sharing function
    Given the job seeker is viewing a Career Advice article
    And the browser supports the device sharing function
    When the job seeker clicks the Share button
    Then the system should open the device sharing options
    And the article title and link should be prepared for sharing

  Scenario: Copy the Career Advice article link
    Given the job seeker is viewing a Career Advice article
    And the browser does not support the device sharing function
    When the job seeker clicks the Share button
    Then the system should copy the article link to the clipboard
    And the system should display a message indicating that the article link was copied

  Scenario: Cancel sharing a Career Advice article
    Given the device sharing options are displayed
    When the job seeker cancels the sharing operation
    Then the system should close the device sharing options
    And the job seeker should remain on the Career Advice article page

  Scenario: Handle an unsuccessful sharing operation
    Given the job seeker is viewing a Career Advice article
    When the article cannot be shared or copied
    Then the system should display a message indicating that the article cannot be shared