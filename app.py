from shiny import App, reactive, render, ui
import urllib3
import json
import pandas as pd
import os

http = urllib3.PoolManager()

app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.input_text("github_handle", "GitHub Username:", placeholder="octocat"),
        ui.input_action_button("fetch", "Fetch Repositories"),
        ui.tags.hr(),
        ui.tags.div(
            "This app fetches public repository information from GitHub.",
            style="font-size: 0.8em; color: #666;"
        )
    ),
    ui.card(
        ui.card_header("Repository Information"),
        ui.output_table("repo_table")
    )
)

def server(input, output, session):
    
    @reactive.calc
    def fetch_repos():
        # Only update when the fetch button is clicked
        input.fetch()
        
        if not input.github_handle():
            return pd.DataFrame(columns=["Repository", "Primary Language"])
        
        url = f"https://api.github.com/users/{input.github_handle()}/repos"
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Shiny-App"
        }
        
        # Add token if available in environment
        github_token = os.environ.get('GITHUB_TOKEN')
        if github_token:
            headers["Authorization"] = f"Bearer {github_token}"
        
        try:
            response = http.request("GET", url, headers=headers)
            if response.status == 200:
                repos = json.loads(response.data.decode('utf-8'))
                data = [(repo["name"], repo["language"] or "Not specified") 
                        for repo in repos]
                return pd.DataFrame(data, columns=["Repository", "Primary Language"])
            elif response.status == 403:
                message = "Rate limit exceeded. GitHub allows 60 requests per hour for unauthenticated users."
                if "X-RateLimit-Remaining" in response.headers:
                    remaining = response.headers["X-RateLimit-Remaining"]
                    reset_time = response.headers["X-RateLimit-Reset"]
                    message += f"\nRemaining requests: {remaining}"
                return pd.DataFrame({"Error": [message]})
            else:
                return pd.DataFrame({"Error": [f"Failed to fetch data. Status code: {response.status}"]})
        except Exception as e:
            return pd.DataFrame({"Error": [str(e)]})

    @output
    @render.table
    def repo_table():
        df = fetch_repos()
        return df

app = App(app_ui, server)
