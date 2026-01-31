# Budgy 2.0

## Description

### Main Components

### Usage

#### Database Structure

File name: budgy_financial_transaction.db

table name: transactions
Columns:
    - id: Integer, Primary Key, Auto Increment (unique identifier for each transaction)
    - authorized_date: DateTime
    - posted_date: DateTime
    - status: String
    - account_name: String
    - description: String
    - primary_category: String
    - detailed_category: String
    - amount: Float
    - repayment: Boolean
    - exclude: Boolean

table name: transactions
Columns:
    - id: Integer, Primary Key, Auto Increment (unique identifier for each update record)
    - datetime: DateTime
    - filename: String
    - status: String

## Challenges

- pass

## Version History

- 1.0: initial release
- 2.0: Major application overhaul. New bank requires new data pulling methods and I have significantly increased my proficiency with python.

## Future Releases

## License

This project is licensed under the MIT License - see the LICENSE.md file for details.
