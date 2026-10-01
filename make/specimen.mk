specimen:
	@mkdir -p specimen/src/fonts
	cp 'fonts/webfonts/Metropolis[wght].woff2' 'fonts/webfonts/Metropolis-Italic[wght].woff2' specimen/src/fonts/
	cd specimen && bun install --frozen-lockfile && bun run build
	@echo "built specimen/_site/index.html"
