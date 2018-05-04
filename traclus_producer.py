# @File  : traclus_producer.py
# @Author: 沈昌力
# @Date  : 2018/4/13
# @Desc  :
import pandas as pd
import click
# json消息上传到kafka
import json
from kafka import KafkaProducer

# producer = KafkaProducer(value_serializer=lambda v: json.dumps(v).encode('utf-8'))

@click.command()
@click.option(
    '--input-file', '-i',
    help='输入的航迹json文件，如果是cvs文件需要通过pre_process.py转为json文件再训练',
    required=True)
def main(input_file):
    get_raw_data(input_file)


producer = KafkaProducer(value_serializer=lambda v: json.dumps(v).encode('utf-8'))
def send2kafka(topic, msg):
    print(msg)
    msg['US'] = str(msg['US'])
    msg['BATCH'] = str(msg['BATCH'])
    # msg['LON'] = str(msg['LON'])
    # msg['LAT'] = str(msg['LAT'])

    producer.send(topic, msg)
    producer.flush()


def get_raw_data(inputfile):
    data = pd.read_csv(inputfile)
    data = data[data['V']!=-1]
    us = data['US']
    us = us.drop_duplicates()
    for u in us:
        u_data = data[data['US'] == u]
        rows = u_data.shape[0]
        for i in range(rows):
            dict_data = u_data.iloc[i].to_dict()
            send2kafka('test2', dict_data)

if __name__ == '__main__':
    main()