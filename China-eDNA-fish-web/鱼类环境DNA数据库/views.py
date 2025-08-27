from django.shortcuts import render
from django.http import HttpResponse  # 引入HTTP响应类
from .models import 物种名, all_12S_info
from django.core.files.storage import FileSystemStorage
import os
import logging
from Bio.Blast import NCBIWWW, NCBIXML
from io import StringIO
from Bio import Entrez
import subprocess
from django.http import JsonResponse
from django.shortcuts import render, redirect

Entrez.email = "1226107791@qq.com"

# 设置日志
logging.basicConfig(level=logging.DEBUG)


# views.py
from django.shortcuts import render
from .models import all_12S_info
import os

def search_species(request):
    query = request.GET.get('q')
    if query:
        latin_results = all_12S_info.objects.filter(Species__icontains=query)
        chinese_results = all_12S_info.objects.filter(cn_Species__icontains=query)
        results = (latin_results | chinese_results).distinct()
    else:
        results = all_12S_info.objects.none()

    for result in results:
        if result.fasta_12S:
            # 获取文件路径列表
            file_paths_str = result.fasta_12S.name  # 获取文件名
            file_paths = file_paths_str.split(',')  # 假设文件名是以逗号分隔的多个文件路径
            fasta_contents = []
            for file_path in file_paths:
                file_path = file_path.strip()  # 移除前后空格
                full_file_path = os.path.join(result.fasta_12S.storage.location, file_path)
                with open(full_file_path, 'r') as file:
                    first_line = file.readline()
                    if first_line.startswith('>ENA|'):
                        data_sources="fasta 数据来源：ENA\n"
                    else:
                        data_sources="fasta 数据来源：NCBI\n"
                    fasta_contents.append(first_line)
                    fasta_contents.append(file.read())
                    fasta_contents.append(data_sources)
            result.fasta_content = '\n'.join(fasta_contents)  # 将所有文件内容合并为一个字符串
            #print(f"Fasta contents for {result.Species}: {result.fasta_content}")
    print(f"Search query: {query}")
    print(f"Latin results: {latin_results}")
    print(f"Chinese results: {chinese_results}")
    print(f"Combined results: {results}")
    return render(request, 'search_results.html', {'results': results})

def 首页(request):
    query = request.GET.get('q', '')
    results = []
    if query:
        results = all_12S_info.objects.filter(Species__icontains=query)  # 假设你按名称搜索
    return render(request, '首页.html', {'query': query, 'results': results})

from .models import *  # 引入全部模型类
from math import ceil  # 引入向上取整函数

def 搜索视图(request):
    query = request.GET.get('q', '')
    results = []
    if query:
        results = all_12S_info.objects.filter(Species__icontains=query)  # 假设你按名称搜索
    return render(request, '搜索.html', {'query': query, 'results': results})

from django.views.generic.list import ListView

class 列表视图(ListView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['物种名列表'] = all_12S_info.objects.order_by('?')[:12]
        #context['目标基因列表'] = 目标基因.objects.order_by('?')[:12]
        return context

class 首页视图(列表视图):
    model = 物种名
    template_name = '首页.html'
    ordering = 'id'
    paginate_by = 10

from django.views.generic import TemplateView

class HomeView(TemplateView):
    template_name = '搜索.html'

def handle_uploaded_file(request, f):
    fs = FileSystemStorage(location=r'C:\资料\广东工业大学\鱼类数据库\fishdb_download\baseinfo\12S\DNA\\')
    filename = fs.save(f.name, f)
    uploaded_file_url = fs.url(filename)
    return os.path.join(fs.location, filename)

def handle_sequence_input(sequence):
    temp_file_path = r'C:\资料\广东工业大学\鱼类数据库\fishdb_download\baseinfo\12S\DNA\temp_sequence.fasta'
    with open(temp_file_path, 'w') as temp_file:
        temp_file.write(sequence)
    return temp_file_path

def blast_search(request):
    results = []
    error_message = None
    #读取文件Invasive_species.txt
    Invasive_species = open(
        r'C:\资料\广东工业大学\鱼类数据库\鱼类环境DNA数据库\鱼类环境DNA数据库网站\media\Invasive_species.txt', 'r',
        encoding='utf-8')
    Invasive_species_list = []
    Invasive_species_dic = {}
    # 将文件中第二三列读取到列表中，并且去除null
    for line in Invasive_species:
        line = line.strip()
        if line:
            species, species_name = line.split('\t')
            # species_name为key为species_name，value为species的字典
            Invasive_species_dic[species_name] = species
            Invasive_species_list.append(species_name)
    if request.method == 'POST':
        query_file = request.FILES.get('query_file')
        sequence = request.POST.get('sequence')
        expect = request.POST.get('expect', 10)  # 默认值为10
        perc_ident = request.POST.get('perc_ident', 98)  # 默认值为98
        hitlist_size = request.POST.get('hitlist_size', 50)  # 默认值为50

        if query_file:
            query_file_path = handle_uploaded_file(request, query_file)
        elif sequence:
            query_file_path = handle_sequence_input(sequence)
        else:
            error_message = "No file or sequence provided."
            return render(request, 'blast_search.html', {'results': results, 'error_message': error_message})

        try:
            # 使用 Biopython 运行 BLAST
            result_handle = NCBIWWW.qblast(
                program="blastn",
                database="nt",
                sequence=open(query_file_path).read(),
                expect=float(expect),
                perc_ident=int(perc_ident),
                hitlist_size=int(hitlist_size),
            )

            # 解析 BLAST 输出
            blast_record = NCBIXML.read(result_handle)
            for alignment in blast_record.alignments:
                for hsp in alignment.hsps:
                    # 获取gi号
                    gi = alignment.hit_id.split('|')[1]
                    # 获取gi对应的taxonomy信息
                    gi = Entrez.efetch(db='nucleotide', id=gi, rettype='gb', retmode='xml')
                    all_info = Entrez.read(gi)
                    Species = all_info[0]['GBSeq_organism']
                    taxonomy = all_info[0]['GBSeq_taxonomy']
                    fastqid = all_info[0]['GBSeq_accession-version']
                    description = all_info[0]['GBSeq_definition']
                    #line_title = fastqid + '\n' + description
                    # 分割分类学信息，每个元素是一个分类学等级
                    taxonomy_ranks = taxonomy.split('; ')
                    # 初始化一个字典来存储分类学信息
                    taxonomy_info = {
                        'Class': None,
                        'Order': None,
                        'Family': None,
                        'Genus': None,
                        'Species': None
                    }
                    # 根据 taxonomy_ranks 的长度来安全地获取分类学信息
                    if len(taxonomy_ranks) > 6:
                        taxonomy_info['Class'] = taxonomy_ranks[6]
                    if len(taxonomy_ranks) > 10:
                        taxonomy_info['Order'] = taxonomy_ranks[10]
                    if len(taxonomy_ranks) > 11:
                        taxonomy_info['Family'] = taxonomy_ranks[11]
                    if len(taxonomy_ranks) > 13:
                        taxonomy_info['Genus'] = taxonomy_ranks[13]
                    taxonomy_info['Species'] = Species
                    Invasivetag = ""
                    if Species in Invasive_species_list:
                        Invasivetag="外来入侵物种："+Invasive_species_dic[Species]
                    else:
                        Invasivetag=""
                    line_title = fastqid + '\n' + description + '\n' +Invasivetag
                    # 打印提取的分类学信息
                    print("Class:", taxonomy_info['Class'])
                    print("Order:", taxonomy_info['Order'])
                    print("Family:", taxonomy_info['Family'])
                    print("Genus:", taxonomy_info['Genus'])
                    print("Species:", taxonomy_info['Species'])

                    results.append({
                        'qseqid': line_title,
                        'pident': hsp.identities / hsp.align_length * 100,
                        'length': hsp.align_length,
                        'mismatch': hsp.align_length - hsp.identities,
                        'gapopen': hsp.gaps,
                        'evalue': hsp.expect,
                        'bitscore': hsp.score,
                        'Class': taxonomy_info['Class'],
                        'Order': taxonomy_info['Order'],
                        'Family': taxonomy_info['Family'],
                        'Genus': taxonomy_info['Genus'],
                        'Species': taxonomy_info['Species'],
                        'subject_sequence': hsp.sbjct
                    })

            result_handle.close()
        except Exception as e:
            error_message = f"Error: {e}"

        if query_file:
            fs = FileSystemStorage(location=r'C:\资料\广东工业大学\鱼类数据库\fishdb_download\baseinfo\12S\DNA\\')
            fs.delete(query_file.name)

    return render(request, 'blast_search.html', {'results': results, 'error_message': error_message})
import subprocess
from django.http import JsonResponse

def run_vsearch(request):
    if request.method == 'POST':
        try:
            # 假设从前端获取到输入文件路径、输出文件路径等参数
            input_file = request.POST.get('input_file')
            output_file = request.POST.get('output_file')
            sintax_db = request.POST.get('sintax_db', 'all_12S.fa')  # 默认的SINTAX数据库路径
            sintax_cutoff = float(request.POST.get('sintax_cutoff', 0.7))  # 默认的SINTAX cutoff值
            threads = int(request.POST.get('threads', 4))  # 默认线程数

            # 定义宿主机路径和容器内部路径
            host_path = r"C:\资料\广东工业大学\eDNA课题组\shana"
            container_path = "/data"

            # 构建 VSEARCH 的 Docker 命令
            command = [
                "docker", "run", "--rm",
                "-v", f"{host_path}:{container_path}",  # 挂载卷
                "quay.io/biocontainers/vsearch:2.30.0--hd6d6fdc_0",
                "vsearch", f"--threads={threads}",
                f"--sintax={container_path}/{input_file}",
                f"--db={container_path}/12S/{sintax_db}", f"--sintax_cutoff={sintax_cutoff}",
                f"--tabbedout={container_path}/{output_file}"
            ]

            # 执行命令，并指定编码为utf-8
            result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')

            if result.returncode == 0:
                return JsonResponse({'status': 'success', 'message': result.stdout})
            else:
                return JsonResponse({'status': 'error', 'message': result.stderr})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


from django.http import JsonResponse
import subprocess

def run_split_fastq(request):
    # 你的视图逻辑
    if request.method == 'POST':
        # 处理 POST 请求
        return JsonResponse({'status': 'success', 'message': '处理成功'})
    else:
        return JsonResponse({'status': 'error', 'message': '无效的请求方法'})
