import os
import sys
import django

# 将项目根目录添加到 sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# 设置 Django 环境变量
os.environ.setdefault('DJANGO_SETTINGS_MODULE', '鱼类环境DNA数据库.settings')

# 初始化 Django 应用
django.setup()

import csv
from 鱼类环境DNA数据库.models import all_12S_info


def import_data_from_csv(file_path):
    with open(file_path, mode='r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        records = []
        for row in reader:
            record = all_12S_info(
                cn_Species=row['cn_Species'],
                cn_Order=row['cn_Order'],
                cn_Family=row['cn_Family'],
                Class=row['Class'],
                Order=row['Order'],
                Family=row['Family'],
                Genus=row['Genus'],
                Species=row['Species'],
                IUCN=row['IUCN'],
                Endemic=row['Endemic'],
                description=row['description'],
                distribution=row['distribution'],
                fishbase_web=row['fishbase_web'],
                fasta_12S=row['fasta_12S']
            )
            records.append(record)
        print(records)
        # 批量插入数据
        all_12S_info.objects.bulk_create(records)

if __name__ == "__main__":
    import_data_from_csv(r'C:\资料\广东工业大学\鱼类数据库\fishdb_download\中国淡水鱼.csv')
