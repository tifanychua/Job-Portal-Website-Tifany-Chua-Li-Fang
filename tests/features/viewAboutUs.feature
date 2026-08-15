Feature: View About Us Page

  As a Job Seeker
  I want to view the About Us page
  So that I can understand the platform's purpose, services, and values

  Scenario: Access the About Us page
    Given the job seeker is viewing the website
    When the job seeker opens the About Us page
    Then the About Us page should be displayed

  Scenario: View platform information
    Given the job seeker is viewing the About Us page
    When the About Us content is loaded
    Then an introduction to the platform should be displayed
    And information about how the platform supports job seekers should be displayed

  Scenario: View the platform mission and values
    Given the job seeker is viewing the About Us page
    When the job seeker views the mission and values section
    Then the platform mission should be displayed
    And the platform core values should be displayed

  Scenario: View job seeker services
    Given the job seeker is viewing the About Us page
    When the job seeker views the services section
    Then services available to job seekers should be displayed
    And the services should include finding jobs and connecting with employers

  Scenario: Explore available jobs
    Given the job seeker is viewing the About Us page
    When the job seeker selects the Explore Jobs option
    Then the job seeker should be directed to the available jobs page

  Scenario: Access the About Us page without logging in
    Given the job seeker is not logged in
    When the job seeker opens the About Us page as a guest
    Then the About Us page should be displayed without requiring authentication
