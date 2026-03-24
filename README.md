# NCC_-SCADA_REPORT_Automation
============================================================
  NEXUS SYNC PRO — Deployment Guide
  Enterprise Automation Suite v9.0
============================================================

WHAT'S INSIDE THIS FOLDER
--------------------------
  NexusSync.exe          — Main application (double-click to run)
  .env                   — Portal login credentials
  whatsapp_contacts.txt  — WhatsApp broadcast contact list

FIRST-TIME SETUP ON A NEW MACHINE
----------------------------------
1. Copy the entire "NexusSync" folder to the target PC
   (keep all files together — do NOT move just the .exe)

2. Edit ".env" with the correct credentials:
      PORTAL_USER=YOUR_USERNAME
      PORTAL_PASS=YOUR_PASSWORD
      PORTAL_DISTRICT=Sitapur

3. Ensure Google Chrome is installed on the target machine.
   The app downloads ChromeDriver automatically on first run.

4. Double-click NexusSync.exe to launch.

HOW IT WORKS
------------
• On startup you will be asked to choose a base data folder.
  The app creates a dated sub-folder (DD-MM-YYYY) inside it.
  If the folder already exists, your previous files are reused.

• Use "AUTO-PILOT MODE" toggle for fully automatic operation:
    - Data pulled hourly (08:00 – 19:00)
    - WhatsApp broadcast sent at 18:05
    - Final Excel report auto-generated after broadcast

• Manual controls are available in the sidebar at any time.

WHATSAPP FIRST-TIME USE
------------------------
• First time WhatsApp Web opens you must scan the QR code.
  After that, the login is remembered in Nexus_Chrome_Profile.

TROUBLESHOOTING
---------------
• "Credentials missing" error → check the .env file
• Chrome doesn't open        → install/update Google Chrome
• Download times out          → check internet / VPN access
• WhatsApp QR keeps appearing → delete Nexus_Chrome_Profile
                                folder and re-scan once

CONTACT
-------
For support contact the system administrator.
============================================================
