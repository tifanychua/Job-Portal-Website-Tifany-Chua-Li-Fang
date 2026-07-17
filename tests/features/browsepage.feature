Feature: Browse Jobs
As a Job Seeker
I want to browse available job opportunities 
So that I can find positions that match my skills and career goals.

Scenario: Job seeker browses available job opportunities
    Given job postings are available in the system
    When the job seeker opens the job listing page
    Then the system should display a list of available job opportunities

Scenario: Job seeker views job summary information
    Given the job seeker is viewing the job listing page
    When job postings are displayed
    Then the system should show the job title, company name and location

Scenario: Job seeker filters job opportunities
    Given job postings are available in the system
    When the job seeker applies filters such as job position, location, or benefits
    Then the system should display job opportunities that match the selected filters