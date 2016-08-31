s = '''
=====
gback
=====

This package provides an simpler interface to Google calendars using 
the google-api-python-client python package and OAuth.

Examples
--------
Note: See the "Setting up the project on Google" section below before trying
the examples.


List calendar names::

    >>> from gback import GCalSession
    >>> session = GCalSession('~/gback.oauth')
    >>> 
    >>> for c in session.names: print c


Add an appointment to a named calendar::



    >>> from gback import GCalSession

    >>> # print the output will display the appiointment url.
    >>> # 'Marc' is the name of the calendar used.

    >>> session = GCalSession('~/gback.oauth')
    >>> des='Write a simpler way to use the google calendar api.'
    >>> print session['Marc'].add('Write Python code.', '20150430', des=des)



Create an ical file for all the appointments in the named calendar::

    >>> from gback import GCalSession

    >>> cal_name = 'Marc'
    >>> session = GCalSession('~/gback.oauth')
    >>> with open(cal_name + '.ical'), 'w') as fh:
    >>>   fh.write(session[cal_name].events)

Setting up the project on Google
--------------------------------
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




LICENSE
=======

The MIT License (MIT)
Copyright (c) 2015 The Brookhaven Group, LLC

Permission is hereby granted, free of charge, to any person
obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the
Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute,
sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall
be included in all copies or substantial portions of the
Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS
OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


'''

def readme(): return s