Design and implement a system that generates a loan receipt whenever a member borrows a book from the library.

When a loan transaction is created, the system should:

Automatically generate a receipt document (in HTML and/or PDF format) containing relevant loan details such as member information, book details, borrow date, and due date.
Store the generated receipt securely in a cloud storage bucket.
Ensure that the receipt is accessible only to the respective member, using proper access control mechanisms (e.g., based on member ID or authenticated access).