# 作者：刘英 (12261077991@qq.com)
# 创建日期：
# 版本：1.0.0
# 描述：
from celery import shared_task
from .models import BlastTask
from Bio.Blast import NCBIWWW, NCBIXML
from io import StringIO
from Bio import Entrez
import os
import logging

# 设置你的邮箱，这是NCBI的要求
Entrez.email = "1226107791@qq.com"

# 设置日志
logging.basicConfig(level=logging.DEBUG)


@shared_task
def run_blast_search(task_id, query_file_path):
    task_record = BlastTask.objects.get(task_id=task_id)

    try:
        # 使用 Biopython 运行 BLAST
        with open(query_file_path, 'r') as query_file:
            result_handle = NCBIWWW.qblast("blastn", "nt", query_file.read())

        # 解析 BLAST 输出
        blast_record = NCBIXML.read(result_handle)
        results = []
        for alignment in blast_record.alignments:
            for hsp in alignment.hsps:
                # 获取gi号
                gi = alignment.hit_id.split('|')[1]
                # 获取gi对应的taxonomy信息
                gi = Entrez.efetch(db='nucleotide', id=gi, rettype='gb', retmode='xml')
                all_info = Entrez.read(gi)
                print(all_info)
                Species = all_info[0]['GBSeq_organism']
                taxonomy = all_info[0]['GBSeq_taxonomy']
                fastqid = all_info[0]['GBSeq_accession-version']
                description = all_info[0]['GBSeq_definition']
                line_title = fastqid + '\n' + description
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
                taxonomy_info['Class'] = taxonomy_ranks[6]
                taxonomy_info['Order'] = taxonomy_ranks[10]
                taxonomy_info['Family'] = taxonomy_ranks[11]
                taxonomy_info['Genus'] = taxonomy_ranks[13]
                taxonomy_info['Species'] = Species
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

        task_record.results = results
        task_record.status = 'completed'
        task_record.save()
    except Exception as e:
        task_record.status = 'error'
        task_record.save()
        logging.error(f"Error during BLAST search: {e}")
