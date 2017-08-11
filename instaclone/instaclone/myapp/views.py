from django.shortcuts import render, redirect
from forms import SignUpForm, LoginForm, PostForm, LikeForm, CommentForm
from models import User, SessionToken, PostModel, LikeModel, CommentModel, BrandModel, PointsModel
from django.contrib.auth.hashers import make_password, check_password
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import logout
from clarifai.rest import ClarifaiApp
from instaclone.settings import BASE_DIR


from imgurpython import ImgurClient


# Create your views here.

def signup_view(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            # saving data to DB
            user = User(name=name, password=make_password(password), email=email, username=username)
            user.save()
            return render(request, 'success.html')
            # return redirect('login/')
    else:
        form = SignUpForm()

    return render(request, 'index.html', {'form': form})


def login_view(request):
    response_data = {}
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = User.objects.filter(username=username).first()

            if user:
                if check_password(password, user.password):
                    token = SessionToken(user=user)
                    token.create_token()
                    token.save()
                    response = redirect('feed/')
                    response.set_cookie(key='session_token', value=token.session_token)
                    return response
                else:
                    response_data['message'] = 'Incorrect Password! Please try again!'

    elif request.method == 'GET':
        form = LoginForm()

    response_data['form'] = form
    return render(request, 'login.html', response_data)


def post_view(request):
    user = check_validation(request)

    if user:
        if request.method == 'POST':
            form = PostForm(request.POST, request.FILES)
            if form.is_valid():
                image = form.cleaned_data.get('image')
                caption = form.cleaned_data.get('caption')
                post = PostModel(user=user, image=image, caption=caption)
                post.save()

                path = str(BASE_DIR + '//' + post.image.url)

                client = ImgurClient("93f5a3ec5dc6e4d" ,"9c98d35936c77aa6772afb00b3eb0b56924a6bb9 ")
                post.image_url = client.upload_from_path(path, anon=True)['link']
                post.save()

                return redirect('/feed/')

        else:
            form = PostForm()
        return render(request, 'post.html', {'form': form})
    else:
        return redirect('/login/')


def feed_view(request):
    user = check_validation(request)
    if user:

        posts = PostModel.objects.all().order_by('created_on')

        for post in posts:
            existing_like = LikeModel.objects.filter(post_id=post.id, user=user).first()
            if existing_like:
                post.has_liked = True

        return render(request, 'feed.html', {'posts': posts})
    else:

        return redirect('/login/')


def like_view(request):
    user = check_validation(request)
    if user and request.method == 'POST':
        form = LikeForm(request.POST)
        if form.is_valid():
            post_id = form.cleaned_data.get('post').id
            existing_like = LikeModel.objects.filter(post_id=post_id, user=user).first()
            if not existing_like:
                LikeModel.objects.create(post_id=post_id, user=user)
            else:
                existing_like.delete()
            return redirect('/feed/')
    else:
        return redirect('/login/')


def comment_view(request):
    user = check_validation(request)
    if user and request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            post_id = form.cleaned_data.get('post').id
            comment_text = form.cleaned_data.get('comment_text')
            comment = CommentModel.objects.create(user=user, post_id=post_id, comment_text=comment_text)
            comment.save()
            return redirect('/feed/')
        else:
            return redirect('/feed/')
    else:
        return redirect('/login')

def logout_view(request):
    user = check_validation(request)
    if user is not None:
        latest_sessn = SessionToken.objects.filter(user=user).last()
        if latest_sessn:
            latest_sessn.delete()
            return redirect("/login/")
        else:
            return redirect('/feeds/')

# For validating the session
def check_validation(request):
    if request.COOKIES.get('session_token'):
        session = SessionToken.objects.filter(session_token=request.COOKIES.get('session_token')).first()
        if session:
            time_to_live = session.created_on + timedelta(days=1)
            if time_to_live > timezone.now():
                return session.user
    else:
        return None

def win_points(user, image_url, caption):
    brands_in_caption = 0
    brand_selected = ""
    points = 0;
    brands = BrandModel.objects.all()

    for brand in brands:
        if caption.__contains__(brand.name):
            brand_selected = brand.name
            brands_in_caption += 1
    image_caption = verify_image(image_url)
    if brands_in_caption == 1:
        points += 50
        if image_caption.__contains__(brand_selected):
            points += 50
    else:
        if image_caption != "":
            if BrandModel.objects.filter(name=image_caption):
                points += 50
    if points >= 50:
        brand = BrandModel.objects.filter(name=brand_selected).first()
        PointsModel.objects.create(user=user, brand=brand)
        return "Post Added with 1 points"
    else:
        return "Post Added"

def verify_image(image_url):
    app = ClarifaiApp(api_key="d9cdd283a5754aef87ed239a4b47b876")
    model = app.models.get("logo")
    responce = model.predict_by_url(url=image_url)
    if responce["status"]["code"] == 10000:
        if responce["outputs"][0]["data"]:
            return responce["outputs"][0]["data"]["regions"][0]["data"]["concepts"][0]["name"].lower()
    return ""

def points_view(request):
    user = check_validation(request)
    if user:

        points_model = PointsModel.objects.filter(user=user).order_by('-created_on')
        points_model.total_points = len(PointsModel.objects.filter(user=user))
        brands = BrandModel.objects.all()
        return render(request, 'points.html', {'points_model': points_model, 'brands': brands, 'user': user})
    else:
        return redirect('/login/')

def self_view(request):
    user = check_validation(request)
    if user:
        posts = PostModel.objects.filter(user=user).order_by('-created_on')
        for post in posts:
            existing_like = LikeModel.objects.filter(post_id=post.id, user=user).first()
            if existing_like:
                post.has_liked = True
        return render(request, 'feed.html', {'posts': posts, 'user': user})
    else:
        return redirect('/login/')
