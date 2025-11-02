# Bootstrap 5 Offline Setup

For full offline functionality, download Bootstrap 5 assets and place them in this directory:

## Required Files

### CSS
Download from: https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css
Place at: `static/css/bootstrap.min.css`

### JavaScript
Download from: https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js
Place at: `static/js/bootstrap.bundle.min.js`

## Quick Setup Commands

```bash
cd static/css
curl -O https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css

cd ../js
curl -O https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js
```

## Alternative: Use Local CDN Mirror

If operating in a fully air-gapped environment, you can:
1. Download Bootstrap from https://getbootstrap.com/
2. Extract the dist/ folder
3. Copy bootstrap.min.css to static/css/
4. Copy bootstrap.bundle.min.js to static/js/

The application will then work completely offline without any external dependencies.
