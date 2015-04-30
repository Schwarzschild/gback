#!/usr/bin/env python
# ** The MIT License **
#
# Copyright (c) 2015 The Brookhaven Group, LLC
# Author: Marc Schwarzschild
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

__doc__ = '''
  To list command line options:
   $ gback.py -h

  To list calendar names:
   $ gback.py --list --oauthfn ~/gback.oauth
  
  To add a whole day event:
   $ gback.py --add <Calendar Name> -d <YYYYMMDD> -s "<summary>"

  To export calendar to ical file:
   $ gback.py --export <CALENDAR> [--path <PATH>]

'''

__program__ = 'gback'
__version__ = 'v0.5'
__author__ = 'Marc Schwarzschild'

import sys
import os
import datetime
import dateutil.parser
import httplib2
import json
from apiclient.discovery import build
from oauth2client.file import Storage
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.tools import run
from icalendar import Calendar, Event

def Version():
    sys.stdout.write(__program__+' '+__version__+' ('+__author__+')\n')
    sys.exit(1)

def s2d(s):
  '''
  Convert YYYYMMDD formatted string to date object.
  '''
  if type(s) is datetime.date: return s
  return datetime.date(int(s[0:4]), int(s[4:6]), int(s[6:8]))

class GoogleCalendarNotFound(Exception): pass

class GCalSession(object):
  '''
    Object establishes connection to Google Calendar API.
  '''

  class _GCalendar(object):
    '''
      Convenience object for use internally to GCalSession().
    '''

    def __init__(self, session, name):

      def get_calendar_ref():
        for cal in session.allCals:
          if cal['summary'] == name: return cal
        raise GoogleCalendarNotFound('Could not find ' + str(name))

      self.session = session
      self.cal = get_calendar_ref()

    def _get_events(self):
      session = self.session
      cal = self.cal

      def getDate(x):
        try:
          t = dateutil.parser.parse(x['dateTime'])
          return t.strftime('%Y%m%dT%H%M%S')
        except KeyError:
          d = dateutil.parser.parse(x['date'])
          return d.strftime('%Y%m%d')
        return None

      ical = Calendar()
      page_token = None

      while True:
        events = session.events().\
                      list(calendarId=cal['id'], pageToken=page_token,
                           orderBy='startTime', singleEvents=True).execute()
        for event in events['items']:
          if 'cancelled' == event['status']: continue

          e = Event()

          if 'start' in event:  e['dtstart'] = getDate(event['start'])
          if 'end' in event: e['dtend'] = getDate(event['end'])

          for k in ['summary', 'location', 'description']:
            if k in event: e[k] = event[k]

          ical.add_component(e)

        page_token = events.get('nextPageToken')
        if not page_token: break

      return ical.to_ical()
      
    events = property(_get_events)

    def add(self, summary, ts, te=None, des=None, loc=None):
      '''
        If te is not provided then it must be a whole day event.
        In that case ts can be a datetime or date object.

        Arguments:
          summary -- summary
               ts -- start time.
               te -- end time.
              des -- appointment description
              loc -- appointment location

        Example ts value:
          ts = dateutil.parser.parse('20150427 09:00:00')
          ts = datetime.date(2015, 04, 27)
      '''

      cal = self.cal
      e = {}
      e['summary'] = unicode(summary)
      tz = cal['timeZone']
      if te is None:
        # Must be a day event.
        ts = te = s2d(ts).strftime('%Y-%m-%d')
        e['start'] = e['end'] = {'date':ts, 'timeZone':tz}
      else:      
        ts = ts.strftime('%Y-%m-%dT%H:%M:%S')
        te = te.strftime('%Y-%m-%dT%H:%M:%S')
        e['start'] = {'dateTime':ts, 'timeZone':tz}
        e['end'] = {'dateTime':te, 'timeZone':tz}
      if des: e['description'] = unicode(des)
      if loc: e['location'] = unicode(loc)

      events = self.session.events()
      event = events.insert(calendarId=cal['id'], body=e)
      event = event.execute()

      return event['htmlLink']

  def __init__(self, oauthfn, clientfn=None):
    '''
      Create a connection to Google Calendars and store calendar objects.

      Arguments:
         oauthfn -- name of a file containing the oath credentials.
        clientfn -- name of a file containing the client id and secret.

      The clientfn is only needed when the oauthfn file does not exist.
      If the oaauthfn file does not exist then GCalSession() will use
      your browser to propmpt for validation.  Once authenticated via
      the browser the oauthfn file will be written with stored
      credentials so subsequent connections can be made without browser
      prompting.
      
    '''

    if clientfn is None: clientfn = oauthfn
    try:
      json_data = open(os.path.expanduser(clientfn)).read()
      data = json.loads(json_data)
      if 'installed' in data: data = data['installed']
      __API_CLIENT_ID__ = data['client_id']
      __API_CLIENT_SECRET__ = data['client_secret']
    except:
      print 'Could not read', clientfn
      exit() 

    storage = Storage(os.path.expanduser(oauthfn))
    credentials = storage.get()
    if credentials is None or credentials.invalid:
      flow = OAuth2WebServerFlow(
                        client_id=__API_CLIENT_ID__,
                        client_secret=__API_CLIENT_SECRET__,
                        scope=['https://www.googleapis.com/auth/calendar',
                               'https://www.googleapis.com/auth/urlshortener'],
                        redirect_uri='urn:ietf:wg:oauth:2.0:oob',
                        euser_agent=__program__+'/'+__version__)

      credentials = run(flow, storage)
    authHttp = credentials.authorize(httplib2.Http())

    self.service = build(serviceName='calendar', version='v3', http=authHttp)
    self._cacheCalendars()

  def _cacheCalendars(self):
    '''
      Cache all the calendar objects for the given service.
    '''
    service = self.service
      
    self.allCals = allCals = []
    calList = service.calendarList().list().execute()
    while True:
      for cal in calList['items']: allCals.append(cal)
      pageToken = calList.get('nextPageToken')
      if pageToken:
          calList = service.calendarList().list(pageToken=pageToken).execute()
      else:
          break

  def __iter__(self):
    '''
      Return an iterable list of calendar objects.
    '''
    return iter(self.allCals)

  def __getitem__(self, name):
    '''
       Return a calendar object for the named calendar.
    '''
    return GCalSession._GCalendar(self, name)

  def events(self): return self.service.events()

  def _names(self): return [cal['summary'] for cal in self]
  names = property(_names)

if __name__ == '__main__':

  from argparse import ArgumentParser
  parser = ArgumentParser(description='Backup Google Calendar', usage=__doc__)
  parser.add_argument('--list', '-l', action='store_true', dest='list_f',
                      help='List calendar names.')
  parser.add_argument('-d', dest='d', metavar='YYYYMMDD')
  parser.add_argument('-s', dest='s', help='Summary string.')
  parser.add_argument('--descr', dest='descr', help='Description')
  parser.add_argument('--add', '-a', dest='add', metavar='NAME',
                      help='Export calendar to ical file.')
  parser.add_argument('--export', '-e', dest='export', metavar='NAME',
                      help='Export calendar to ical file.')
  parser.add_argument('--path', '-p', dest='path', help='Set path.',
                      default='./')
  parser.add_argument('--oauthfn', dest='oauthfn', default='~/gback.oauth',
                      metavar='FILENAME',
                      help='Set oauth credential file name.')
  parser.add_argument('--clientfn', dest='clientfn', metavar='FILENAME', 
                      help='Set client credential file name.')

  args = parser.parse_args()

  if args.list_f:
    session = GCalSession(args.oauthfn, args.clientfn)
    for c in session.names: print c
  elif args.add is not None:
    if args.d is None:
      print 'You must use -d <YYYYMMDD>'
      exit()
    if args.s is None:
      print 'You must use -s <event description>'
      exit()
      
    session = GCalSession(args.oauthfn, args.clientfn)
    print session[args.add].add(args.s, args.d, des=args.descr)
  elif args.export is not None:
    session = GCalSession(args.oauthfn, args.clientfn)
    if args.export in session.names:
      with open(os.path.join(args.path, args.export + '.ical'), 'w') as fh:
        fh.write(session[args.export].events)
    else:
      print args.export, 'is not a known calendar.'
  else:
    print __doc__

'''
Visit:
  https://console.developers.google.com/project/

Choose "Create Project"
Enter a project name.  This can be anything.
I used "gback" for google backup.
Read the agreements and agree to them if you wish to continue.
Wait while Activities windows works on setting up your project.
Select "APIs & auth" on the left pane to expand menu items.
select "Credentials"
select "Create new Client ID"
select "Installed application"

Answer consent screen information prompt.

  Select your email address and enter your project name in the "Product
  Name" field.  I entered "gback".

  Click on "Save"

If prompted to create another client id.  Click on "Cancel".

You have to repeat the following steps.  But this time "gback" should be
shown in the drop down box at the top of the web page.

select "Create new Client ID"
select "Installed application"
select "Other" for the installed application type.

Now  you should have a "Client ID for native application shown".
Select "Download JSON"

That will save a JSON file with a client_id and client_secret among
other things.  It will have a long file name but you can rename it to
anything you like, "gback.json", say.

Enable APIs:

  Under "APIs & auth" select "APIs"
  Select "Google+ API"
  Then enable it.

  Under "APIs & auth" select "APIs"
  Select "Calendar API"
  Then enable it.

  The first time you run this program it will launch your browser to log
  into your Google account.  It will get a key and save it to your named
  OAuth file using the --oauthfn arg.  After that it will read your OAuth
  file to get the key.

   $ python gback.py -l --clientfn gback.json --oauthfn gback.oauth

After logging in using on your browser click on 'Accept' when prompted that
gcalcback would ike to "Manage your calendars".

From now on the gback.py program should work using the gback.json and
gback.oauth files without need for a browser.


Note:
  Running this program requested permission which needed validation
  using a browser which did not work with w3m because it doesn't support
  Javascript.  I had to run it the first time on ny in xwindows so it
  could launch chrome for validation.  It stored keys etc using
  Storage() to a file so that it doesn't need to revalidate again.

'''        

