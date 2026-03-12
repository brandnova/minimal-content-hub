import uuid
from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User
from django_ckeditor_5.fields import CKEditor5Field
from .utils import convert_to_webp, webp_filename


# ── Site Settings (singleton) ──────────────────────────────────────────────

class SiteSettings(models.Model):
    site_name       = models.CharField(max_length=100, default='The Hub')
    tiktok_handle   = models.CharField(max_length=100, blank=True, help_text="Without @")
    instagram_handle = models.CharField(max_length=100, blank=True, help_text="Without @")
    youtube_handle  = models.CharField(max_length=100, blank=True, help_text="Without @")
    contact_email   = models.EmailField(blank=True)

    class Meta:
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'

    def __str__(self):
        return self.site_name

    def save(self, *args, **kwargs):
        # Enforce singleton — only one row ever exists
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


# ── Category ───────────────────────────────────────────────────────────────

class Category(models.Model):
    name        = models.CharField(max_length=100, unique=True)
    slug        = models.SlugField(unique=True, blank=True, max_length=120)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# ── Abstract base ──────────────────────────────────────────────────────────

class BaseContent(models.Model):
    title       = models.CharField(max_length=200)
    slug        = models.SlugField(unique=True, blank=True, max_length=220)
    category    = models.ForeignKey(
        Category, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='%(class)s_items'
    )
    thumbnail   = models.ImageField(upload_to='thumbnails/', blank=True, null=True)
    excerpt     = models.TextField(max_length=300)
    body        = CKEditor5Field(config_name='default')
    is_published = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['is_published', '-created_at']),
            models.Index(fields=['category', 'is_published']),
        ]

    def save(self, *args, **kwargs):

        if not self.slug:
            base_slug = slugify(self.title)

            # short uuid for uniqueness
            uid = uuid.uuid4().hex[:8]

            self.slug = f"{base_slug}-{uid}"

        # Convert thumbnail to WebP on first upload or replacement
        if self.thumbnail:
            # _committed=False means it's a fresh upload, not an already-saved file
            if not getattr(self.thumbnail, '_committed', True):
                webp_content = convert_to_webp(self.thumbnail)
                new_name = webp_filename(self.thumbnail.name)
                self.thumbnail.save(new_name, webp_content, save=False)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


# ── Post ───────────────────────────────────────────────────────────────────

class Post(BaseContent):
    class Meta(BaseContent.Meta):
        verbose_name = 'Post'
        verbose_name_plural = 'Posts'


# ── Course ─────────────────────────────────────────────────────────────────

class Course(BaseContent):
    intro_video_url         = models.URLField(blank=True, null=True)
    external_resource_url   = models.URLField(blank=True, null=True)
    external_resource_label = models.CharField(max_length=100, blank=True)

    # Payment fields
    is_paid = models.BooleanField(
        default=False,
        help_text="If enabled, the external resource URL is locked behind payment."
    )
    price = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        help_text="Price in NGN (Naira). Leave blank if free."
    )

    class Meta(BaseContent.Meta):
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'

    @property
    def is_free(self):
        return not self.is_paid or not self.price


# ── Enrollment ─────────────────────────────────────────────────────────────

class Enrollment(models.Model):
    GATEWAY_CHOICES = [
        ('paystack', 'Paystack'),
        ('flutterwave', 'Flutterwave'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]

    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course      = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    gateway     = models.CharField(max_length=20, choices=GATEWAY_CHOICES)
    reference   = models.CharField(max_length=200, unique=True, default=uuid.uuid4)
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    amount      = models.DecimalField(max_digits=10, decimal_places=2)
    created_at  = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'course')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} → {self.course.title} [{self.status}]"