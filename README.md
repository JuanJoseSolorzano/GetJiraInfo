# getjinfo

> A Jira ticket information fetcher tool via terminal. 

`getjinfo` allows you to fetch and display JIRA ticket information directly from your terminal. This tool uses the REST API of JIRA to interact with your JIRA server, and requires environment variables for configuration.
---

## Features
  
- **Fetch JIRA Sprint information** directly from the terminal
- **Display info about the active Sprint** for the project
- **Environment variable configuration** for JIRA server, username, and password
- **Works as** a global CLI command after installation

---

## Installation

```bash
pip install getjinfo
```

Or install from source:

```bash
git clone https://github.com/JuanJoseSolorzano/getjinfo_project.git 
cd getjinfo_project
pip install .
```
## Required Environment Variables
- `JIRA_SERVER`: The URL of your JIRA server (e.g., `yourdomain.atlassian.net`).
- `JIRA_USERNAME`: Your JIRA username (usually your email address).
- `JIRA_PASSWORD`: Your JIRA API token or password.
---

## Usage

```bash

usage: getjinfo.py [-h] [-q QUERY] [-u USER] [--all-user ALL_USER] [-m MAX] [-s] [--all-me] [--all] [--curr-sprint]

Add a comment to a JIRA issue.

optional arguments:
  -h, --help            show this help message and exit

  -q, --query      QUERY      Custom JQL query to fetch issues.
  -u, --user       USER       Show detailed information about the issue.
  -m, --max        MAX        The maximum number of results.
  -s, --sprint     Show       issues in the current sprint.
  --all-user       ALL_USER   Show all issues assigned to the specified user.
  --all-me         ------     Show all  issues assigned to the current user.
  --all            ------     Show all  issues in the project.
  --curr-sprint    ------     Show issues in the current sprint.
```

### Examples

```bash
getjinfo -u juso006 -s # Show detailed information about the issue with key "juso006" in the current sprint.
getjinfo --all-me # Show all issues assigned to the current user.
getjinfo --all # Show all issues in the project.
getjinfo -s # Show issues in the current sprint.
getjinfo -q '[QUERY AS IN THE JIRA SEARCH BAR]' # Show issues based on a custom JQL query.
getjinfo --all-user juso006 # Show all issues assigned to the user "juso006".
getjinfo --all -m 50 # Show all issues in the project, but limit the results to 50.
```
---

## License

See [LICENSE](LICENSE) for details.

---

## Author

**Juan Jose Solorzano Carrillo** — juanjose.solorzano.c@gmail.com
