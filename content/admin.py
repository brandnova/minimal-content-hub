from django.contrib import admin
from .models import Post, Course, Category, SiteSettings, Enrollment


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Branding', {'fields': ('site_name', 'contact_email')}),
        ('Social Handles', {'fields': ('tiktok_handle', 'instagram_handle', 'youtube_handle')}),
    )

    def has_add_permission(self, request):
        # Prevent creating a second row
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


class BaseContentAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'is_published', 'created_at')
    list_filter = ('category', 'is_published')
    search_fields = ('title', 'excerpt')
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ('is_published',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Content', {
            'fields': ('title', 'slug', 'category', 'thumbnail', 'excerpt', 'body')
        }),
        ('Publishing', {
            'fields': ('is_published', 'created_at', 'updated_at')
        }),
    )


@admin.register(Post)
class PostAdmin(BaseContentAdmin):
    pass


@admin.register(Course)
class CourseAdmin(BaseContentAdmin):
    fieldsets = BaseContentAdmin.fieldsets + (
        ('Course Extras', {
            'fields': ('intro_video_url', 'external_resource_url',
                       'external_resource_label', 'is_paid', 'price')
        }),
    )


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'gateway', 'status', 'amount', 'created_at')
    list_filter = ('status', 'gateway')
    search_fields = ('user__email', 'course__title', 'reference')
    readonly_fields = ('reference', 'created_at', 'verified_at')