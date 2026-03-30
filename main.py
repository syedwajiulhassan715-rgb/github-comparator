import re
import os
from sys import set_coroutine_origin_tracking_depth
import requests
from groq import Groq
#from anthropic import Anthropic
from dotenv import load_dotenv
load_dotenv()
print(f"ENV CHECK: {os.environ.get('GOOGLE_API_KEY')}")

#client = Anthropic() #think this as opening a connection to Claude that you reuse acroos all API calls


MAX_REPOS = 5


def get_urls_from_user():
    # Prompts user to enter up to 5 GitHub URLs
    # Returns: list of URL strings
    print(f"Enter upto {MAX_REPOS} Git Hub repo URLs.")
    print("Press Enter after each . Type done when finished. ")
    
    urls = []

    while len(urls)< MAX_REPOS:
        raw = input(f"URL {len(urls) + 1}: ").strip()

        if raw.lower() == "done":
            break

        #skip if empty 
        if not raw:
            continue

        #validate it looks like a github url before accepting
        if "github.com" not in raw:
            print(" x Not a Github URL - skipping")

            continue
        urls.append(raw)
    return urls
def fetch_readme(url):
    headers = {
    "Accept": "application/vnd.github.v3.raw",
    "User-Agent": "github-comparator"
 }

    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"
    
    # Takes one GitHub URL
    # Fetches README content via GitHub API
    # Returns: readme text string, or None on failure
    try:
        parts = url.rstrip("/").split("github.com/")[-1].split("/")
        owner = parts[0]
        repo = parts[1]
    except IndexError:
        print(f"x could not parse URL: {url}")
        return None

    #Github Api endpoint for readme content
    api_url = f"https://api.github.com/repos/{owner}/{repo}/readme"

    headers = {
        "Accept": "application/vnd.github.v3.raw",
        "User-Agent": "github-comparator"
    }

    #add token if available raises rate limit
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"

    try:
        response = requests.get(api_url, headers=headers, timeout=10)
        #404 means repo exists bur has no readme
        if response.status_code == 404:
            return "NO_README"
        response.raise_for_status()

    except requests.exceptions.Timeout:
        print(f"  x Timeout fetching{url}")
        return None
    except requests.exceptions.ConnectionError:
        print(f"  x could not reach Github")
    except requests.exceptions.HTTPError as e:
        print(f"  x HTTP error: {e}")
        return None

    #check min len 
    content = response.text
    if len(content) < 50:
        return "INSUFFICIENT_DATA"
    
    return content


    #  send_to_claude(repo data):
    # Takes list of readme texts
    # Sends structured comparison prompt to Claude API
    # Returns: Claude's raw response text

def analyze_with_ai(repo_data):
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

    repos_text = ""
    for i, repo in enumerate(repo_data, 1):
        # Truncate each README to 2000 chars to stay within token limits
        readme_preview = repo['readme'][:2000]
        repos_text += f"\n--- REPO {i}: {repo['url']} ---\n"
        repos_text += readme_preview + "\n"

    prompt = f"""You are comparing {len(repo_data)} GitHub repositories
for a developer choosing which to use or learn from.

For each repo provide exactly:
- WHAT IT DOES: One sentence
- PROBLEM IT SOLVES: One sentence
- TECH STACK: Languages and frameworks mentioned
- COMPLEXITY: Beginner / Intermediate / Advanced
- BEGINNER FRIENDLY: Yes / No / Unclear
- ACTIVELY MAINTAINED: Yes / No / Unclear
- VERDICT: One sentence recommendation

If information is not explicitly stated in the README,
write "Not mentioned" — never guess or infer.

Here are the repositories:
{repos_text}

End with a RECOMMENDATION section: which repo would you
suggest for a beginner AI developer and why, in 2-3 sentences."""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000
        )
        return response.choices[0].message.content

    except Exception as e:
        print(f"Groq API error: {type(e).__name__}: {e}")
        return None



def format_comparison(claude_response,urls):

    # Takes Claude's raw text
    # Cleans and structures it for terminal display
    # Returns: formatted string

    header = "\n" + "═" * 60 + "\n"
    header += " GITHUB REPO COMPARISON\n "
    header += "="*60 +"\n"

    #add urls analyzed for reference
    header += "\nRepos analyzed:\n"
    for i, url in enumerate(urls, 1):
        header += f" {i}.{url}\n"

    header += "\n" + "-"* 60 + "\n"

    return header + claude_response + "\n" + "="*60
def run_comparator():
    # Orchestrates all four functions in order
    # Entry point — called at the bottom of the file
    print("\n" +"=" *60)
    print(" GITHUB REPO COMPARATOR")
    print("="* 60)

    #1
    urls = get_urls_from_user()

    if not urls:
        print("\nNo URLs provided. Exiting.")
        return
    
    if len(urls) <2:
        print("\nNeed atleast 2 repos to compare. Exiting")
        return

    #2 fetch README for each url
    print(f"\nFetching {len(urls)} repos...")
    repo_data = []

    for url in urls:
        print(f"\n {url}")
        readme = fetch_readme(url)

        if readme is None:
            print(f" Skipping - could not fetch ")
            continue
        elif readme == "NO_README":
            print(f" Skipping- no README found")
            continue
        elif readme == "INSUFFICIENT_DATA":
            print(f" Skipping - README too short to analyze")
            continue
        
        print(f" Fetched ({len(readme)} chars)")
        repo_data.append({"url": url, "readme": readme})
        
    if len(repo_data) < 2:
        print("\nNot enough calid repos to compare.")
        print("check that your URLs have meaningful READMEs.")
        return

        #3 send to claude 
    print(f"\nSending {len(repo_data)} repos to Claude for analysis...")
    ai_response = analyze_with_ai(repo_data)

    if ai_response is None:
        print("AI analysis failed. Check your API key.")
        return

    output =  format_comparison(ai_response, [r["url"] for r in repo_data])
    print(output)

if __name__ == "__main__":
    run_comparator()
