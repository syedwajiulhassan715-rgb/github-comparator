#GitHub Repo Comparator 

Paste upto 5 Github repos URLs and get an Ai powered side by side comparison. 
What each project does, tech stack, complexity level, begineer friendliness, and a final recommendation. 


##Stack
-Python 3.13
- GitHub API
- Groq API (llama-3.3-70b)
- python-dotenv

## Setup
1. Clone the repo
2. Create virtual environment: `python -m venv venv`
3. Activate: `venv\Scripts\Activate`
4. Install: `pip install -r requirements.txt`
5. Create `.env` file:

GROQ_API_KEY=your_groq_key_here
6. Run: `python main.py`

## Notes
- Free Groq API key at console.groq.com
- Keep READMEs under 2000 chars per repo for free tier
- Minimum 2 repos required for comparison

## Project Status
v1.0 — working.