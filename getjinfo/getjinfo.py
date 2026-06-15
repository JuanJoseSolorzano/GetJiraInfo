import os
import requests
from requests.auth import HTTPBasicAuth
import sys
import argparse
sys.stdout.reconfigure(encoding="utf-8")#type: ignore
sys.stderr.reconfigure(encoding="utf-8")#type: ignore

JIRA_SERVER = os.getenv("JIRA_SERVER","")
USERNAME = os.getenv("JIRA_USERNAME","")
PASSWORD = os.getenv("JIRA_PASSWORD","")

URL = "https://{0}/rest/api/2/issue/{1}/comment"
HEADERS = {"Accept": "application/json","Content-Type": "application/json"}
PAYLOAD = {"body": ""}
SEPARATOR = '─' * 100
SEPARATOR_2 = '═' * 100

def parse_args():
    parser = argparse.ArgumentParser(description="Add a comment to a JIRA issue.")
    parser.add_argument("-q","--query", type=str, help="Custom JQL query to fetch issues.")
    parser.add_argument("-u","--user",  type=str, help="Show detailed information about the issue.")
    parser.add_argument("--all-user",   type=str, help="Show all issues assigned to the specified user.")
    parser.add_argument("-m","--max",   type=int, default=10000, help="The maximum number of results.") 
    parser.add_argument("-s","--sprint",action="store_true", default=False, help="Show issues in the current sprint.")
    parser.add_argument("--all-me", action="store_true",default=False, help="Show all issues assigned to the current user.")
    parser.add_argument("--all", action="store_true", default=False, help="Show all issues in the project.")
    parser.add_argument("--curr-sprint", action="store_true", default=False, help="Show issues in the current sprint.")
    return parser.parse_args()

def connect_jira(jql:str,maxr:int) -> requests.Response:
    url = f"https://{JIRA_SERVER}/rest/api/2/search"
    return requests.get(
        url,
        params={"jql": jql, "maxResults": maxr, "fields": "summary,status,created,assignee,timetracking"},
        auth=HTTPBasicAuth(USERNAME, PASSWORD),
        headers={"Accept": "application/json"}
    )

def create_query(args:argparse.Namespace) -> str:
    if args.sprint and args.user: # All issues in the current sprint assigned to the current user.
        jql = f'project = "KANBAN P EDS SE ETS/TAS JIRA" AND sprint in openSprints() AND assignee = {args.user} ORDER BY created DESC'
    elif args.all_me:# Default user and all issues assigned to them.
        jql = 'project = "KANBAN P EDS SE ETS/TAS JIRA" AND assignee = currentUser() ORDER BY created DESC' 
    elif args.all_user: # All issues asigned to the specific user.
        jql = f'project = "KANBAN P EDS SE ETS/TAS JIRA" AND assignee = {args.all_user} ORDER BY created DESC'
    elif args.all: # All issues in the project.
        jql = 'project = "KANBAN P EDS SE ETS/TAS JIRA" ORDER BY created DESC'
    elif args.curr_sprint: # All issues in the current sprint.
        jql = 'project = "KANBAN P EDS SE ETS/TAS JIRA" AND sprint in openSprints() ORDER BY assignee ASC'
    elif args.user: # All issues assigned to the specific user in the current sprint.
        jql = f'project = "KANBAN P EDS SE ETS/TAS JIRA" AND assignee = {args.user} ORDER BY created DESC'
    elif args.query: # Custom JQL query provided by the user.
        jql = str(args.query)
    else:
        jql = 'project = "KANBAN P EDS SE ETS/TAS JIRA" AND sprint in openSprints() AND assignee = currentUser() ORDER BY created DESC'
    return jql

def create_table(response:requests.Response,maxr:int) -> None:
    data = response.json()
    total_time = 0
    for issue in response.json().get("issues", []):
        time_estimate = issue["fields"].get("timetracking", {}).get("originalEstimateSeconds") or 0
        total_time += time_estimate
    assigned_time = f"{total_time // 3600}h {(total_time % 3600) // 60}m"
    print(SEPARATOR_2)
    print(f"{'Key':<10} │ {'Status':<15} │ {'Assignee':<25} │ Summary")
    print(SEPARATOR_2)
    # Table content
    for issue in data["issues"]:
        key = issue["key"]
        summary = issue["fields"]["summary"]
        status = issue["fields"]["status"]["name"]
        assignee = issue["fields"]["assignee"]["displayName"] if issue["fields"]["assignee"] else "Unassigned"
        assignee = assignee[:25] + "..." if len(assignee) > 25 else assignee
        summary = summary[:80] + "..." if len(summary) > 80 else summary
        print(f"{key:<10} │ {status:<15} │ {assignee:<25} │ {summary}")
    print(SEPARATOR_2)
    print(f"Total issues found:  {data['total']}")
    print(f"Max results shown:   {maxr}")
    print(f"Assigned time:       {assigned_time}")
    print(SEPARATOR)

def run()->None:
    args = parse_args()
    maxr = args.max if args.max else 10000
    jql = create_query(args)
    response = connect_jira(jql, maxr)
    response.raise_for_status()
    create_table(response, maxr)

if __name__ == "__main__":
    run()
