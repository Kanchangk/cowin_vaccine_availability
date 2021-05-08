#!/usr/bin/python
# -*- coding: utf-8 -*-
import datetime
import json
import requests
import pandas as pd
import streamlit as st
from copy import deepcopy
import twilio
from twilio.rest import Client
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pretty_html_table import build_table
import random
import itertools
import time

while True:
    st.set_page_config(layout='wide', initial_sidebar_state='collapsed')


    # @st.cache(allow_output_mutation=True, suppress_st_warning=True)

    def load_mapping():
        df = pd.read_csv('district_kamrup.csv')
        return df

###############  Filter if vaccine is for 18+ #######################
    def filter_column(df, col, value):
        df_temp = deepcopy(df.loc[df[col] == value, :])
        return df_temp

###############  Filter if any slot is available for 18+ #######################
    def filter_in_stock(df, col):
        df_temp = deepcopy(df.loc[df[col] > 0, :])
        return df_temp


    # def get_location(df, col):
    #    df_temp = deepcopy(df.loc[df[col], :])
    #    return df_temp

    mapping_df = load_mapping()
    mapping_dict = pd.Series(mapping_df['district id'].values,
                             index=mapping_df['district name'
                             ].values).to_dict()
    rename_mapping = {
        'date': 'Date',
        'min_age_limit': 'Minimum Age Limit',
        'available_capacity': 'Available Capacity',
        'pincode': 'Pincode',
        'name': 'Hospital Name',
        'state_name': 'State',
        'district_name': 'District',
        'block_name': 'Block Name',
        'fee_type': 'Fees',
        }

    # numdays = st.sidebar.slider('Select Date Range', 0, 100, 10)
    unique_districts = list(mapping_df['district name'].unique())
    # unique_districts = list(mapping_df["district name"])
    (left_column_1, right_column_1) = st.beta_columns(2)
    with left_column_1:
        numdays = st.slider('Select Date Range', 0, 100, 4)
    with right_column_1:
        default_dist = unique_districts.index('Kamrup Metropolitan')

    #    default_dist = unique_districts.index(unique_districts[0])
    length = len(unique_districts)
    final_df = None

    i = 1
    for i in range(length):
        dist_inp = st.selectbox('Select District', unique_districts,
                                index=default_dist)
        default_dist = default_dist + 1
        DIST_ID = mapping_dict[dist_inp]
        base = datetime.datetime.today()
        date_list = [base + datetime.timedelta(days=x) for x in
                     range(numdays)]
        date_str = [x.strftime('%d-%m-%Y') for x in date_list]

        # for DIST_ID in unique_districts:

        for INP_DATE in date_str:

##################change user agents from the list to get rid of frequent 403 error in CoWin API #################################

            user_agent_list = [
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Safari/605.1.15'
                    ,
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0'
                    ,
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36'
                    ,
                ]

                        # Pick a random user agent

            user_agent = random.choice(user_agent_list)
            URL = \
                'https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByDistrict?district_id={}&date={}'.format(DIST_ID,
                    INP_DATE)
            headers = {'User-Agent': user_agent}
            response = requests.get(URL, headers=headers)
            if response.ok and 'centers' in json.loads(response.text):
                resp_json = json.loads(response.text)['centers']
                if resp_json is not None:
                    df = pd.DataFrame(resp_json)
                    if len(df):
                        df = df.explode('sessions')
                        df['min_age_limit'] = \
                            df.sessions.apply(lambda x: \
                                x['min_age_limit'])
                        df['available_capacity'] = \
                            df.sessions.apply(lambda x: \
                                x['available_capacity'])
                        df['date'] = df.sessions.apply(lambda x: \
                                x['date'])
                        df = df[[
                            'date',
                            'available_capacity',
                            'min_age_limit',
                            'pincode',
                            'name',
                            'state_name',
                            'district_name',
                            'block_name',
                            'fee_type',
                            ]]
                        if final_df is not None:
                            final_df = pd.concat([final_df, df])
                        else:
                            final_df = deepcopy(df)
                    else:
                        st.error('No rows in the data Extracted from the API'
                                 )
                i = i + 1
    if len(final_df):
        final_df.drop_duplicates(inplace=True)
        final_df.rename(columns=rename_mapping, inplace=True)
        final_df = filter_column(final_df, 'Minimum Age Limit', 18)
        final_df = filter_in_stock(final_df, 'Available Capacity')
        table = deepcopy(final_df)
        table.reset_index(inplace=True, drop=True)
        st.table(table)
    else:
        st.error('No Data Found')
    if final_df is not None:
        if len(final_df) > 0:

    #        hospitals = []
    #        date = []
    #        [hospitals.append(x) for x in final_df["Hospital Name"] if x not in hospitals]
    #        [date.append(x) for x in final_df["Date"] if x not in date]
    #        sms_text = str("Cowin notification : Run for vaccine at {0}".format(hospitals))
    
        # To send SMS via Twilio
     #       account_sid = 'your Account Sid'
     #       auth_token = 'your aauth token'
     #       client = Client(account_sid, auth_token)
     #       message = client.messages \
     #           .create(
     #           body=sms_text,
     #           from_='+1xxxxxxxxx', #Twilio  configured mobile number
     #           to='+91xxxxxxxxxx' #Mobile number that needs to be notified, your personal number
     #       )

        # Email notify
            fromaddr = "xxxx@gmail.com"
            toaddr = ["yyyy@gmail.com","zzzz@gmail.com"]
            dropped_df=final_df.drop(['State'], axis=1)
            for dest in toaddr:
                msg = MIMEMultipart()
                msg['From'] = fromaddr
                msg['To'] = dest
                msg['Subject'] = "CoWin Vaccine Notification from kandarpa "
                body = build_table(dropped_df, 'blue_light')
                msg.attach(MIMEText(body, 'html'))
                s = smtplib.SMTP('smtp.gmail.com', 587)
                s.starttls()
                s.login(fromaddr, "password of the mail you are using to send email")
                text = msg.as_string()
                s.sendmail(fromaddr, dest, text)
                s.quit()

    # ################################whatsapp notification#############################

            account_sid = 'Twilio account SID'
            auth_token = 'Twilio auth token'
            client = Client(account_sid, auth_token)
            num = ['whatsapp:+91xxxxxxxxxx','whatsapp:+91xxxxxxxxxx', 'whatsapp:+91xxxxxxxxxx']     # mobile number that needs to be notified
            whatsapp_df = final_df.drop(['State', 'Minimum Age Limit',
                    'Fees', 'Hospital Name', 'District'], axis=1)                       # drop unnecessary df index
            ######## Split the df so that the message does not exceed the whatsapp char limit 1600 ########
            if len(whatsapp_df) > 23:
                whatsapp_df_1 = whatsapp_df.iloc[:24, :]
                whatsapp_df_2 = whatsapp_df.iloc[24:, :]
                msg_body1 = whatsapp_df_1.to_string(index=False)
                msg_body2 = whatsapp_df_2.to_string(index=False)
                print (whatsapp_df)
                for number in num:
                    message1 = \
                        client.messages.create(from_='whatsapp:+1xxxxxxxxx'                    #Twilio  configured whatsapp number
                            , body=msg_body1, to=number)                                      
                    message2 = \
                        client.messages.create(from_='whatsapp:+1xxxxxxxxx'                     #Twilio  configured whatsapp number
                            , body=msg_body2, to=number)                                      
            else:
                msg_body = "*Kamrup metro*\n"+whatsapp_df.to_string(index=False)
                for number in num:
                    message = \
                        client.messages.create(from_='whatsapp:+1xxxxxxxxxx'
                            , body=msg_body, to=number)                                      
        else:

            pass
    else:
        pass
    time.sleep(150)
