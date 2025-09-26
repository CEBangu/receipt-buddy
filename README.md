## Receipt Reader 🧾 - v1 (Mac Only)


This app uses Gemini-2.5-flash-lite to read and extract information from grocery receipts in your gmail. It then logs this information to an excel spreadsheet for further exploration and analysis.

### Workflow:
Initially, the app look for historical emails from the sender, and populates the spreadsheet with this information. Since the free version of Gemini is being used, it is rate limited to 15 requests per minute, so it might seem a bit slow. Once this is done, the app then runs an update script every 4 hours to see if there are new emails from that sender, and if so, adds them to the spreadsheet. 

### How To:
1. **Google Cloud Setup:**

You need to set up a GoogleCloud project, and grab its credentials.json. You also need a Gemini api key. The credentials.json should be stored in the receipt-buddy directory, and the api key should be stored in a .env file in the directory:

`GEMINI_API_KEY=YourAPIKey`

2. **Setting up senders:**

You need to set your own senders. If you shop at UExpress in France, this is already done for you. The EmailGrabber assumes the receipt is the first pdf found in the email. Senders should be added in the `config.toml` as elements of that list. 
If that is not the case, then you will need to change the function. I'll add some easier customizability later. If the PDF order is mixed up sometimes then you can find it by looking for the name. Just play around with `_get_attachment_payload()` method. 

3. **Initialization:**

Once that is done, create the venv with `uv --sync locked`. Then, run the `initialize.py` script. NB! This script creates a couple of notable things. Firslty, it creates an executable to run the `update.py` on its own, to add new receipts after the historical ones are done. It also creates a plist in `~Libray/LaunchAgents` to run the update script every 4 hours, to check for new receipts. If you DO NOT want this behaviour, you can run `setup.py` manually, and then `update.py` whenever you want to look for new receipts.
