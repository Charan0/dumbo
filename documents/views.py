from django.shortcuts import render, redirect
from .forms import UploadDocumentForm
import requests
from requests.auth import HTTPBasicAuth
from .models import Document
from . import utils
from django.contrib.auth.decorators import login_required
<<<<<<< HEAD
from django.views.generic.list import ListView
from django.db.models import Q
=======
from accounts.models import Profile
>>>>>>> main


# Create your views here.
def get_doc_tags(doc_name: str):
    # doc_name := documents/{name}.ext
    dtype = doc_name.split('.')[-1]
    # gs://dumbo-document-storage/documents/Dark.png
    bucket_name = 'dumbo-document-storage'
    uri = f'gs://{bucket_name}/{doc_name}'
    dest_uri = f'gs://{bucket_name}/tags/ReturnedTags'
    if dtype in ['jpg', 'jpeg', 'png']:
        tags = utils.get_tags(uri, dest_uri, 'image')
    else:
        tags = utils.get_tags(uri, dest_uri, 'document')
    return tags


@login_required(login_url='/user/login')
def my_documents(request):
    form = UploadDocumentForm()
    if request.method == 'POST':
        form = UploadDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            doc_object = form.save(commit=False)
            doc_object.owner = request.user
            doc_object.save()
            tags = get_doc_tags(doc_object.path.name)
            print(tags)
            if tags is not None:
                doc_object.tags.add(*tags)
                doc_object.save()
            return redirect('my_documents')
    context = {'form': form, 'documents': Document.objects.all()[:4],
               'public_documents': Document.objects.filter(is_public=True),
               'important_documents': Document.objects.filter(is_important=True),
               'common_tags': Document.tags.most_common()[:10],
               'profile': Profile.objects.get(user=request.user)}

    return render(request, 'documents/my_documents.html', context)


def to_format(file_path: str, name: str, format_: str = 'pdf'):
    api_key = '830dd544d855f1bb095949ecbd165a8f54b446b1'
    job_id = start_job(api_key, file_path, format_)
    target_file_id = conversion(api_key, job_id)
    download_file(api_key, target_file_id, name, format_)


def start_job(api_key: str, file_path: str, format_: str = 'pdf'):
    endpoint = "https://sandbox.zamzar.com/v1/jobs"
    target_format = format_

    file_content = {'source_file': open(file_path, 'rb')}
    data_content = {'target_format': target_format}
    r = requests.post(endpoint, data=data_content, files=file_content, auth=HTTPBasicAuth(api_key, ''))
    json_resp = r.json()
    job_id = json_resp['id']
    # source_file_id = json_resp['source_file']['id']
    return job_id


def conversion(api_key: str, job_id: int):
    endpoint = f'https://sandbox.zamzar.com/v1/jobs/{job_id}'
    while True:
        r = requests.get(endpoint, auth=HTTPBasicAuth(api_key, ''))
        json_resp = r.json()
        status = json_resp['status']
        if status == 'successful':
            target_files = json_resp['target_files']
            target_file_id = target_files[0]['id']
            return target_file_id
        else:
            continue


def download_file(api_key: str, target_file_id: int, name: str, format_: str = 'pdf'):
    local_filename = f'{name}.{format_}'
    endpoint = f'https://sandbox.zamzar.com/v1/files/{target_file_id}/content'

    response = requests.get(endpoint, stream=True, auth=HTTPBasicAuth(api_key, ''))

    try:
        with open(local_filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    f.flush()
            print('File Downloaded and Saved')
    except IOError:
        print('Error')


class SearchResultsView(ListView):
    model = Document
    template_name = 'documents/search_results.html'

    def get_queryset(self):
        query = self.request.GET.get('q')

        query = query.split(" ")  # making a list of all the tags

        condition = Q(tags__name__icontains=query[0])

        for string in query[1:]:
            condition |= Q(tags__name__icontains=string)  # the or condition for all the queried tags

        condition &= Q(owner=self.request.user)  # the and condition for the username

        object_list = Document.objects.filter(condition).distinct()

        # print(object_list)

        return object_list
