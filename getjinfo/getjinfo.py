import os
import sys
import requests
import argparse
from datetime import datetime
from requests.auth import HTTPBasicAuth
from rich.console import Console
from rich.table import Table
from colored import Fore, Style

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore
sys.stderr.reconfigure(encoding="utf-8")  # type: ignore

JIRA_DOMAIN = os.getenv("JIRA_DOMAIN", "")
BOARD_ID = int(os.getenv("JIRA_BOARD", ""))
JIRA_EMAIL = os.getenv("JIRA_EMAIL","")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN","")
USER = os.getenv("JIRA_USER","") 

check_env_vars = [JIRA_DOMAIN, JIRA_EMAIL, JIRA_API_TOKEN]
if not all(var != "" for var in check_env_vars):
    print(f"{Fore.RED}Error: One or more required environment variables are missing.{Style.reset}")
    print(f"{Fore.YELLOW}Please set JIRA_DOMAIN, JIRA_EMAIL, and JIRA_API_TOKEN.{Style.reset}")
    sys.exit(1)

console = Console()
auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)
headers = {"Accept": "application/json"}

def args_parse():
    parser = argparse.ArgumentParser(description="Get Jira information.")
    parser.add_argument("-b", "--board", type=int, default=BOARD_ID, help="Jira board ID (default: 19628)")
    parser.add_argument("-u", "--user", type=str, default=USER, help="Filter issues by assignee (default: None)")
    parser.add_argument("-bckl", "--backlog", action="store_true", help="Get backlog issues (default: current sprint)")
    parser.add_argument("-spr", "--sprints", action="store_true", help="Get issues for a specific sprint ID (default: current sprint)")
    return parser.parse_args()

def get_current_sprint(board_id: int):
    url = f"https://{JIRA_DOMAIN}/rest/agile/1.0/board/{board_id}/sprint?state=active"
    resp = requests.get(url, auth=auth, headers=headers)
    resp.raise_for_status()
    data = resp.json()
    return data["values"][0] if data.get("values") else None

def get_backlog_issues(board_id: int):
    url = f"https://{JIRA_DOMAIN}/rest/agile/1.0/board/{board_id}/backlog"

    issues = []
    start_at = 0
    max_results = 600

    while True:
        resp = requests.get(
            url,
            params={
                "startAt": start_at,
                "maxResults": max_results,
                "fields": "summary,status,assignee,created,timeoriginalestimate,timeestimate,timetracking"
            },
            auth=auth,
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()

        issues.extend(data.get("issues", []))

        start_at += max_results
        if start_at >= data.get("total", 0):
            break

    return issues

def print_backlog():
    issues = get_backlog_issues(BOARD_ID)

    table = Table(title=f"Backlog issues for board {BOARD_ID}")
    table.add_column("Key", style="cyan", no_wrap=True)
    table.add_column("Status", style="magenta")
    table.add_column("Assignee", style="green")
    table.add_column("Created", style="yellow")
    table.add_column("Summary", style="white")

    for issue in issues:
        fields = issue["fields"]
        created_field = fields["created"]
        data_time = datetime.strptime(created_field, "%Y-%m-%dT%H:%M:%S.%f%z")
        created = data_time.strftime("%d/%m/%Y %H:%M")
        assignee = fields["assignee"]["displayName"] if fields["assignee"] else "Unassigned"
        table.add_row(
            issue["key"],
            fields["status"]["name"],
            assignee,
            created,
            fields["summary"],
        )

    console.print(table)
    console.print(f"[bold]Total issues:[/bold] {len(issues)}")

def get_sprint_issues(sprint_id: int,user:str=""):
    url = f"https://{JIRA_DOMAIN}/rest/agile/1.0/board/{BOARD_ID}/sprint/{sprint_id}/issue"

    issues = []
    start_at = 0
    max_results = 100

    while True:
        resp = requests.get(
            url,
            params={
                "startAt": start_at,
                "maxResults": max_results,
                "fields": "summary,status,assignee,created,timeoriginalestimate,timeestimate,timetracking"
            },
            auth=auth,
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()

        issues.extend(data.get("issues", []))

        start_at += max_results
        if start_at >= data.get("total", 0):
            break

    if user != "":
        issues = [
            issue for issue in issues
            if issue["fields"]["assignee"]
            and user.lower() in issue["fields"]["assignee"]["displayName"].lower()]

    return issues

def print_current_sprint():
    sprint = get_current_sprint(BOARD_ID)

    if not sprint:
        console.print("[red]No active sprint found.[/red]")
        return
    start_date = sprint.get("startDate", "N/A")
    end_date = sprint.get("endDate", "N/A")
    if start_date != "N/A":
        start_date = datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%S.%f%z").strftime("%d/%m/%Y %H:%M")
    if end_date != "N/A":
        end_date = datetime.strptime(end_date, "%Y-%m-%dT%H:%M:%S.%f%z").strftime("%d/%m/%Y %H:%M")
    console.print(f"[bold green]Current Sprint:[/bold green] {sprint['name']}")
    console.print(f"[bold]Sprint ID:[/bold] {sprint['id']}")
    console.print(f"[bold]State:[/bold] {sprint['state']}")
    console.print(f"[bold]Start:[/bold] {start_date}")
    console.print(f"[bold]End:[/bold] {end_date}")
    console.print()
    
    issues = get_sprint_issues(sprint["id"], user=USER)
    time_for_sprint = 0
    for issue in issues:
        fields = issue["fields"]
        time_tracking = fields.get("timetracking", {})
        original_estimate_seg = time_tracking.get("originalEstimateSeconds", "N/A")
        estimate_time_hrs = original_estimate_seg / 3600 if original_estimate_seg != "N/A" else "N/A"
        time_for_sprint += estimate_time_hrs if estimate_time_hrs != "N/A" else 0

    table = Table(title=f"Issues in {sprint['name']} (Estimated Time: {time_for_sprint:.2f} hrs)")
    table.add_column("Key", style="cyan", no_wrap=True)
    table.add_column("Status", style="magenta")
    table.add_column("Assignee", style="green")
    table.add_column("Created", style="yellow")
    table.add_column("Summary", style="white")

    for issue in issues:
        fields = issue["fields"]
        created_field = fields["created"]
        data_time = datetime.strptime(created_field, "%Y-%m-%dT%H:%M:%S.%f%z")
        created = data_time.strftime("%d/%m/%Y %H:%M")
        assignee = fields["assignee"]["displayName"] if fields["assignee"] else "Unassigned"
        table.add_row(
            issue["key"],
            fields["status"]["name"],
            assignee,
            created,
            fields["summary"],
        )

    console.print(table)
    console.print(f"[bold]Total issues:[/bold] {len(issues)}")

def print_specific_sprint(sprint_id: int):
    sprint = get_sprint_issues(sprint_id, user=USER)

    if not sprint:
        console.print(f"[red]No issues found for sprint ID {sprint_id}.[/red]")
        return

    table = Table(title=f"Issues in Sprint ID {sprint_id}")
    table.add_column("Key", style="cyan", no_wrap=True)
    table.add_column("Status", style="magenta")
    table.add_column("Assignee", style="green")
    table.add_column("Created", style="yellow")
    table.add_column("Summary", style="white")

    time_for_sprint = 0
    for issue in sprint:
        fields = issue["fields"]
        created_field = fields["created"]
        time_tracking = fields.get("timetracking", {})
        original_estimate_seg = time_tracking.get("originalEstimateSeconds", "N/A")
        estimate_time_hrs = original_estimate_seg / 3600 if original_estimate_seg != "N/A" else "N/A"
        time_for_sprint += estimate_time_hrs if estimate_time_hrs != "N/A" else 0
        data_time = datetime.strptime(created_field, "%Y-%m-%dT%H:%M:%S.%f%z")
        created = data_time.strftime("%d/%m/%Y %H:%M")
        assignee = fields["assignee"]["displayName"] if fields["assignee"] else "Unassigned"
        table.add_row(
            issue["key"],
            fields["status"]["name"],
            assignee,
            created,
            fields["summary"],
        )

    console.print(table)
    console.print(f"[bold]Total issues:[/bold] {len(sprint)}")
    console.print(f"[bold]Total estimated time for sprint:[/bold] {time_for_sprint:.2f} hrs")

def all_sprints():
    url = f"https://{JIRA_DOMAIN}/rest/agile/1.0/board/{BOARD_ID}/sprint?state=active,future,closed"
    resp = requests.get(url, auth=auth, headers=headers)
    resp.raise_for_status()

    data = resp.json()

    if data.get("values"):
        for sprint in data["values"]:
            start_date = sprint.get("startDate", "N/A")
            end_date = sprint.get("endDate", "N/A")
            if start_date != "N/A":
                start_date = datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%S.%f%z").strftime("%d/%m/%Y %H:%M")
            if end_date != "N/A":
                end_date = datetime.strptime(end_date, "%Y-%m-%dT%H:%M:%S.%f%z").strftime("%d/%m/%Y %H:%M")
            console.print(f"[bold green]Current Sprint:[/bold green] {sprint['name']}")
            console.print(f"[bold]Sprint ID:[/bold] {sprint['id']}")
            console.print(f"[bold]State:[/bold] {sprint['state']}")
            console.print(f"[bold]Start:[/bold] {start_date}")
            console.print(f"[bold]End:[/bold] {end_date}")
            print_specific_sprint(sprint['id'])
            console.print()
    else:
        print("No active sprint found.")

def run():
    args = args_parse()
    if args.board:
        global BOARD_ID
        BOARD_ID = args.board
    if args.user:
        global USER
        USER = args.user

    if args.backlog:
        print_backlog()
    elif args.sprints:
        all_sprints()
    else:
        print_current_sprint() 

if __name__ == "__main__":
    run()