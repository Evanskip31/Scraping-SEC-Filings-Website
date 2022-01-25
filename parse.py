# import the required libraries
from bs4 import BeautifulSoup
import requests
from collections import defaultdict
import csv


# Specify the browsers - this will make the site think that the page is opened via a browser.
headers={'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36'}
# page link that has the daily filings
r = requests.get("https://www.sec.gov/cgi-bin/current?q1=0&q2=6&q3=", headers=headers)
soup = BeautifulSoup(r.content, 'html.parser') # parsing the page using BeautifulSoup and extracting its contents

# create empty lists, we'll fill them later on with data
cik_list = [] # a list of the required CIK filings
index_cik = [] # a list of the index of the above filings
base_url = 'https://www.sec.gov' # this is the base url

# Finding all hyperlinks with href
a_tag = soup.find_all('a', href=True)

# for loop to loop through all the contents of the hyperlinks
for h,chars in enumerate(a_tag):
    # for each loop, get the text of each a-tag
    text_link = chars.get_text()
    # loop through the text to find if these conditions are met. (Required filings)
    if (text_link == '10-Q' or text_link == '10-K' or text_link == '8-K'):
        index_cik.append(h) # fill the list created with data that meets this condition

for i in index_cik: #parse through the index list and get text of each a-tag
    a_text = a_tag[i].get_text()
    a_text_cik = a_tag[i+1].get_text() # the cik key of each listing is just 1 step ahead thus (+1)
    size = 10 - len(a_text_cik) # the json of each of the cik listing has 10 characters, find what's needed to get to 10
    fill_0 = str(0)*size
    final_cik = fill_0+a_text_cik
    if final_cik not in cik_list: # first find if the cik filing is not already in the cik list
        cik_list.append(final_cik) # append final result to the list created
    
# Now that we have a list of all CIK, we can move to the next step - obtaining info
print(len(cik_list))
search_forms = ['10-Q', '10-K', '8-K', '8-K/A']
x=0 # we'll use this for testing and limiting the number of filings
cik_data = {} # dictionary list to save our data

# for loop to iterate through each page, extracting the info and links
for cik in cik_list:
    
     # we want to test the first six companies. We'll remove it so we parse everything in the cik_list
    if x < 6: 
        # let's find the basic info
        data = requests.get(f'https://data.sec.gov/submissions/CIK{cik}.json', headers={'user-agent': 'Mozilla/5.0'}).json()
        cik_data[cik]=defaultdict(list)
        cik_data[cik]['name'] = data['name']
        cik_data[cik]['employee_id'] = data['ein']
        cik_data[cik]['exchanges'] = data['exchanges']
        cik_data[cik]['stateOfIncorporation'] = data['stateOfIncorporation']
        cik_data[cik]['zipCode'] = data['addresses']['mailing']['zipCode']
        cik_data[cik]['phone'] = data['phone']
        cik_data[cik]['city'] = data['addresses']['mailing']['city']
        cik_data[cik]['trading_symbol'] = data['tickers']
        cik_data[cik]['file_No.'] = data['filings']['recent']['fileNumber']
        cik_data[cik]['date_File'] = data['filings']['recent']['filingDate']
        
        # iterate through the filing date to get only filings done from 2021
        for k,item in enumerate(cik_data[cik]['date_File']):
            # split each and find index where 2021 ends, then add 1.
            date_split = item.split('-') # split the date to get the year
            if date_split[0] == '2021': # if-condition to get all possible scenarios that meet this condition
                final_index = k + 1 # to the very last 2021, we add 1 to get its index so we can iterate to that number
                print(final_index, date_split[0], k)
        cik_data[cik]['file_No.'] = data['filings']['recent']['fileNumber'][0:final_index] # getting only file numbers for companies posted this year
        cik_data[cik]['date_File'] = data['filings']['recent']['filingDate'][0:final_index] # getting only file dates for companies posted this year
                
        base_url = f'https://sec.gov/Archives/edgar/data/{cik[3:]}'
        print(final_index, 73)
        for i, form in enumerate(data['filings']['recent']['form']):
            if i < final_index:
                if form == '10-Q' or form == '10-K' or form == '8-K':
                    print(i, final_index, form)
                    if form in search_forms:
                        fname=data['filings']['recent']['primaryDocument'][i]
                        access_number=data['filings']['recent']['accessionNumber'][i]
                        access_number=''.join(access_number.split('-'))
                        # content_pages.append('/'.join([base_url, access_number, fname]))
                        cik_data[cik]['report_date', form].append(data['filings']['recent']['reportDate'][i]) # for each form and filing, we also extract the report date/ period
                        cik_data[cik][form].append('/'.join([base_url, access_number, fname]))
        x = x + 1

# Now that we have the full data as a dictionary, we will parse through each and extract the financial data

# we can now create a csv file to save each of our data once we iterate through it
with open('SEC_filings_t.csv','w',newline='') as csvfile:
    # field names that will be the title of our columns
    fieldnames = ['Name of Company', 'Trading Symbol', 'State of Incorporation', 'City', 'ZipCode', 'Employee Id', 'Phone No.', 'Exchanges', 'Form', 
                  'Financial Period', 'Total Assets', 'Total Liabilities', 'Stockholder Equity', 'Total Operating Expenses', 'Net Incone', 'Webpage'] 
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    # writer.writerows(data)
    
    # iterate through our dictionary data for the urls
    for item in cik_data:
        for each in cik_data[item]:
           
            if each == '8-K' or each == '10-K' or each == '10-Q' or each == '8-K/A': # finding possible matches
                for count,one in enumerate(cik_data[item][each]):
                    print(each, one)
                    print('\n')
                    # This is where scraping for the financial data will be done
                    # remember that we are inside each of the url link so just scraping begins
                    # scrape each of the links for financial data
                    r = requests.get(one, headers={'user-agent': 'Mozilla/5.0'})
                    soup = BeautifulSoup(r.content, 'html.parser')
                    table_rows = soup.find_all('tr') # finding all table records in the web page
                    
                    # save every other information about the company and the listing
                    name = cik_data[item]['name']
                    employee_id = cik_data[item]['employee_id']
                    exchanges = cik_data[item]['exchanges']
                    stateOfIncorporation = cik_data[item]['stateOfIncorporation']
                    zipCode = cik_data[item]['zipCode']
                    phone = cik_data[item]['phone']
                    city = cik_data[item]['city']
                    trading_symbol = cik_data[item]['trading_symbol']
                    zipCode = cik_data[item]['zipCode']
                    report_date = cik_data[item]['report_date', each][count]
                    
                    # assign each of our financial information first as not reported. Finding the info, we'll change it.
                    total_assets = ''
                    total_liabilities = ''
                    total_equity = ''
                    total_expenses = ''
                    net_income = ''
                    
                    # iterate through the table rows
                    for every in table_rows:
                        row_text = every.get_text() 
                        ## If condition to find if financial information is found
                        if 'Financial Information' in row_text or 'FINANCIAL INFORMATION' in row_text or 'FINANCIAL STATEMENTS' in row_text or 'Financial Statements' in row_text or 'Financial Statements and Supplementary Data' in row_text:
                            every = 1 # if this condition is met, we can assign every to 1
                            finance_data = soup.find_all('td')
                            break
                        else:
                            every = 0 # else, assign it to 0
                    
                    if every == 1: # mean that the page has financial info in it.
                        # obtaining assets data
                        # let's list all possible matches where total assets cell could be stored as inside the table
                        asset_text = "TOTAL"+'\n'+"    "+"ASSETS"
                        assets = ['TOTAL ASSETS', asset_text, 'Total assets', ' Total assets ', 'Total Assets', ' Total Assets ', '\nTotal Assets',
                                  'Total assets','\nTotal assets', '\nTotal Assets\n']
                        # iterate through our list above to find a match with one in that page
                        for asset in assets:
                            # iterate through the web page to look for a match
                            for k,chars in enumerate(finance_data):
                                finance_text = finance_data[k].get_text() # obtain the text for the content so that it's easy to look for the match
                                assets_data = 'None' # let's assing none, so once we have the required data we change it
                                if finance_text == asset: # if-condition that will be executed once condition is met
                                    # scrape the values for the total assets
                                    k = k + 3 # in most pages, the finance values are 3 steps away from the text
                                    # using all possible means to obtain data
                                    if finance_data[k].get_text() == '':
                                        k = k - 1
                                        if finance_data[k].get_text() == '':
                                            k = k - 1
                                    total_assets = finance_data[k].get_text() # saving data found
                                    for char in finance_data[k].get_text():
                                        if char == '\n':
                                            total_assets = total_assets.replace('\n', '')
                                    assets_data = 'Filled' # we assume that if there was a match, there obviously will be data. so assign this not to filled
                                    # we will break from this loop to save on time and avoid iterating again to another possible match
                                    break
                            if assets_data == 'Filled': # if this condition is met, we break from the loop entirely. Saving on time and avoid rewriting our current data
                                break
                            
                        # obtainig liabilities data
                        # let's list all possible matches where total liabilities cell could be stored as inside the table
                        liability_text = "TOTAL"+'\n'+"    "+"ASSETS"
                        liabilities = ['Total Liabilities', 'TOTAL LIABILITIES', 'Total liabilities', liability_text, ' Total liabilities ', 'Total current liabilities','\nTotal Liabilities',
                                       'Total Current Liabilities', '\nTotal liabilities', 'Total current liabilities', '\nTotal Liabilities\n'] #consider ('Total' in finance_text and 'Liabilities' in finance_text)
                        # iterate through our list above to find a match with one in that page
                        for liability in liabilities:
                            # iterate through the web page to look for a match
                            for k,chars in enumerate(finance_data):
                                finance_text = finance_data[k].get_text()
                                liabilities_data = 'None'
                                if finance_text == liability:
                                    # scrape the values for the total assets
                                    # we'll use all possible scenarios to find financial data. the constinue keyword will skip the current loop, finds the next match
                                    m= k + 3
                                    if finance_data[m].get_text() == '' and liability == 'Total current liabilities':
                                        m = m - 2
                                        if finance_data[m].get_text() == '':
                                            m = m + 1
                                    if finance_data[m].get_text() == '' and liability == 'Total liabilities':
                                        m = m - 1
                                        continue
                                    if finance_data[m].get_text() == '$' or finance_data[m-1].get_text() == '$':# If anything changes, see here
                                        continue
                                    total_liabilities = finance_data[m].get_text() # saving data found
                                    for char in finance_data[m].get_text():
                                        if char == '\n':
                                            total_liabilities = total_liabilities.replace('\n', '')
                                    print(total_liabilities)
                                    liabilities_data = 'Filled'
                                    # total_liabilities.append(finance_data[m].get_text())
                                    break
                            if liabilities_data == 'Filled': #set condition to break loop once we have what we are looking for
                                break
                            
                        # obtainig total liabilities and equity data
                        # let's list all possible matches where total liabilities and equity cell could be stored as inside the table
                        equity_text = "TOTAL"+'\n'+"    "+"LIABILITIES AND STOCKHOLDERS’ DEFICIT"
                        equities = ["TOTAL LIABILITIES AND STOCKHOLDERS’ DEFICIT", equity_text, "TOTAL LIABILITIES AND STOCKHOLDERS’ EQUITY (DEFICIT)", 
                                    'Total liabilities and equity', ' Total liabilities and stockholders’ deficit ', ' Total liabilities and stockholders’ equity ', " Total liabilities and stockholders' equity ",
                                    'TOTAL LIABILITIES AND EQUITY', 'Total Liabilities and Stockholders’ Equity', '\nTotal Liabilities and Stockholders’ Equity', "\nTotal Liabilities and Stockholders' Equity",
                                    "Total liabilities and stockholders' equity", 'Total liabilities and stockholders’ equity', "Total Liabilities and Shareholders’ Equity", "\nTotal liabilities and shareholders' equity",
                                    'Total liabilities and shareholders’ equity', 'Total liabilities and stockholders’ equity ',"Total liabilities and shareholders' equity",
                                    "Total Liabilities and Stockholder's Deficit", 'Total Liabilities and Stockholders’\n    Equity', 'Total liabilities and equity (deficit)',
                                    "Total liabilities, redeemable noncontrolling interests and stockholders’ equity", '\nTotal Liabilities and Stockholders’\xa0Deficit\n'] #in because the exact string won't be found. use partial match
                        for equity in equities: # iterating throught our list above
                            for k,chars in enumerate(finance_data): 
                                finance_text = finance_data[k].get_text()
                                equity_data = 'None'
                                if finance_text == equity: # proceed to find the finance values if this condition is met
                                    t = k + 3
                                    if finance_data[t].get_text() == '':
                                        t = t - 1
                                    total_equity = finance_data[t].get_text() # saving data found
                                    # parse through the contents of data obtained for special characters and remove them
                                    for char in finance_data[t].get_text():
                                        if char == '\n':
                                            total_equity = total_equity.replace('\n', '')
                                    print(total_equity)
                                    equity_data = 'Filled'
                                    break # once the data is obtained, break from the loop
                            if equity_data == 'Filled': # if this condition evaluates to true, it means there is a possibility there is data we fetched.
                                break # once the data is obtained, break from the loop
                        
                        # obtainig total operating expenses data
                        # let's list all possible matches where total operating expenses cell could be stored as inside the table
                        expense_text = "Total"+'\n'+"    "+"Operating Expenses"
                        expenses = ["Total Operating Expenses", expense_text, "Total operating expenses", ' Total operating costs and expenses ', ' Total operating cost and expenses ', '\nOperating Loss', 
                                    'Operating Income (Loss)', '\nOperating Income (Loss)', 'Net cash provided by operating activities', '\nTotal operating expenses',
                                    'Operating Expenses', 'Total Operating\n    Expenses', '\xa0\xa0\xa0\xa0 Total operating expenses', 'Loss from operations','\nTotal operating expense\n'] #in because the exact string won't be found. use partial match
                        for expense in expenses:
                            for k,chars in enumerate(finance_data):
                                finance_text = finance_data[k].get_text()
                                expense_data = 'None'
                                if finance_text == expense: # and k > t:
                                    y = k + 3
                                    if finance_data[y].get_text() == '\xa0':
                                        y = y + 1
                                    elif finance_data[y].get_text() == '':
                                        y = y - 1
                                    if finance_data[y].get_text() == '' and finance_data[y+1].get_text() == '' and finance_data[y+2].get_text() == '':
                                        y = y + 4 # continue from here
                                    if finance_data[y].get_text() == '':
                                        y = y - 1
                                    total_expenses = finance_data[y].get_text() # saving data found
                                    for char in finance_data[y].get_text():
                                        if char == '\n':
                                            total_expenses = total_expenses.replace('\n', '')
                                    print(total_expenses)
                                    expense_data = 'Filled'
                                    break
                            if expense_data == 'Filled':
                                break
                        
                        # obtainig net income data
                        # let's list all possible matches where net income cell could be stored as inside the table
                        net_income_text = "Net"+'\n'+"    "+"Loss"
                        net_income_list = ["NET INCOME", "NET INCOME (LOSS)", "NET LOSS", net_income_text, 'Net loss and comprehensive loss',"Net income", "Net Income", "Net income (loss)", 
                                           ' Net (loss) ', ' Net (loss) income ', 'Net Income (Loss)', '\nNet Income (Loss)', 'Net Loss', '\nNet loss',
                                           'Net (loss) earnings', 'Net earnings', 'Net loss', 'Net (Loss) Income','\nNet income (loss)\n', '\nNet (loss)\n'] #in because the exact string won't be found. use partial match
                        for income in net_income_list:
                            for k,chars in enumerate(finance_data):
                                finance_text = finance_data[k].get_text()
                                income_data = 'None'
                                if finance_text == income: 
                                    x = k + 3
                                    print(finance_text)
                                    # using any possible means to obtain data. continue keyword will skip this 
                                    # current loop and goes to find another match
                                    if finance_data[x].get_text() == '' and finance_data[x+1].get_text() == '' and finance_data[x-1].get_text() == '':
                                        x = x + 5 # interchanged
                                        if finance_data[x].get_text() == '':
                                            x = x - 2
                                            if finance_data[x].get_text() == '$':
                                                x = x + 1
                                   
                                    elif finance_data[x].get_text() == '': #and income == 'Net income':
                                         x = x - 1
                                         if finance_data[x].get_text() == '' and income == 'Net income':
                                             continue
                                         elif finance_data[x].get_text() == '':
                                             x = x - 1
                                             if finance_data[x].get_text() == '—\xa0':
                                                 continue
                                    elif finance_data[x].get_text() == '' and income == 'Net income':
                                        continue
                                    elif finance_data[x].get_text() == '-':
                                        continue
                                    
                                    elif finance_data[x].get_text() == '':# and income == 'Net Income':
                                        x = x - 2
                                        if finance_data[x].get_text() == '$':
                                            x = x + 1
                                    net_income = finance_data[x].get_text() # saving data found
                                    # let's remove special characters before saving
                                    for char in finance_data[x].get_text():
                                        if char == '\n':
                                            net_income = net_income.replace('\n', '')
                                        elif char == '(' or char == ')':
                                            net_income = net_income.replace('(', '')
                                            net_income = net_income.replace(')', '')
                                    income_data = 'Filled'
                                    break
                            if income_data == 'Filled':
                                break
                            
                    # saving the data we obtaned as a dictionary. Keys must be similar to fieldnames
                    data = [{'Name of Company': name, 'Trading Symbol': trading_symbol, 'State of Incorporation': stateOfIncorporation, 'City': city, 
                             'ZipCode': zipCode, 'Employee Id': employee_id, 'Phone No.': phone, 'Exchanges': exchanges, 'Form': each, 'Financial Period': report_date,
                             'Total Assets': total_assets, 'Total Liabilities': total_liabilities, 'Stockholder Equity': total_equity, 
                             'Total Operating Expenses': total_expenses, 'Net Incone': net_income, 'Webpage': one}]
                    writer.writerows(data) # this will write the rows to the file csv created above

                    