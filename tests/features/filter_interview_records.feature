Feature: Filter Interview Records


    As an Employer
    I want to filter interview records by status
    So that I can efficiently track interview progress and manage candidate interactions throughout the recruitment process.



    Scenario: Filter interview records by status

        Given the employer has interview records with different statuses

        When the employer selects an interview status filter

        Then the system should display only interview records matching the selected status



    Scenario: View all interview records without applying status filter

        Given the employer is viewing the interview records page

        When the employer does not select any status filter

        Then the system should display all interview records



    Scenario: No interview records found for selected status

        Given the employer applies a status filter

        When no interview records match the selected status

        Then the system should display a "No interview records found" message