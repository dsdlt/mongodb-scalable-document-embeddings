from sentence_transformers import SentenceTransformer
from typing import List
from confluent_kafka import Producer, Consumer
import json 
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import pprint
import random
import string
import concurrent.futures
import argparse
from texttagging import texttagging



def read_ccloud_config(config_file):
    conf = {}
    with open(config_file) as fh:
        for line in fh:
            line = line.strip()
            if len(line) != 0 and line[0] != "#":
                parameter, value = line.strip().split('=', 1)
                conf[parameter] = value.strip()
    return conf


def generate_embedding_tag(id, text, producer, model, nlp, output_topic, input_topic):
    
    #Generate embeddings
    embeddings = model.encode(text, convert_to_tensor=True)
    #Generate tags
    tags_array = texttagging.extract_tags(text, nlp)
    event = {'lyrics': text, 'tags': tags_array, '_id': id }
    if(input_topic == 'SpanishInputTopic'):
        event['lyrics_embeddings_es'] = embeddings.tolist()
    else:
        event['lyrics_embeddings_en'] = embeddings.tolist()
    producer.produce(output_topic, value=json.dumps(event))
    producer.flush()
    return True

def process_documents(input_topic, output_topic, executor, model, nlp):

    #Configure producer and consumer
    producer = Producer(read_ccloud_config("client.properties"))
    props = read_ccloud_config("client.properties")
    props["group.id"] = "python-group-1"
    props["auto.offset.reset"] = "earliest"
    consumer = Consumer(props)
    
    #Subscribe to the input topic
    consumer.subscribe(input_topic)
    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is not None and msg.error() is None:
                jsonDocument = json.loads(msg.value())
                lyrics=jsonDocument['fullDocument']['lyrics']
                id=jsonDocument['fullDocument']['_id']

                #Create a new thread to process the embeddings and tags for each event received
                executor.submit(generate_embedding_tag, id, lyrics, producer, model, nlp, output_topic, input_topic[0])
    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()
        producer.close()

def main():
    parser = argparse.ArgumentParser(description='Metadata Service')
    parser.add_argument('-l', '--language', type=str, required=True, help="Language specific Kafka Topic [english, spanish]")
    
    args = parser.parse_args()
    language = args.language

    #Configuring topics and models
    if(language == "spanish"):
        #https://www.sbert.net/docs/pretrained_models.html
        #model = SentenceTransformer('sentence-transformers/distiluse-base-multilingual-cased-v1')
        model = SentenceTransformer('mrm8488/distiluse-base-multilingual-cased-v2-finetuned-stsb_multi_mt-es')
        input_topic = "SpanishInputTopic"
        nlp = texttagging.init_library('es_core_news_sm')
    else:
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        input_topic = "EnglishInputTopic"
        nlp = texttagging.init_library('en_core_web_sm')

    output_topic = "OutputTopic"
    max_workers=10
    print('Input topic used: ' + input_topic)
    print('Output topic used: ' + output_topic)
    print('Number of concurrent threads: ' + str(max_workers))
    
    #Multi-threading to utilise all the CPUs of the host
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)

    #Start processing events from the topics
    process_documents([input_topic], output_topic, executor, model, nlp)

main()