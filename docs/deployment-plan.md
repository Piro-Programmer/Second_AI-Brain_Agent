# Streamlit Deployment Plan: SecondSelf // AI Second Brain

This document outlines the step-by-step process for deploying the SecondSelf application on **Streamlit Community Cloud**.

## 1. Prerequisites

- A GitHub account.
- A [Streamlit Community Cloud](https://share.streamlit.io/) account connected to your GitHub.
- An API Key from your chosen LLM provider (Groq or xAI).

## 2. Prepare the Repository

Ensure your repository is pushed to GitHub and contains all necessary files for deployment. The essential files are already present in the project:
- `app.py`: The main entry point for the Streamlit app.
- `requirements.txt`: Contains all the necessary Python dependencies (`streamlit`, `groq`, `openai`, `sentence-transformers`, `numpy`, `python-frontmatter`, `pypdf`, `streamlit-agraph`, etc.).
- `.gitignore`: Ensures you don't commit your `.env` file or `__pycache__` directories.

**Command to push to GitHub (if not already done):**
```bash
git add .
git commit -m "Prepare for Streamlit deployment"
git push origin main
```

## 3. Deploy to Streamlit Community Cloud

1. Log in to [Streamlit Community Cloud](https://share.streamlit.io/).
2. Click the **"New app"** button.
3. If prompted, authorize Streamlit to access your GitHub repositories.
4. Fill out the deployment details:
   - **Repository:** Select this project's repository.
   - **Branch:** `main` (or the branch you are deploying from).
   - **Main file path:** `app.py`
5. **Do not click "Deploy!" yet.**

## 4. Configure Secrets (Environment Variables)

Streamlit Community Cloud uses "Secrets" to securely manage environment variables, replacing the local `.env` file.

1. In the deployment dialog, click on **"Advanced settings..."** (or access Settings > Secrets if the app is already deployed).
2. Locate the **"Secrets"** text box.
3. Paste the contents of your environment configuration (referencing `.env.example`). Use the TOML format:

```toml
# LLM provider: "groq" (default) or "grok"
LLM_PROVIDER="groq"

# Replace with your actual API key
GROQ_API_KEY="your_groq_key_here"

# Only needed if you are using xAI
XAI_API_KEY="your_xai_grok_key_here"
```

4. Click **"Save"**.

## 5. Launch the Application

1. Click the **"Deploy!"** button.
2. Streamlit will now spin up a container, install the dependencies listed in `requirements.txt`, and launch `app.py`.
3. The deployment process may take a few minutes as it downloads and installs packages.
4. Once completed, your app will be live and accessible via a public URL (e.g., `https://your-app-name.streamlit.app`).

## 6. Post-Deployment & Data Persistence Note

> [!WARNING]  
> **Data Persistence:** Streamlit Community Cloud environments are ephemeral. Since this app uses local directories (`docs/`, `data/`) to store notes and graph embeddings, any new notes created via the UI while hosted on Streamlit **will be lost** when the container sleeps or reboots.
> 
> For a true production deployment where you want to add notes remotely, you would need to modify the data layer to use cloud storage (like AWS S3) or a database (like Supabase or MongoDB) instead of the local filesystem.

- **Continuous Deployment:** Any pushes to the connected GitHub branch (e.g., `main`) will automatically trigger a redeployment on Streamlit.
- **Managing Secrets:** If you ever need to rotate your API keys, you can update them by going to your app's dashboard on Streamlit, clicking the three dots (`...`), selecting **"Settings"**, and editing the **"Secrets"** section.
