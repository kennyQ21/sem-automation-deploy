# SEM Automation Platform - Backend Deployment

## 🚀 Deploy to Render.com

### 1. Upload to GitHub
- Create new repository: `sem-automation-backend`
- Upload all files from this folder
- Push to GitHub

### 2. Deploy to Render
1. Go to [render.com](https://render.com)
2. Create new "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn src.main:app --host 0.0.0.0 --port $PORT`

### 3. Set Environment Variables
Add these in Render's Environment Variables section:
```
OPENAI_API_KEY=sk-proj-your_actual_key
GOOGLE_ADS_DEVELOPER_TOKEN=your_actual_token
GOOGLE_ADS_CLIENT_ID=your_actual_client_id
GOOGLE_ADS_CLIENT_SECRET=your_actual_secret
GOOGLE_ADS_REFRESH_TOKEN=your_actual_refresh_token
GOOGLE_ADS_CUSTOMER_ID=your_actual_customer_id
DATABASE_URL=(auto-provided by Render)
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
```

### 4. Deploy
- Click "Deploy" and wait for build to complete
- Get your live backend URL

## 📊 Features
- FastAPI backend with OpenAPI docs
- Google Ads API integration
- OpenAI GPT-4 integration
- PostgreSQL with vector storage
- SEM campaign generation
- Keyword processing and evaluation
