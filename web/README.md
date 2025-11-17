# Universe MCP - Web Frontend

Modern, interactive web interface for browsing the Universe MCP library.

## Features

- 🔍 **Real-time Search**: Search across 6,488+ servers, 428+ clients, and use cases
- 🏷️ **Advanced Filters**: Filter by classification (Official, Community, Reference)
- 📊 **Live Statistics**: View ecosystem statistics and trends
- 🎨 **Modern Design**: Beautiful dark theme with smooth animations
- 📱 **Responsive**: Works perfectly on desktop, tablet, and mobile
- ⚡ **Fast**: Client-side rendering with efficient pagination
- 🌐 **Static**: No backend required - deploy anywhere

## Quick Start

### Option 1: Python HTTP Server (Recommended)

```bash
# From the project root
python web/serve.py

# Or manually
python -m http.server 8000 --directory web
```

Then open: http://localhost:8000

### Option 2: Node.js HTTP Server

```bash
# Install http-server globally
npm install -g http-server

# Serve from web directory
cd web
http-server -p 8000
```

Then open: http://localhost:8000

### Option 3: GitHub Pages

This site is ready to be deployed to GitHub Pages:

1. Push to GitHub
2. Go to repository Settings → Pages
3. Select source: `main` branch, `/web` folder
4. Your site will be live at: `https://username.github.io/universe_mcp/`

### Option 4: Any Static Host

Deploy to:
- Netlify: Drag and drop `web/` folder
- Vercel: Import repository
- Cloudflare Pages: Connect repository
- AWS S3: Upload `web/` folder as static website

## Project Structure

```
web/
├── index.html          # Main HTML file
├── assets/
│   ├── css/
│   │   └── style.css   # All styles
│   └── js/
│       └── app.js      # Application logic
├── serve.py            # Simple Python server
└── README.md           # This file
```

## Features Overview

### Search
- Type to search across all fields (name, description, provider)
- Real-time results with 300ms debounce
- Press Enter or click Search button

### Filters
- **All**: Show all servers
- **Official**: Official servers only
- **Community**: Community servers only
- **Reference**: Reference implementations only

### Tabs
- **Servers**: Browse 6,488+ MCP servers
- **Clients**: Browse 428+ MCP clients
- **Use Cases**: See real-world examples
- **Statistics**: View ecosystem stats

### Pagination
- Load 24 items at a time
- Click "Load More" to see more results
- Automatically hides when all items loaded

## Data Sources

The frontend loads data from these JSON indexes (auto-generated):

- `../indexes/all-servers.json` - All MCP servers
- `../indexes/all-clients.json` - All MCP clients
- `../indexes/all-usecases.json` - All use cases
- `../indexes/statistics.json` - Ecosystem statistics

These indexes are automatically updated by the scraper.

## Customization

### Change Theme Colors

Edit `assets/css/style.css` and modify the CSS variables:

```css
:root {
    --primary-color: #6366f1;
    --secondary-color: #8b5cf6;
    --background: #0f172a;
    /* ... more variables ... */
}
```

### Change Items Per Page

Edit `assets/js/app.js`:

```javascript
pagination: {
    servers: { page: 1, perPage: 24 },  // Change 24 to desired number
    clients: { page: 1, perPage: 24 },
    usecases: { page: 1, perPage: 24 }
}
```

### Add More Filters

1. Add filter buttons in `initFilters()` function
2. Update `filterData()` function to apply new filters
3. Update state.filters object

## Performance

- **Initial Load**: ~2-3 seconds (loading 6,917 items)
- **Search**: <100ms (client-side filtering)
- **Filter**: <50ms (client-side filtering)
- **Pagination**: <10ms (slicing array)

## Browser Support

- Chrome/Edge: ✅ Fully supported
- Firefox: ✅ Fully supported
- Safari: ✅ Fully supported
- Mobile browsers: ✅ Fully supported

## Future Enhancements

Potential improvements:

- [ ] Advanced search syntax (AND, OR, NOT)
- [ ] Save search preferences to localStorage
- [ ] Export search results as CSV/JSON
- [ ] Dark/Light theme toggle
- [ ] Keyboard shortcuts
- [ ] URL-based filters (shareable links)
- [ ] Server comparison tool
- [ ] Integration with GitHub API for live stars/forks

## Contributing

To improve the frontend:

1. Edit HTML/CSS/JS files
2. Test locally with `python serve.py`
3. Commit changes
4. Open Pull Request

## License

MIT License - See LICENSE file in repository root

## Links

- **Repository**: https://github.com/willabs-ia/universe_mcp
- **Data Source**: https://www.pulsemcp.com
- **Issues**: https://github.com/willabs-ia/universe_mcp/issues
