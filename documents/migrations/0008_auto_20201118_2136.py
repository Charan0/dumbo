# Generated by Django 3.1.2 on 2020-11-18 16:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0007_thumbs'),
    ]

    operations = [
        migrations.AlterField(
            model_name='thumbs',
            name='image',
            field=models.ImageField(default='https://storage.googleapis.com/dumbo-document-storage/thumbnails/documents/default.png', upload_to='thumbnails/'),
        ),
    ]