Extend the existing application with a Loan Service that manages the full lifecycle of a book loan
Borrowing

- A member can only borrow a book if at least one copy is available
- A member cannot borrow the same book twice simultaneously - they must return it first
- An inactive member cannot borrow any book
- Every loan must have a due date, and that due date must be in the future
- When a loan is created, the book's available_copies must decrease by 1 atomically, the loan record and the copy count update must happen in the same transaction

Returning

A loan cannot be returned twice
When a book is returned, available_copies must increase by 1 atomically
The return timestamp must be recorded

A Member model - members are the people who borrow books. At minimum: name, email, phone, membership date, active status. Email must be unique.
A Loan model - represents a single borrowing event. Links a member to a book, tracks when it was borrowed, when it is due, and when it was returned.

Questions to think about before writing code

What happens if two members try to borrow the last copy of a book at exactly the same time? How do you prevent both loans from succeeding?
Should deleting a member be a hard delete or a soft delete, and why does your answer affect the loan table?
Where does the due date come from - should the client send it, or should the API calculate it from a configured loan period?