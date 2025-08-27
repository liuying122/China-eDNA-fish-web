from django.db import models
from django.urls import reverse
from tinymce.models import HTMLField
import os

class 物种名(models.Model):
    种名拉丁语 = models.CharField(max_length=200, primary_key=True)
    种曾用名拉丁语 = models.CharField(max_length=200, blank=True)
    种名中文 = models.CharField(max_length=20, blank=True)
    种曾用名中文 = models.CharField(max_length=20, blank=True)

def get_upload_path(instance, filename):
    return f"{instance.种名拉丁语.种名拉丁语.replace(' ', '_')}/{filename}"
class all_12S_info(models.Model):
    cn_Species = models.CharField(max_length=20, blank=True)
    Sub_cn_Species = models.CharField(max_length=20, blank=True)
    cn_Order = models.CharField(max_length=20, blank=True)
    Sub_cn_Order = models.CharField(max_length=20, blank=True)
    cn_Family = models.CharField(max_length=20, blank=True)
    Sub_cn_Family = models.CharField(max_length=20, blank=True)
    cn_Genus = models.CharField(max_length=20, blank=True)
    Sub_cn_Genus = models.CharField(max_length=20, blank=True)
    cn_Species = models.CharField(max_length=20, blank=True)
    Sub_cn_Species = models.CharField(max_length=20, blank=True)
    Class = models.CharField(max_length=200, blank=True)
    cn_Class = models.CharField(max_length=200, blank=True)
    Subclass = models.CharField(max_length=200, blank=True)
    Order = models.CharField(max_length=200, blank=True)
    Suborder = models.CharField(max_length=200, blank=True)
    Family = models.CharField(max_length=200, blank=True)
    Subfamily = models.CharField(max_length=200, blank=True)
    Genus = models.CharField(max_length=200, blank=True)
    Subgenus = models.CharField(max_length=200, blank=True)
    Species = models.CharField(max_length=200, blank=True,primary_key=True)
    Subspecies = models.CharField(max_length=200, blank=True)
    IUCN = models.CharField(max_length=20, blank=True)
    Endemic = models.CharField(max_length=20, blank=True)
    description = models.TextField(max_length=5000, blank=True)
    distribution = models.TextField(max_length=100, blank=True)
    fishbase_web = models.URLField(blank=True, null=True)
    fasta_12S = models.FileField(upload_to='fasta_files/')  # 假设这里存储的是以逗号分隔的多个文件路径

    # 如果你需要更复杂的逻辑，可以添加一个方法
    def get_fasta_files(self):
        return self.fasta_12S.split(',')

    def read_fasta_contents(self):
        contents = []
        for file_path in self.get_fasta_files():
            file_path = file_path.strip()
            full_file_path = os.path.join(self.fasta_12S.storage.location, file_path)
            with open(full_file_path, 'r') as file:
                contents.append(file.read())
        return '\n'.join(contents)

    def __str__(self):
        return self.Species
