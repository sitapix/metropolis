specimen-image:
	$(VENV)/python scripts/make_specimen_image.py

# Optional: librsvg and ImageMagick export the GitHub upload.
social-preview: specimen-image
	rsvg-convert --width 2560 --height 1280 documentation/social-preview.svg | magick png:- -quality 92 -strip documentation/social-preview.jpg
