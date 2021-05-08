# cowin_slot_avaialbility

This script will send notifications via whatsapp and email every 150 seconds if there is any slot available for the districts available in the csv file. 
It uses Twilio APIs to send message through whatsapp and smtp to send email. 

how to: 

Edit the district_mapping.csv to remove the unnecessary districts you don't want to get notifications of. 
install/import all the required modules. 

Enter details required such as email addresses, phone number and Twilio SID &auth token. 
run cowin_main.py
