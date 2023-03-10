"""
List all bugs related to accessibility.
- Include both bugs in components specific to accessibility and bugs elsewhere
	with the access keyword.
- Map access-s ratings to severity ratings.
- Map old severity values (major and normal) to new severity values (s2 and s3).
- Present enhancement/task as severity, sorting after defects.
- Sort by severity (highest first), product and component (alphabetical), then
	creation time (most recent first).
- Output as a tab separated table.
"""

import re
import urllib.parse
import requests

QUERY_PREFIX = "https://bugzilla.mozilla.org/rest/bug?include_fields=id,summary,product,component,severity,type,whiteboard&limit=0&quicksearch="
# Quick search queries. All queries will be merged into the output list.
QUERIES = [
	"component:disability -product:thunderbird",
	"keywords:access -component:disability product:core,devtools,fenix,firefox,focus,toolkit -product:graveyard",
]

def getBugs(query):
	r = requests.get(QUERY_PREFIX + urllib.parse.quote_plus(query))
	r.raise_for_status()
	return r.json()["bugs"]

def sortKey(bug):
	severity = bug["severity"]
	if severity in ("", "--", "n/a"):
		# No/invalid severity. Sort last.
		severity = "s5"
	elif severity == "enhancement":
		# Enhancements go after all defects.
		severity = "s6"
	elif severity == "task":
		# Tasks go after enhancements.
		severity = "s7"
	bugId = int(bug["id"])
	# We want to sort descending on bug id to get most recent bugs first, so
	# multiply by -1.
	bugId *= -1
	return severity, bug["product"], bug["component"], bugId

RE_ACCESS_S = re.compile(r'\[access-(s[1234])')

def fullQuery():
	bugs = []
	for query in QUERIES:
		bugs.extend(getBugs(query))
	for bug in bugs:
		severity = bug["severity"]
		bugType = bug["type"]
		m = RE_ACCESS_S.search(bug["whiteboard"])
		if m:
			# Map access-s whiteboard tag to severity.
			severity = m.group(1)
		elif bugType != "defect":
			# Severity is irrelevant for enhancements/tasks, so put that in the
			# severity field.
			severity = bugType
		else:
			severity = severity.lower()
			# Map some old severity values to new ones.
			if severity == "major":
				severity = "s2"
			elif severity == "normal":
				severity = "s3"
		bug["severity"] = severity
	return sorted(bugs, key=sortKey)

def main():
	bugs = fullQuery()
	for bug in bugs:
		print('{id}\t{summary}\t{severity}\t{product}\t{component}'.format(**bug))

if __name__ == "__main__":
	main()
