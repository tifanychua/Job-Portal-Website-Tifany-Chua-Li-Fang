Feature: Job Search and Filtering

  As a Job Seeker
  I want to search and filter job opportunities
  So that I can quickly find jobs that match my preferences.

  Background:
    Given the job portal contains active job postings
    And the job seeker is on the job search page

  ##########################################################
  # Job Title Search
  ##########################################################

  Scenario: Search jobs by exact job title
    When the job seeker enters "Software Engineer" in the search box
    And clicks the "Search Jobs" button
    Then the system should display job postings with the title "Software Engineer"

  Scenario: Search jobs by partial job title
    When the job seeker enters "Engineer" in the search box
    And clicks the "Search Jobs" button
    Then the system should display job postings containing "Engineer"

  Scenario: Search jobs by job title regardless of capitalization
    When the job seeker enters "software engineer" in the search box
    And clicks the "Search Jobs" button
    Then the system should display matching job postings regardless of capitalization

  ##########################################################
  # Company Search
  ##########################################################

  Scenario: Search jobs by exact company name
    When the job seeker enters "ABC Sdn Bhd" in the search box
    And clicks the "Search Jobs" button
    Then the system should display job postings from "ABC Sdn Bhd"

  Scenario: Search jobs by partial company name
    When the job seeker enters "ABC" in the search box
    And clicks the "Search Jobs" button
    Then the system should display job postings from companies containing "ABC"

  ##########################################################
  # Category Search
  ##########################################################

  Scenario: Search jobs by category
    When the job seeker selects "Information Technology" from the category list
    And clicks the "Search Jobs" button
    Then the system should display job postings belonging to the "Information Technology" category

  Scenario: Clear category search
    Given the job seeker has selected a category
    When the job seeker selects "All Categories"
    And clicks the "Search Jobs" button
    Then the system should display all available job postings

  ##########################################################
  # Location Filter
  ##########################################################

  Scenario: Filter jobs by location
    Given search results are displayed
    When the job seeker selects the location "Kuala Lumpur"
    Then the system should display only job postings located in "Kuala Lumpur"

  Scenario: Filter jobs by multiple locations
    Given search results are displayed
    When the job seeker selects the locations "Kuala Lumpur" and "Selangor"
    Then the system should display job postings from either selected location

  Scenario: Remove location filter
    Given the location filter is applied
    When the job seeker clears all selected locations
    Then the system should display all available job postings

  ##########################################################
  # Position Filter
  ##########################################################

  Scenario: Filter jobs by position
    Given search results are displayed
    When the job seeker selects the position "Full Time"
    Then the system should display only "Full Time" job postings

  Scenario: Filter jobs by multiple positions
    Given search results are displayed
    When the job seeker selects "Full Time" and "Internship"
    Then the system should display job postings matching either selected position

  Scenario: Remove position filter
    Given the position filter is applied
    When the job seeker clears all selected positions
    Then the system should display all available job postings

  ##########################################################
  # Benefits Filter
  ##########################################################

  Scenario: Filter jobs by benefit
    Given search results are displayed
    When the job seeker selects the benefit "Medical"
    Then the system should display only job postings offering "Medical"

  Scenario: Filter jobs by multiple benefits
    Given search results are displayed
    When the job seeker selects the benefits "Medical" and "Remote Work"
    Then the system should display job postings offering either selected benefit

  Scenario: Remove benefits filter
    Given the benefits filter is applied
    When the job seeker clears all selected benefits
    Then the system should display all available job postings

  ##########################################################
  # Combined Search & Filter
  ##########################################################

  Scenario: Search by job title and filter by location
    When the job seeker searches for "Engineer"
    And selects the location "Kuala Lumpur"
    Then the system should display only Engineering jobs located in "Kuala Lumpur"

  Scenario: Search by category and filter by benefit
    When the job seeker selects the category "Information Technology"
    And selects the benefit "Medical"
    Then the system should display only Information Technology jobs offering "Medical"

  Scenario: Search and filter by multiple criteria
    When the job seeker searches for "Developer"
    And selects the category "Information Technology"
    And selects the location "Selangor"
    And selects the position "Full Time"
    Then the system should display only matching job postings

  ##########################################################
  # No Result
  ##########################################################

  Scenario: No matching jobs found
    When the job seeker searches for "Astronaut"
    Then the system should display the message "No jobs match your search."

  Scenario: No jobs found after filtering
    Given search results are displayed
    When the job seeker selects filters that have no matching jobs
    Then the system should display the message "No jobs match your search."

  ##########################################################
  # View Job Details
  ##########################################################

  Scenario: View job details from search results
    Given search results are displayed
    When the job seeker selects a job posting
    Then the system should display the complete job details
    And the job title should be displayed
    And the company name should be displayed
    And the job location should be displayed
    And the job benefits should be displayed