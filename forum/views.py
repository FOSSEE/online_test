from django.shortcuts import render, redirect
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages

from yaksh.models import Course
from yaksh.views import is_moderator
from yaksh.decorators import email_verified, has_profile

from .models import Post, Comment
from .forms import PostForm, CommentForm


@login_required
@email_verified
def course_forum(request, course_id):
    user = request.user
    base_template = 'user.html'
    moderator = False
    if is_moderator(user):
        base_template = 'manage.html'
        moderator = True
    course = get_object_or_404(Course, id=course_id)
    course_ct = ContentType.objects.get_for_model(course)
    if (not course.is_creator(user) and not course.is_teacher(user)
            and not course.is_student(user)):
        raise Http404('You are not enrolled in {0} course'.format(course.name))
    search_term = request.GET.get('search_post')
    if search_term:
        posts = Post.objects.filter(
                Q(title__icontains=search_term) |
                Q(description__icontains=search_term),
                target_ct=course_ct, target_id=course.id, active=True
            )
    else:
        posts = Post.objects.filter(
            target_ct=course_ct, target_id=course.id, active=True
        ).order_by('-modified_at')
    paginator = Paginator(posts, 10)
    page = request.GET.get('page')
    posts = paginator.get_page(page)
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            new_post = form.save(commit=False)
            new_post.creator = user
            new_post.target = course
            new_post.anonymous = request.POST.get('anonymous', '') == 'on'
            new_post.save()
            messages.success(request, "Added post successfully")
            return redirect('forum:post_comments',
                            course_id=course.id, uuid=new_post.uid)
    else:
        form = PostForm()
    return render(request, 'forum/course_forum.html', {
        'user': user,
        'course': course,
        'base_template': base_template,
        'moderator': moderator,
        'objects': posts,
        'form': form,
        'user': user
        })


@login_required
@email_verified
def lessons_forum(request, course_id):
    user = request.user
    base_template = 'user.html'
    moderator = False
    if is_moderator(user):
        base_template = 'manage.html'
        moderator = True
    course = get_object_or_404(Course, id=course_id)
    course_ct = ContentType.objects.get_for_model(course)
    lesson_posts = course.get_lesson_posts()
    return render(request, 'forum/lessons_forum.html', {
        'user': user,
        'base_template': base_template,
        'moderator': moderator,
        'course': course,
        'posts': lesson_posts,
    })


@login_required
@email_verified
def post_comments(request, course_id, uuid):
    user = request.user
    base_template = 'user.html'
    if is_moderator(user):
        base_template = 'manage.html'
    post = get_object_or_404(Post, uid=uuid)
    comments = post.comments.filter(active=True)
    course = get_object_or_404(Course, id=course_id)
    if (not course.is_creator(user) and not course.is_teacher(user)
            and not course.is_student(user)):
        raise Http404('You are not enrolled in {0} course'.format(course.name))
    form = CommentForm()
    if request.method == "POST":
        form = CommentForm(request.POST, request.FILES)
        if form.is_valid():
            new_comment = form.save(commit=False)
            new_comment.creator = request.user
            new_comment.post_field = post
            new_comment.anonymous = request.POST.get('anonymous', '') == 'on'
            new_comment.save()
            messages.success(request, "Added comment successfully")
            return redirect(request.path_info)
    return render(request, 'forum/post_comments.html', {
        'post': post,
        'comments': comments,
        'base_template': base_template,
        'form': form,
        'user': user,
        'course': course
        })


@login_required
@email_verified
def hide_post(request, course_id, uuid):
    user = request.user
    course = get_object_or_404(Course, id=course_id)
    if (not course.is_creator(user) and not course.is_teacher(user)):
        raise Http404(
            'Only a course creator or a teacher can delete the post.'
        )
    post = get_object_or_404(Post, uid=uuid)
    post.comment.active = False
    post.active = False
    post.save()
    messages.success(request, "Post deleted successfully")
    return redirect('forum:course_forum', course_id)


@login_required
@email_verified
def hide_comment(request, course_id, uuid):
    user = request.user
    if course_id:
        course = get_object_or_404(Course, id=course_id)
        if (not course.is_creator(user) and not course.is_teacher(user)):
            raise Http404(
                'Only a course creator or a teacher can delete the comments'
            )
    comment = get_object_or_404(Comment, uid=uuid)
    post_uid = comment.post_field.uid
    comment.active = False
    comment.save()
    messages.success(request, "Post comment deleted successfully")
    return redirect('forum:post_comments', course_id, post_uid)
