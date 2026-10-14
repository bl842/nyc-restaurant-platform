# GitHub deployment

Create an accessible repository, preferably named `nyc-restaurant-platform`. A public repository supports GitHub Pages on GitHub Free. Initializing it with a README gives the connector an existing branch and commit to update. Grant the connected GitHub app access to this repository before requesting upload.

The prepared files belong at the repository root: `index.html`, `.nojekyll`, README, scripts, data, outputs, charts and business documents. Do not upload only the ZIP archive if the goal is a live dashboard. The HTML is self-contained and needs no server-side Python or database process.

After upload, open repository Settings, then Pages. Under Build and deployment, choose Deploy from a branch, select main and /(root), then Save. Follow the publishing status and use the exact live URL returned by GitHub. Pages is enabled and the public dashboard is live at https://bl842.github.io/nyc-restaurant-platform/. HTTP access and the published dashboard content were verified on 14 October 2026.

For future updates, rebuild the analysis and maps using the commands in README. build_dashboard.py writes both HTML files. Commit the updated index.html to the configured publishing branch. No external map tile key is required.

The prepared local copy passed file-integrity and static-deployment checks. Existing calculation and DOM tests are retained. Actual published-site browser QA remains pending.
