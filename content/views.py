import json
import uuid
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Q, Value, CharField
from django.db.models.functions import Coalesce
from django.core.paginator import Paginator
from itertools import chain
from operator import attrgetter

from .models import Post, Course, Category, Enrollment
from .payments import (
    paystack_initialize, paystack_verify,
    flutterwave_initialize, flutterwave_verify,
)


ITEMS_PER_PAGE = 12


# ── Feed helpers ───────────────────────────────────────────────────────────

def _build_feed(query='', category_slug=''):
    base_filters = {'is_published': True}
    if category_slug:
        base_filters['category__slug'] = category_slug

    search_filter = Q()
    if query:
        search_filter = Q(title__icontains=query) | Q(excerpt__icontains=query)

    posts = (
        Post.objects
        .filter(**base_filters)
        .filter(search_filter)
        .select_related('category')
        .annotate(content_type=Value('post', output_field=CharField()))
    )

    courses = (
        Course.objects
        .filter(**base_filters)
        .filter(search_filter)
        .select_related('category')
        .annotate(content_type=Value('course', output_field=CharField()))
    )

    return sorted(chain(posts, courses), key=attrgetter('created_at'), reverse=True)


# ── List ───────────────────────────────────────────────────────────────────

@vary_on_cookie                   # logged-in users see their own state
@cache_page(60 * 5)               # 5 minutes
def content_list(request):
    query         = request.GET.get('q', '').strip()
    category_slug = request.GET.get('category', '').strip()
    page_number   = request.GET.get('page', 1)

    feed      = _build_feed(query, category_slug)
    paginator = Paginator(feed, ITEMS_PER_PAGE)
    page_obj  = paginator.get_page(page_number)

    selected_category = Category.objects.filter(slug=category_slug).first() if category_slug else None

    context = {
        'page_obj': page_obj,
        'query': query,
        'selected_category': selected_category,
        'category_slug': category_slug,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'content/partials/cards.html', context)

    return render(request, 'content/list.html', context)


# ── Detail pages ───────────────────────────────────────────────────────────

def post_detail(request, slug):
    post = get_object_or_404(Post, slug=slug, is_published=True)
    return render(request, 'content/post_detail.html', {'item': post})


def course_detail(request, slug):
    course = get_object_or_404(Course, slug=slug, is_published=True)

    # Check enrollment
    is_enrolled = False
    if request.user.is_authenticated and course.is_paid:
        is_enrolled = Enrollment.objects.filter(
            user=request.user, course=course, status='success'
        ).exists()

    return render(request, 'content/course_detail.html', {
        'item': course,
        'is_enrolled': is_enrolled,
    })


# ── Payment: gateway selection ─────────────────────────────────────────────

@login_required
def payment_select(request, slug):
    course = get_object_or_404(Course, slug=slug, is_published=True, is_paid=True)

    # Already enrolled — skip
    if Enrollment.objects.filter(user=request.user, course=course, status='success').exists():
        return redirect('content:course_detail', slug=slug)

    return render(request, 'content/payment_select.html', {'course': course})


# ── Payment: initiate ──────────────────────────────────────────────────────

@login_required
def payment_initiate(request, slug):
    if request.method != 'POST':
        return redirect('content:payment_select', slug=slug)

    course  = get_object_or_404(Course, slug=slug, is_published=True, is_paid=True)
    gateway = request.POST.get('gateway')  # 'paystack' or 'flutterwave'

    if gateway not in ('paystack', 'flutterwave'):
        messages.error(request, "Invalid payment gateway.")
        return redirect('content:payment_select', slug=slug)

    # Create pending enrollment
    reference  = uuid.uuid4()
    enrollment = Enrollment.objects.create(
        user=request.user,
        course=course,
        gateway=gateway,
        reference=reference,
        status='pending',
        amount=course.price,
    )

    callback_url = request.build_absolute_uri(
        f'/payment/verify/{gateway}/{reference}/'
    )

    try:
        if gateway == 'paystack':
            redirect_url = paystack_initialize(
                email=request.user.email,
                amount_ngn=course.price,
                reference=reference,
                callback_url=callback_url,
            )
        else:
            redirect_url = flutterwave_initialize(
                email=request.user.email,
                amount_ngn=course.price,
                reference=reference,
                callback_url=callback_url,
                course_title=course.title,
            )
    except Exception:
        enrollment.status = 'failed'
        enrollment.save()
        messages.error(request, "Could not reach payment provider. Please try again.")
        return redirect('content:payment_select', slug=slug)

    return redirect(redirect_url)


# ── Payment: verify (callback from gateway) ───────────────────────────────

@login_required
def payment_verify(request, gateway, reference):
    enrollment = get_object_or_404(Enrollment, reference=reference, user=request.user)

    if enrollment.status == 'success':
        messages.success(request, "You're already enrolled.")
        return redirect('content:course_detail', slug=enrollment.course.slug)

    try:
        if gateway == 'paystack':
            verified = paystack_verify(str(reference))
        else:
            # Flutterwave sends transaction_id as a query param
            transaction_id = request.GET.get('transaction_id')
            verified = flutterwave_verify(transaction_id) if transaction_id else False
    except Exception:
        verified = False

    if verified:
        enrollment.status      = 'success'
        enrollment.verified_at = timezone.now()
        enrollment.save()
        messages.success(request, f"You're now enrolled in {enrollment.course.title}!")
    else:
        enrollment.status = 'failed'
        enrollment.save()
        messages.error(request, "Payment could not be verified. Please contact support.")

    return redirect('content:course_detail', slug=enrollment.course.slug)


# ── Profile ────────────────────────────────────────────────────────────────

@login_required
def profile(request):
    enrollments = Enrollment.objects.filter(
        user=request.user, status='success'
    ).select_related('course', 'course__category').order_by('-created_at')

    if request.method == 'POST':
        # Simple profile name update — allauth handles password/email
        first = request.POST.get('first_name', '').strip()
        last  = request.POST.get('last_name', '').strip()
        request.user.first_name = first
        request.user.last_name  = last
        request.user.save()
        messages.success(request, "Profile updated.")
        return redirect('content:profile')

    return render(request, 'content/profile.html', {'enrollments': enrollments})