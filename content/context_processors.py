from .models import Category, SiteSettings

def site_context(request):
    return {
        'all_categories': Category.objects.all(),
        'site': SiteSettings.load(),
    }