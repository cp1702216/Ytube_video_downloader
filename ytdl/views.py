from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
# Create your views here.
from django.http import HttpResponse
from django.shortcuts import render
import youtube_dl
from .forms import DownloadForm
import re
from . models import Account
from django.contrib import messages, auth


def download_video(request):
    global context
    form = DownloadForm(request.POST or None)
    
    if form.is_valid():
        video_url = form.cleaned_data.get("url")
        regex = r'^(http(s)?:\/\/)?((w){3}.)?youtu(be|.be)?(\.com)?\/.+'
        #regex = (r"^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?$\n")
        print(video_url)
        if not re.match(regex,video_url):
            print('nhi hoa')
            return HttpResponse('Enter correct url.')

        # if 'm.' in video_url:
        #     video_url = video_url.replace(u'm.', u'')

        # elif 'youtu.be' in video_url:
        #     video_id = video_url.split('/')[-1]
        #     video_url = 'https://www.youtube.com/watch?v=' + video_id

        # if len(video_url.split("=")[-1]) < 11:
        #     return HttpResponse('Enter correct url.')

        ydl_opts = {}

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            meta = ydl.extract_info(
                video_url, download=False)
        video_audio_streams = []
        for m in meta['formats']:
            file_size = m['filesize']
            if file_size is not None:
                file_size = f'{round(int(file_size) / 1000000,2)} mb'

            resolution = 'Audio'
            if m['height'] is not None:
                resolution = f"{m['height']}x{m['width']}"
            video_audio_streams.append({
                'resolution': resolution,
                'extension': m['ext'],
                'file_size': file_size,
                'video_url': m['url']
            })
        video_audio_streams = video_audio_streams[::-1]
        context = {
            'form': form,
            'title': meta['title'], 'streams': video_audio_streams,
            'description': meta['description'], 'likes': meta['like_count'],
            'dislikes': meta['dislike_count'], 'thumb': meta['thumbnails'][3]['url'],
            'duration': round(int(meta['duration'])/60, 2), 'views': f'{int(meta["view_count"]):,}'
        }
        return render(request, 'home.html', context)
    return render(request, 'home.html', {'form': form})

@csrf_exempt
def login(request):
    if request.method=="POST":
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = auth.authenticate(email=email, password=password)

        if user is not None:
            auth.login(request, user)
            return redirect('download_video')

    return render(request, 'login.html')

@csrf_exempt
def signup(request):
    if request.method=="POST":
        first_name = request.POST.get('fname')
        last_name = request.POST.get('lname')
        email = request.POST.get('email')
        password = request.POST.get('password')
        cpassword = request.POST.get('confirm_password')

        username = email.split('@')[0]
        user = Account.objects.create_user(username=username, email=email, password=password, first_name=first_name, last_name=last_name)
        user.save()
        from trycourier import Courier

        client = Courier(auth_token="pk_prod_FF56H95JBA47FTH53DAJNKH3B7BF")

        resp = client.send_message(
        message={
            "to": {
            "email": user.email,
            },
            "template": "GA7P1M6S0NM28RJKQR6VSFSJCRS9",
            "data": {
            "user": user.username,
            },
        }
        )
        
        print(first_name, last_name, email, password, username)
        return redirect('download_video')

    return render(request, 'signup.html')