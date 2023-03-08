#!/usr/bin/python3
"""
Send an email when a11y-review is requested on Bugzilla. This is intended to be
run periodically (e.g. cron) on a system with a local SMTP server.
"""

import os
import requests
import json
from email.mime.text import MIMEText
import smtplib

QUERY_URL = 'https://bugzilla.mozilla.org/rest/bug?include_fields=id,summary,status&bug_status=UNCONFIRMED&bug_status=NEW&bug_status=ASSIGNED&bug_status=REOPENED&f1=classification&field0-0-0=cf_a11y_review_project_flag&o1=notequals&type0-0-0=substring&v1=Graveyard&value0-0-0=requested'
DATA_FILE = os.path.expanduser("~/data/mozA11yReviewNotifier.json")
EMAIL_FROM = "Moz a11y-review request notifier <jamie+mozA11yReviewNotifier@jantrid.net>"
EMAIL_TO = "jteh@mozilla.com"
EMAIL_SUBJECT = "New a11y-review requests"

def getNewBugs():
    r = requests.get(QUERY_URL)
    if r.status_code != 200:
        raise RuntimeError("Query failed with error %d" % r.status_code)
    bugs = r.json()["bugs"]
    bugIds = {bug["id"] for bug in bugs}

    try:
        prevBugIds = set(json.load(open(DATA_FILE)))
    except FileNotFoundError:
        prevBugIds = set()

    newBugIds = bugIds - prevBugIds
    newBugs = [bug for bug in bugs if bug["id"] in newBugIds]
    newBugs.sort(key=lambda bug: bug["id"])

    json.dump(list(bugIds), open(DATA_FILE, "w"))
    return newBugs

def buildEmailBody(bugs):
    html = ("<html>\n<body>\n<p>There are new requests for a11y-review!</p>\n"
        "<ul>\n")
    for bug in bugs:
        html += (
            '<li><a href="https://bugzilla.mozilla.org/show_bug.cgi?id={id}">{id}: {summary}</a></li>\n'
            .format(id=bug["id"], summary=bug["summary"]))
    html += "</ul>\n</body>\n</html>"
    return html

def buildEmail(body):
    msg = MIMEText(body, "html", _charset="UTF-8")
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    msg["Subject"] = EMAIL_SUBJECT
    return msg

def sendEmail(msg):
    s = smtplib.SMTP("localhost")
    s.sendmail(EMAIL_FROM, [EMAIL_TO], msg)
    s.quit()

def main():
    bugs = getNewBugs()
    if not bugs:
        return
    body = buildEmailBody(bugs)
    msg = buildEmail(body)
    sendEmail(msg.as_string())

if __name__ == "__main__":
    main()
