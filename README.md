## Receipt Reader 🧾 - v1

A little tool that let's you extract information from digital receipts in your email, and export them into an excel spreadsheet.

Currently being used for groceries, but I suppose it could be expanded to any sort of digital receipt.

Proposed workflow:
    1. Check email for new receipts (daily) - download receipts from all emails newer than previous check.
        1.1 automate process. Will do it on timer from my computer, all other options require mucho setup. 
        1.2 Need to check how the email api works for downloading attachments. ✅
    2. Extract relevant price information via Gemini 2.5 Flash API as JSON
        2.1. document in -> json out - just have to double check that the image API supports PDF? I suppose it must. ✅
    3. Parse JSON to update Excel spreadsheet.
        3.1 Have to also create the spreadsheet. This also informs the structure of the prompt, so will be some recursive process here.
    4. Rinse & Repeat
        4.1 make it downloadable for other people?

