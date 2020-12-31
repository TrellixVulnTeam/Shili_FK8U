from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
import json
# Create your views here.
from django.views import View

from home.models import ShiliEmail, MaHoaOneTimePad, Database
from post.models import Post
from user.models import MyUser


class Index(View):
    def get(self, request):
        if request.user.is_authenticated:
            database = Database(request.user.id)
            context = database.get_database_index()
            return render(request, 'home/home.html', context)
        else:
            return render(request, 'home/index.html')

    def post(self, request):
        if request.user.is_authenticated:
            # Đăng bài
            content = request.POST.get('content')
            hashtag = request.POST.get('hashtag').upper().replace(" ", "")
            feeling = request.POST.get('feeling')
            tag_friends = request.POST.get('tag_friends')
            public = request.POST.get('public')
            photo = ''
            try:
                photo = request.FILES['photo']
            except:
                pass
            new_post = Post()
            new_post.content = content
            new_post.photo = photo
            new_post.hashtag = hashtag
            new_post.feeling = feeling
            new_post.tag_friends = tag_friends
            new_post.public = public
            new_post.user = request.user
            new_post.save()
            messages = "Bạn vừa đăng thành công bài viết. Hãy tiếp tục sử  trải nghệm"

            context = {
                'messages': messages
            }
            return redirect('home:home')


class Login_user(View):
    def post(self, request):
        if request.method == 'POST':
            data = json.loads(request.body.decode('utf-8'))
            username = data['username']
            password = data['password']
            try:
                user = authenticate(username=MyUser.objects.get(email=username), password=password)
            except:
                user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return HttpResponse('success')
                else:
                    return HttpResponse(
                        'Tài khoản đã bị vô hiệu hóa vì chưa được xác thực. Hãy kiểm tra email để lấy link xác thực.')
            else:
                return HttpResponse('Tài khoản hoặc mật khẩu chưa chính xác. Vui lòng thử lại')


def logout_user(request):
    try:
        logout(request)
    except:
        pass
    return redirect('home:home')


class Register_user(View):
    def post(self, request):
        data = json.loads(request.body.decode('utf-8'))
        email = data['email']
        if not MyUser.objects.filter(email=email).exists():
            new_user = MyUser()
            new_user.first_name = data['firstname']
            new_user.last_name = data['lastname']
            new_user.username = data['username']
            new_user.email = data['email']
            new_user.set_password(data['password1'])
            new_user.birthday = data['birthday']
            new_user.gender = data['gender']
            new_user.is_active = 0
            new_user.save()
            new_user = MyUser.objects.filter(username=data['username'])
            if new_user:
                data = "Hello"
                one_time_pad = MaHoaOneTimePad()
                result = one_time_pad.ma_hoa(email)
                theme = ShiliEmail(result[0], result[1], email)
                msg_html = theme.xac_thuc()
                send_mail('Welcome to Shili!', data, "PLC", [email], html_message=msg_html, fail_silently=False)
                return HttpResponse('Đăng kí thành công tài khoản. Kiểm tra email để nhận liên kết kích hoạt tài khoản')
            else:
                return HttpResponse('Có lỗi xảy ra! Vui lòng thử lại')


class Send_pass(View):
    def post(self, request):
        data = json.loads(request.body.decode('utf-8'))
        email = data['email']
        one_time_pad = MaHoaOneTimePad()
        result = one_time_pad.ma_hoa(email)
        theme = ShiliEmail(result[0], result[1], email)
        msg_html = theme.reset_password()
        send_mail('Shili! Đặt lại mật khẩu', 'Hello', "PLC", [email], html_message=msg_html, fail_silently=False)
        return HttpResponse('Kiểm tra email để lấy liên kết đến trang thay đổi mật khẩu')


class Xacthuc(View):
    def get(self, request, key, ban_ma):
        one_time_pad = MaHoaOneTimePad()
        email = one_time_pad.giai_ma(key, ban_ma)
        context = {
            'email': email,
            'key': key,
            'ban_ma': ban_ma,
        }
        user = MyUser.objects.get(email=email)
        user.is_active = 1
        user.save()
        return render(request, 'mail/xacthuc.html', context)


class ResetPassword(View):
    def get(self, request, key, ban_ma):
        one_time_pad = MaHoaOneTimePad()
        email = one_time_pad.giai_ma(key, ban_ma)
        context = {
            'email': email,
            'key': key,
            'ban_ma': ban_ma,
        }
        return render(request, 'mail/reset_password.html', context)

    def post(self, request, key, ban_ma):
        one_time_pad = MaHoaOneTimePad()
        email = one_time_pad.giai_ma(key, ban_ma)
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        if password2 == password1:
            edit_user = MyUser.objects.get(email=email)
            edit_user.set_password(password1)
            edit_user.save()
        return redirect('home:home')


class Check(View):
    def post(self, request):
        data = json.loads(request.body.decode('utf-8'))
        username = data['username']
        email = data['email']
        try:
            MyUser.objects.get(username=username)
            return HttpResponse('trùng username')
        except:
            pass
        try:
            MyUser.objects.get(email=email)
            return HttpResponse('trùng email')
        except:
            pass
        return HttpResponse('')


class ApiGetContent(View):
    def post(self, request):
        if request.user.is_authenticated:
            sql_post_follow = "SELECT * FROM post_post a JOIN user_myuser b ON a.user_id =  b.id WHERE a.user_id IN(SELECT followres_id FROM user_follower WHERE main_user_id = " + str(
                request.user.id) + ") OR a.user_id = " + str(request.user.id) + "  ORDER BY a.created_at DESC"
            get_post_follow = Post.objects.raw(sql_post_follow)
            post_follow = []
            for i in get_post_follow:
                thisdict = {}
                thisdict["post_id"] = i.post
                thisdict["username"] = i.username
                thisdict["full_name"] = i.first_name + " " + i.last_name
                thisdict["feeling"] = i.feeling
                thisdict["avatar"] = str(i.avatar)
                thisdict["photo"] = str(i.photo)
                thisdict["created_at"] = i.created_at
                thisdict["public"] = i.public
                thisdict["content"] = i.content
                thisdict["hashtag"] = i.hashtag
                thisdict["user_id"] = i.user_id
                post_follow.append(thisdict)
            return JsonResponse({'result': post_follow})
        else:
            return redirect('home:home')
