# Extension Icons

## Current Status

**Placeholder icons are needed!** The extension requires three icon sizes:

- `icon16.png` - 16x16 pixels (toolbar icon)
- `icon48.png` - 48x48 pixels (extension management)
- `icon128.png` - 128x128 pixels (Chrome Web Store)

## Temporary Solution

You can use the provided SVG template below and convert it to PNG using online tools or image editors.

### SVG Template (Markdown logo)

Save this as `icon.svg` and convert to PNG at different sizes:

```svg
<svg width="128" height="128" xmlns="http://www.w3.org/2000/svg">
  <!-- Background -->
  <rect width="128" height="128" rx="20" fill="#4A90E2"/>
  
  <!-- Markdown "M" and down arrow -->
  <text x="64" y="75" font-family="Arial, sans-serif" font-size="72" font-weight="bold" fill="white" text-anchor="middle">M↓</text>
</svg>
```

## How to Convert SVG to PNG

### Option 1: Online Converter (Easiest)
1. Go to https://svgtopng.com/ or https://cloudconvert.com/svg-to-png
2. Upload the `icon.svg`
3. Convert to 16x16, 48x48, and 128x128 PNG files
4. Rename and save as `icon16.png`, `icon48.png`, `icon128.png`

### Option 2: Using ImageMagick (Command Line)
```bash
# Install ImageMagick first: https://imagemagick.org/
convert icon.svg -resize 16x16 icon16.png
convert icon.svg -resize 48x48 icon48.png
convert icon.svg -resize 128x128 icon128.png
```

### Option 3: Using Inkscape
```bash
# Install Inkscape: https://inkscape.org/
inkscape icon.svg --export-filename=icon16.png --export-width=16
inkscape icon.svg --export-filename=icon48.png --export-width=48
inkscape icon.svg --export-filename=icon128.png --export-width=128
```

### Option 4: Design Your Own
Create custom icons using:
- **Figma** (free): https://figma.com
- **Canva** (free): https://canva.com
- **GIMP** (free): https://gimp.org
- **Photoshop** (paid)

**Design Guidelines:**
- Use a simple, recognizable design
- Keep high contrast for visibility
- Avoid fine details (especially for 16x16)
- Consider using a "M" + "↓" motif (Markdown + down arrow)
- Blue/white color scheme works well

## Quick Placeholder Icons

If you need something immediately, you can:

1. **Use existing Markdown editor icons** as inspiration
2. **Simple solid color squares** with "MD" text
3. **Download from icon libraries**:
   - https://icons8.com/ (search "markdown")
   - https://iconscout.com/ (search "markdown")
   - https://flaticon.com/ (search "markdown")

## Once You Have Icons

Place them in this directory (`extension/icons/`) with exact names:
```
extension/icons/
├── icon16.png
├── icon48.png
├── icon128.png
└── README.md (this file)
```

The extension will load them automatically via `manifest.json`.

## Current Workaround

Until proper icons are created, the extension will use Chrome's default icon (puzzle piece). The extension will still function normally, but will look more professional with custom icons!
