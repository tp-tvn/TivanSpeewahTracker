# Drill Tracker

A Streamlit-based drilling project tracking dashboard with real-time cost analysis, budget management, and admin controls.

## Features

- **Dashboard** — Real-time drilling activity tracking and cost analysis
- **Admin Panel** — Manage rates, budgets, drill hole purposes, and settings
- **Rate Management** — Track and update drilling rates by rig and activity type
- **Budget Tracking** — Monitor costs against budget targets by drill type
- **Weather Integration** — Track weather events and impacts on drilling
- **PLOD Integration** — Import and track drilling data from SharePoint

## Quick Start

### Prerequisites
- Python 3.10+
- Pip (Python package manager)

### Local Installation

1. Clone the repository:
```bash
git clone https://github.com/your-org/drill-tracker.git
cd drill-tracker
```

2. Install dependencies:
```bash
pip install -r app/requirements.txt
```

3. Run the dashboard:
```bash
streamlit run app/app.py
```

## Deployment

### Streamlit Cloud (Recommended)

1. Push code to GitHub
2. Sign up at [streamlit.io/cloud](https://streamlit.io/cloud)
3. Connect your GitHub repo
4. Click "Deploy" — app will be live at `your-app.streamlit.app`

## Project Structure

```
drill-tracker/
├── app/
│   ├── app.py              # Main dashboard
│   ├── admin.py            # Admin panel
│   ├── db.py               # Database functions
│   ├── requirements.txt    # Dependencies
│   └── logo.png
├── config/                 # Configuration files
├── data/                   # Generated at runtime
├── README.md
└── .gitignore
```

## Support

For issues, contact your system administrator.

## Development & Staging

### Two Environments
- **Production**: https://tivanspeewahtracker.streamlit.app/ (main branch, users use this)
- **Staging**: https://tivanspeewahtracker-developer.streamlit.app/ (develop branch, test here first)

### Development Workflow
1. Create a branch from `develop` or work directly on `develop`
2. Make changes and test locally: `python -m streamlit run app/app.py`
3. Commit: `git add . && git commit -m "description"`
4. Push to develop: `git push origin develop`
5. Wait 30-60 seconds for Streamlit Cloud to deploy to staging
6. Test thoroughly at staging URL
7. When ready for production: `git push origin develop:main`
8. Wait 30-60 seconds for production deployment
