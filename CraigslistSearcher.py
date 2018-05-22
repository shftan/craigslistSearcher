import csv
from datetime import datetime
from urllib2 import urlopen
from BeautifulSoup import BeautifulSoup
from django.utils.html import strip_entities
import re
import smtplib
from email.mime.text import MIMEText

"""
Search Craigslist for postings made today that match users' requests and email matching postings to users
"""

class CraigslistSearcher(object) :
    """
    Represents a Craigslist daily searcher
    """

    def __init__(self) :
        # Create dictionary of categories and their Craigslist abbreviations
        self.categories = {
                           'Community' : 'ccc',
                           'Gigs' : 'ggg',
                           'Housing' : 'hhh',
                           'Jobs' : 'jjj',
                           'Personals' : 'ppp',
                           'Resumes' : 'res',
                           'For Sale' : 'sss',
                           'Services' : 'bbb'
                          }

        # Create dictionary of locations and their Craigslist abbreviations
        self.locations = {}
        file = csv.reader(open('CraigslistLocations.txt','rU'),delimiter='\t')
        for line in file :
            location = line[2]
            abbreviation = line[3]
            self.locations[location] = abbreviation

        # Today's date
        self.today = datetime.now()

        # Login and password of email account that will send emails to users
        self.fromEmail = 'CraigslistSearchBot@gmail.com'
        self.password = 'huifentan'

    def search(self, searchTerm, category, location) :
        """
        Parse and store Craigslist search results
        """

        # Initialize list to store Craigslist postings
        postings = []

        # Create URL for webpage of search results. Spaces in search terms are represented by '+' in the URL
        urlPart = 'http://{2}.craigslist.org/search/?query={0}&catAbb={1}'.format(searchTerm.replace(' ','+'), self.categories[category], self.locations[location])        
        url = urlPart

        # Create variable to indicate that all postings of the day have been scrapped
        reached = False

        # Create variable to represent page number of search results
        page = 0

        while not reached :
            # Parse html
            fileHTML = BeautifulSoup(urlopen(url))

            # Extract postings
            postingsHTML = fileHTML('p')

            # Store date, title and link for each Craigslist posting made today
            for posting in postingsHTML :
                description = ''.join(posting.findAll(text=True))

                # Strip \n and \t from title
                description = description.replace('\n', '')
                description = description.replace('\t', '')

                # Strip HTML entities from title
                description = strip_entities(description)

                # Split description into date and shorter title
                descriptionSplit = description.split('-',1)
                title = descriptionSplit[1].strip()
                date = descriptionSplit[0].strip()

                # Get date information
                date = datetime.strptime(date, '%b %d')

                # Store title and link of postings made today
                if date.month == self.today.month and date.day == self.today.day :
                    link = posting('a')[0]['href']
                    # Strip title of unwanted information and characters
                    title = title[0:title.rfind(')')+1]
                    title = title.replace(' - ', ' ')
                    title = re.sub('\s{2,}',' ', title)
	            postings.append((title, link))
                else :
                    reached = True
                    break
       	    
            # Create URL of next page of search results
            page += 100
            url = urlPart + '&s=' + str(page)    
          
        return postings

    def email(self, toEmail, searchTerm, category, location, postings) :
        """
        Email search results to user
        """

        # Create line with user's request information
        request = ' for {0} in {1} in {2}'.format(searchTerm.title(), category, location)

        # Create body of email message
        if len(postings) ==  0 :  # No new postings were made today
            body = 'Sorry, we could not find any new Craigslist postings today' + request + '.\n\n'
        else :
            body = "Here are today's new Craigslist postings" + request + ':\n\n\n'
            for posting in postings :   
                body += posting[0] + '\n' + posting[1] + '\n\n' 
              
        # Add subject and email addresses
        message = MIMEText(body)
        message['Subject'] = '{0}/{1}/{2} Craigslist postings {3}'.format(self.today.month, self.today.day, self.today.year, request)
        message['From'] = self.fromEmail
        message['To'] = toEmail

	# Send email message via gmail smtp server
        s = smtplib.SMTP('smtp.gmail.com',587)
        s.ehlo()
        s.starttls()
        s.login(self.fromEmail,self.password)
        s.sendmail(self.fromEmail, toEmail, message.as_string())
        s.quit()

def main() :
    # Open file containing users' requests
    file = open('users.txt','r') 

    # Initialize Craigslist searcher
    searcher = CraigslistSearcher()

    for line in file :
        # Parse user's request
        toEmail, searchTerm, category, location = line.rstrip('\r\n').split('\t')

        # Search Craigslist postings
        postings = searcher.search(searchTerm, category, location)    

	# Email results
        searcher.email(toEmail, searchTerm, category, location, postings)

    file.close()

if __name__ == "__main__" :
    main()       
