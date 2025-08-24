# Deployment Guide

This guide provides step-by-step instructions for deploying Site2MD to various free hosting platforms.

## Prerequisites

- Git installed on your machine
- GitHub account
- Basic knowledge of command line operations

## Quick Start (One-Click Deploys)

### 1. Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/new?template=https://github.com/yourusername/site2md)

**Manual Setup:**
1. Visit [Railway](https://railway.app)
2. Sign up/Login with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Connect your Site2MD repository
5. Railway will automatically detect and deploy using `railway.toml`

### 2. Render

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/yourusername/site2md)

**Manual Setup:**
1. Visit [Render](https://render.com)
2. Sign up/Login with GitHub
3. Click "New" → "Web Service"
4. Connect your GitHub repository
5. Render will use `render.yaml` for configuration
6. Service will be available at `https://your-service-name.onrender.com`

### 3. Heroku

[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/yourusername/site2md)

**Manual Setup:**
1. Install [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)
2. Login to Heroku: `heroku login`
3. Create new app: `heroku create your-app-name`
4. Deploy:
   ```bash
   git push heroku main
   ```

### 4. Vercel (API Functions)

1. Visit [Vercel](https://vercel.com)
2. Import GitHub repository
3. Vercel will use `vercel.json` configuration
4. Functions will be deployed automatically

## Local Development

### Using Docker

```bash
# Build and run with Docker Compose
docker-compose up --build

# Access at http://localhost:8000
```

### Using Python Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev,web]"

# Run web server
python -m site2md.web.main

# Access at http://localhost:8000
```

## Environment Variables

Most platforms require minimal configuration, but you can set these optional variables:

- `PORT`: Port number (auto-configured by most platforms)
- `PYTHONUNBUFFERED`: Set to "1" for real-time logs

## Platform-Specific Notes

### Railway
- Free tier: 500 hours/month
- Automatic HTTPS
- Custom domains available
- PostgreSQL addon available if needed

### Render
- Free tier: 750 hours/month
- Automatic SSL certificates
- Custom domains on paid plans
- Services sleep after 15 minutes of inactivity

### Heroku
- Free tier discontinued (paid plans start at $5/month)
- Excellent ecosystem and addons
- Automatic SSL certificates

### Vercel
- Optimized for serverless functions
- Fast global CDN
- Free tier with generous limits
- Perfect for API endpoints

## Health Checks

All deployments include health check endpoints:
- `GET /health` - Basic health check
- `GET /` - Web interface with status

## Monitoring

Check application logs on each platform:

**Railway:** Dashboard → Service → Logs
**Render:** Dashboard → Service → Logs  
**Heroku:** `heroku logs --tail -a your-app-name`
**Vercel:** Dashboard → Functions → View Function Logs

## Troubleshooting

### Common Issues

1. **Build Failures**
   - Check Python version (requires 3.11+)
   - Verify `pyproject.toml` dependencies
   - Check platform-specific logs

2. **Memory Issues**
   - Reduce concurrent crawling in large websites
   - Consider upgrading to paid tier for more resources

3. **Timeout Issues**
   - Most free tiers have 30-60 second request timeouts
   - Use smaller batch sizes for large crawls

### Performance Tips

- Enable JavaScript rendering only when necessary
- Use incremental crawling for large sites
- Set appropriate delays between requests
- Monitor resource usage on your chosen platform

## Security Considerations

- Never commit sensitive data to repository
- Use platform environment variables for secrets
- Keep dependencies updated via automated PRs
- Monitor for security vulnerabilities

## Getting Help

1. Check platform documentation
2. Review application logs
3. Test locally first with Docker
4. Check GitHub Issues for known problems

## Next Steps

After deployment:
1. Test the web interface
2. Try crawling a small website
3. Monitor performance and logs
4. Set up custom domain (if needed)
5. Configure monitoring/alerts

Your Site2MD instance will be ready for public use!