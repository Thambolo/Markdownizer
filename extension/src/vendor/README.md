# Extension Vendor Libraries

## Required: Mozilla Readability.js

Download the Readability.js library to this directory:

### Option 1: Using curl (PowerShell/Linux/Mac)

```bash
# From the extension/vendor directory
curl -o readability.js https://raw.githubusercontent.com/mozilla/readability/main/Readability.js
```

### Option 2: Using PowerShell

```powershell
# From the extension/vendor directory
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/mozilla/readability/main/Readability.js" -OutFile "readability.js"
```

### Option 3: Manual Download

1. Go to: https://github.com/mozilla/readability
2. Navigate to `Readability.js` file
3. Click "Raw" button
4. Save file as `readability.js` in this directory

## Verification

After downloading, this directory should contain:
- `readability.js` (required)
- `README.md` (this file)

## About Readability.js

Readability.js is Mozilla's library for extracting clean, readable content from web pages. It's the same technology used in Firefox Reader View.

- **License**: Apache 2.0
- **Repository**: https://github.com/mozilla/readability
- **Purpose**: Extracts main content from articles while removing ads, navigation, and boilerplate
