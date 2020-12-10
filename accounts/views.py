from django.shortcuts import render, redirect
from .admin import DumboUserCreationForm
from .forms import DumboUserLoginForm, UserUpdateForm, ProfileUpdateForm
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.core.mail import EmailMessage
from .tokens import account_activation_token
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.shortcuts import render
from django.http import HttpResponse
from .models import DumboUser, Profile
from django.utils.encoding import force_bytes, force_text
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .decorators import redirect_user
from documents.models import Document


# Create your views here.
@redirect_user
def register(request):  # This view is used to register new users into the application
    if request.method == 'POST':
        form = DumboUserCreationForm(request.POST)  # The form used for saving/creating the new users
        if form.is_valid():
            # We save the object temporarily and not commit
            user = form.save(commit=False)
            # We activate a user account after email confirmation
            user.is_active = False
            user.save()
            current_site = get_current_site(request)
            mail_subject = 'Activate your Dumbo account.'
            message = render_to_string('accounts/acc_active_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            })
            to_email = form.cleaned_data.get('email')
            email = EmailMessage(
                mail_subject, message, to=[to_email]
            )
            # Email for account verification sent
            email.send()
            return render(request, 'accounts/email_confirm_request.html')
    else:
        form = DumboUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})


@redirect_user
def login_view(request):
    if request.method == 'POST':
        form = DumboUserLoginForm(request.POST)  # The form used to authenticate our users
        if form.is_valid():
            user_object = form.cleaned_data.get('user_object')
            print(f'Login successful for {user_object}')
            # Users can be authenticated into the site either by using
            # their email and username since for a user both are unique
            # and can be used to identified the user
            login(request, user_object, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('my_documents')
    else:
        form = DumboUserLoginForm()
    return render(request, 'accounts/login.html', {'form': form})


# View for activation link
def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = DumboUser.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, DumboUser.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        # Verified the user, thus made active
        user.is_active = True
        user.save()
        # Logged in
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        return render(request, 'accounts/email_confirm.html')
    else:
        return HttpResponse('Activation link is invalid!')


def profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST,
                                   request.FILES,
                                   instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, f'Your account has been updated!')
            return redirect('profile')

    else:
        u_form = UserUpdateForm()
        p_form = ProfileUpdateForm()

    user_profile = Profile.objects.get(user=request.user)

    user_profile.in_trash = len(Document.objects.filter(owner=request.user, in_trash=True))
    user_profile.total_docs = len(Document.objects.filter(owner=request.user))
    user_profile.public_docs = len(Document.objects.filter(owner=request.user, is_public=True))
    user_profile.important_docs = len(Document.objects.filter(owner=request.user, is_important=True))

    user_profile.save()
    context = {
        'u_form': u_form,
        'p_form': p_form,
        'profile': user_profile,
        'form': PasswordChangeForm(user=request.user),
        'remaining_space': round((user_profile.total_space - user_profile.used_space) * 1e-9, 2),
        'total_space': user_profile.total_space * 1e-9,
        'data_value': 100 - ((user_profile.total_space - user_profile.used_space) / user_profile.total_space) * 100
    }

    return render(request, 'accounts/profile.html', context)


@login_required(login_url='/user/login')
def user_change_pass(request):
    if request.method == "POST":
        fm = PasswordChangeForm(user=request.user, data=request.POST)
        if fm.is_valid():
            fm.save()
            return redirect("/user/login")
        else:
            messages.warning(request, f'an error occurred try again')
    return redirect('profile')
