import ast
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from getpass import getpass
import json
from datetime import date
import smtplib, ssl
import time
import pandas
import requests


def send_request():
    # put data in txt file and load from it (for flexible search)
    """Send request to realtor.ca to get a list of apartments with set characteristics"""
    url = 'https://api2.realtor.ca/Listing.svc/PropertySearch_Post'
    try:
        with open('data.txt', mode='r', encoding='utf-8') as file:
            data = ast.literal_eval(file.read())
    except:
        data = {'LatitudeMax': '43.65531',
                'LongitudeMax': '-79.33186',
                'LatitudeMin': '43.62916',
                'LongitudeMin': '-79.41262',
                'Sort': '6-D',
                'PropertyTypeGroupID': '1',
                'PropertySearchTypeId': '1',
                'TransactionTypeId': '3',
                'RentMin': '2000',
                'RentMax': '2300',
                'BedRange': '1-1',
                'BuildingTypeId': '17',
                'Currency': 'CAD',
                'CultureId': '1',
                'ApplicationId': '37'}
    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
              'Chrome/87.0.4280.88 Safari/537.36'}
    # get the contents of page 1 to get total number of records
    response = requests.post(url=url, data=data, headers=headers)
    extract = json.loads(response.text)
    # get total number of records to make another request
    # with all records on one page
    records = extract['Paging']['TotalRecords']
    data['RecordsPerPage'] = records
    # sleep for 10 seconds before sending the next request
    time.sleep(10)
    # make second request to get all records
    response = requests.post(url=url, data=data, headers=headers)
    extract = json.loads(response.text)

    # with open("realtor_data.txt", mode='r', encoding='utf-8') as file1:
    #     extract = ast.literal_eval(file1.read())

    return extract


def extract_data(extract):
    """Extract only necessary info about the apartments"""
    the_list = list()
    results = extract["Results"]
    for result in results:
        the_dict = dict()
        try:
            the_dict['Bedrooms'] = result['Building']['Bedrooms']
        except:
            the_dict['Bedrooms'] = 'Not given'
        try:
            the_dict['Bathrooms'] = result['Building']['BathroomTotal']
        except:
            the_dict['Bathrooms'] = 'Not given'
        try:
            the_dict['Description'] = result['PublicRemarks']
        except:
            the_dict['Description'] = 'Not given'
        try:
            the_dict['Rent'] = result['Property']['LeaseRent']
        except:
            the_dict['Rent'] = 'Not given'
        try:
            the_dict['Address'] = result['Property']['Address']['AddressText']
        except:
            the_dict['Address'] = 'Not given'
        try:
            the_dict['Link'] = 'https://www.realtor.ca' + result['RelativeURLEn']
        except:
            the_dict['Link'] = 'Not given'
        the_list.append(the_dict)
    df = pandas.DataFrame(the_list)

    return df


def save_files(df):
    """Save extracted data into .xlsx and .html files"""
    try:
        with pandas.ExcelWriter('C:/Users/Elena/Desktop/realtor-'+str(date.today())+'.xlsx') as writer:
            df.to_excel(writer)
    except:
        print('Could not save to Excel file')
    try:
        df.to_html('realtor-'+str(date.today())+'.html', justify='center', index_names=False, render_links=True)
    except:
        print('Could not save to HTML file')


def send_email(df):
    sender_email = 'realtorcawebscraper@gmail.com'
    # sender_email = input('Enter sender email address: ')
    sender_pass = getpass('Enter sender email password: ')
    receiver_email = 'kolomeets.elena7@gmail.com'
    # receiver_email = input('Enter receiver email address: ')
    message = MIMEMultipart('alternative')
    message['Subject'] = 'Your realtor.ca search results'
    message['From'] = sender_email
    message['To'] = receiver_email

    # Create the plain-text and HTML version of the message
    text = """\
    Hi,
    
    Here should be fresh real estate search results from https://www.realtor.ca.
    If you do not see them, your email client does not display HTML content by default.   
    You can turn it on or use the .html or .xlsx files created with the same results!
    
    Enjoy!
    Elena Kolomeets
    https://github.com/elena-kolomeets"""

    # add results table to the end of html
    html = """\
    <html>
      <body>
        <p>Hi,</br>
           Here are fresh real estate search results from <a href="https://www.realtor.ca" target="_blank">Realtor Canada</a> 
           </br>
           Enjoy!</br>
           (Made by <a href="https://github.com/elena-kolomeets" target="_blank">Elena Kolomeets</a>)
        </p>
      </body>
    </html>
    """+'\n'+df.to_html(justify='center', index_names=False, render_links=True)

    # Turn these into plain/html MIMEText objects and add to MIMEMultipart message
    message.attach(MIMEText(text, 'plain'))
    message.attach(MIMEText(html, 'html'))

    # Create secure connection with server and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as server:
        try:
            server.login(sender_email, sender_pass)
        except:
            print('Could not login in the sender email')
        try:
            server.sendmail(sender_email, receiver_email, message.as_string())
        except:
            print('Could not send an email to '+receiver_email)


def main():
    """Add docs"""
    scraped_data = send_request()
    extracted_data = extract_data(scraped_data)
    save_files(extracted_data)
    send_email(extracted_data)


if __name__ == '__main__':
    main()
