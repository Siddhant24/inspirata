import json
import requests
import datetime
import csv
import time
import re, os, json
import urllib.request as urllib2 
import requests
try:
    from urllib.request import urlopen, Request
except ImportError:
    from urllib2 import urlopen, Request

app_id = "340963926402035"
app_secret = "b9c46f67e14f5d69c343e0df06bea0bd"
group_id = "531752773523381"

# input date formatted as YYYY-MM-DD
since_date = "2018-01-02"
until_date = "2018-01-27"

access_token = app_id + "|" + app_secret
proxyDict = {
              "http"  : "",
              "https" : "",
              "ftp"   : ""
            }

def request_until_succeed(url):
    req = Request(url)
    success = False
    while success is False:
        try:
<<<<<<< HEAD
            response = requests.get(url, proxies = proxyDict)
            if response.status_code == 200:
                success = True
=======
            response = requests.get(url)    
            # if response.getcode() == 200:
                # success = True
>>>>>>> 3e349e852b543ba36a4bbda9736e957393e6734f
        except Exception as e:
            print(e)
            time.sleep(5)

            print("Error for URL {}: {}".format(url, datetime.datetime.now()))
            print("Retrying.")

    return response.text

# Needed to write tricky unicode correctly to csv


def unicode_decode(text):
    try:
        return text.encode('utf-8').decode()
    except UnicodeDecodeError:
        return text.encode('utf-8')


def getFacebookPageFeedUrl(base_url):

    # Construct the URL string; see http://stackoverflow.com/a/37239851 for
    # Reactions parameters
    fields = "&fields=message,link,created_time,type,name,id," + \
        "comments.limit(0).summary(true),shares,reactions" + \
        ".limit(0).summary(true),from"
    url = base_url + fields

    return url


def getReactionsForStatuses(base_url):

    reaction_types = ['like', 'love', 'wow', 'haha', 'sad', 'angry']
    reactions_dict = {}   # dict of {status_id: tuple<6>}

    for reaction_type in reaction_types:
        fields = "&fields=reactions.type({}).limit(0).summary(total_count)".format(
            reaction_type.upper())

        url = base_url + fields

        data = json.loads(request_until_succeed(url))['data']

        data_processed = set()  # set() removes rare duplicates in statuses
        for status in data:
            id = status['id']
            count = status['reactions']['summary']['total_count']
            data_processed.add((id, count))

        for id, count in data_processed:
            if id in reactions_dict:
                reactions_dict[id] = reactions_dict[id] + (count,)
            else:
                reactions_dict[id] = (count,)

    return reactions_dict


def processFacebookPageFeedStatus(status):

    # The status is now a Python dictionary, so for top-level items,
    # we can simply call the key.

    # Additionally, some items may not always exist,
    # so must check for existence first

    status_id = status['id']
    status_type = status['type']

    status_message = '' if 'message' not in status else \
        unicode_decode(status['message'])
    link_name = '' if 'name' not in status else \
        unicode_decode(status['name'])
    status_link = '' if 'link' not in status else \
        unicode_decode(status['link'])

    # Time needs special care since a) it's in UTC and
    # b) it's not easy to use in statistical programs.

    status_published = datetime.datetime.strptime(
        status['created_time'], '%Y-%m-%dT%H:%M:%S+0000')
    status_published = status_published + \
        datetime.timedelta(hours=-5)  # EST
    status_published = status_published.strftime(
        '%Y-%m-%d %H:%M:%S')  # best time format for spreadsheet programs
    status_author = unicode_decode(status['from']['name'])

    # Nested items require chaining dictionary keys.

    num_reactions = 0 if 'reactions' not in status else \
        status['reactions']['summary']['total_count']
    num_comments = 0 if 'comments' not in status else \
        status['comments']['summary']['total_count']
    num_shares = 0 if 'shares' not in status else status['shares']['count']

    return (status_id, status_message, status_author, link_name, status_type,
            status_link, status_published, num_reactions, num_comments, num_shares)


def scrapeFacebookPageFeedStatus(group_id, access_token, since_date, until_date):
    with open('{}_facebook_statuses.csv'.format(group_id), 'w') as file:
        w = csv.writer(file)
        w.writerow(["status_id", "status_message", "status_author", "link_name",
                    "status_type", "status_link", "status_published",
                    "num_reactions", "num_comments", "num_shares", "num_likes",
                    "num_loves", "num_wows", "num_hahas", "num_sads", "num_angrys",
                    "num_special"])

        has_next_page = True
        num_processed = 0   # keep a count on how many we've processed
        scrape_starttime = datetime.datetime.now()

        # /feed endpoint pagenates througn an `until` and `paging` parameters
        until = ''
        paging = ''
        base = "https://graph.facebook.com/v2.9"
        node = "/{}/feed".format(group_id)
        parameters = "/?limit={}&access_token={}".format(100, access_token)
        since = "&since={}".format(since_date) if since_date \
            is not '' else ''
        until = "&until={}".format(until_date) if until_date \
            is not '' else ''

        print("Scraping {} Facebook Group: {}\n".format(
            group_id, scrape_starttime))

        while has_next_page:
            
            until = '' if until is '' else "&until={}".format(until)
            paging = '' if until is '' else "&__paging_token={}".format(paging)
            base_url = base + node + parameters + since + until + paging

            url = getFacebookPageFeedUrl(base_url)
            statuses = json.loads(request_until_succeed(url))
            reactions = getReactionsForStatuses(base_url)
            

            for status in statuses['data']:

                # Ensure it is a status with the expected metadata
                if 'reactions' in status:
                    status_data = processFacebookPageFeedStatus(status)
                    reactions_data = reactions[status_data[0]]

                    # calculate thankful/pride through algebra
                    num_special = status_data[7] - sum(reactions_data)
                    w.writerow(status_data + reactions_data + (num_special,))

                # output progress occasionally to make sure code is not
                # stalling
                num_processed += 1
                if num_processed % 100 == 0:
                    print("{} Statuses Processed: {}".format
                          (num_processed, datetime.datetime.now()))

            # if there is no next page, we're done.
            if 'paging' in statuses:
                next_url = statuses['paging']['next']
                until = re.search('until=([0-9]*?)(&|$)', next_url).group(1)
                paging = re.search(
                    '__paging_token=(.*?)(&|$)', next_url).group(1)

            else:
                has_next_page = False

        print("\nDone!\n{} Statuses Processed in {}".format(
              num_processed, datetime.datetime.now() - scrape_starttime))

def testFacebookPageData(page_id, access_token):
    
    # construct the URL string
    base = "https://graph.facebook.com/v2.4"
    node = "/" + page_id
    parameters = "/?access_token=%s" % access_token
    url = base + node + parameters
    import requests

    response = requests.get(url, proxies = proxyDict).json()
    # retrieve data
    # req = urllib2.Request(url)
    # response = urllib2.urlopen(req)
    print(response)
    # response
    # data = json.loads(response.read().decode('utf-8'))
    
    # print (json.dump(response, indent=4, sort_keys=True))
    

testFacebookPageData("531752773523381", access_token)


# if __name__ == '__main__':
scrapeFacebookPageFeedStatus("531752773523381", access_token, since_date, until_date)
# scrapeFacebookPageFeedStatus(group_id, access_token, since_date, until_date)


# The CSV can be opened in all major statistical programs. Have fun! :)
