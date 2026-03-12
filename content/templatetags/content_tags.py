from django import template
import re

register = template.Library()

@register.filter
def youtube_embed(url):
    """Convert a YouTube watch URL to an embed URL."""
    # Handle youtu.be/ID short links
    short = re.match(r'https?://youtu\.be/([^?&]+)', url)
    if short:
        return f'https://www.youtube.com/embed/{short.group(1)}'
    # Handle youtube.com/watch?v=ID
    watch = re.match(r'https?://(?:www\.)?youtube\.com/watch\?v=([^&]+)', url)
    if watch:
        return f'https://www.youtube.com/embed/{watch.group(1)}'
    return url