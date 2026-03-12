from django.core.management.base import BaseCommand
from faker import Faker
import random
from decimal import Decimal
import uuid
from django.utils.text import slugify

from content.models import Post, Course, Category

fake = Faker()


class Command(BaseCommand):
    help = "Seed database with fake posts and courses"

    def add_arguments(self, parser):
        parser.add_argument('--posts', type=int, default=100)
        parser.add_argument('--courses', type=int, default=80)

    def handle(self, *args, **options):

        posts_count = options['posts']
        courses_count = options['courses']

        self.stdout.write(self.style.WARNING("Wiping existing posts and courses..."))

        Post.objects.all().delete()
        Course.objects.all().delete()

        # Categories
        categories = [
            "Python",
            "Django",
            "React",
            "Web Development",
            "Programming",
            "AI",
            "Startups",
            "Productivity",
        ]

        category_objs = []
        for name in categories:
            cat, _ = Category.objects.get_or_create(name=name)
            category_objs.append(cat)

        self.stdout.write(self.style.SUCCESS("Categories ready"))

        # -----------------------
        # Create Posts
        # -----------------------

        posts = []

        for _ in range(posts_count):

            title = fake.sentence(nb_words=6)
            slug = f"{slugify(title)}-{uuid.uuid4().hex[:8]}"

            posts.append(
                Post(
                    title=title,
                    slug=slug,
                    excerpt=fake.text(max_nb_chars=200),
                    body="\n\n".join(fake.paragraphs(nb=15)),
                    category=random.choice(category_objs),
                    thumbnail=None,  # <-- leave empty so template fallback works
                    is_published=True,
                )
            )

        Post.objects.bulk_create(posts)

        self.stdout.write(self.style.SUCCESS(f"{posts_count} posts created"))

        # -----------------------
        # Create Courses
        # -----------------------

        courses = []

        for _ in range(courses_count):

            title = fake.sentence(nb_words=6)
            slug = f"{slugify(title)}-{uuid.uuid4().hex[:8]}"

            is_paid = random.choice([True, False])

            price = None
            if is_paid:
                price = Decimal(random.choice([
                    2500, 5000, 7500, 10000, 15000
                ]))

            courses.append(
                Course(
                    title=title,
                    slug=slug,
                    excerpt=fake.text(max_nb_chars=200),
                    body="\n\n".join(fake.paragraphs(nb=20)),
                    category=random.choice(category_objs),
                    thumbnail=None,  # <-- fallback image will display
                    intro_video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                    external_resource_url=fake.url(),
                    external_resource_label="Download Resources",
                    is_paid=is_paid,
                    price=price,
                    is_published=True,
                )
            )

        Course.objects.bulk_create(courses)

        self.stdout.write(self.style.SUCCESS(f"{courses_count} courses created"))
        self.stdout.write(self.style.SUCCESS("Database successfully reseeded"))