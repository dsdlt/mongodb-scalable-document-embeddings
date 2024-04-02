import pymongo
import argparse
from getpass import getpass
from sentence_transformers import SentenceTransformer

def main():
    parser = argparse.ArgumentParser(description='A simple chatbot in Python')
    parser.add_argument('-u', '--username', type=str, required=True, help="MongoDB Username")
    parser.add_argument('-p', '--password', type=str, help='MongoDB Password')
    parser.add_argument('-H', '--hostname', type=str, required=True, help="Hostname")
    
    args = parser.parse_args()
    # Use getpass for password to hide it from command line history and other users 
    #pwd = getpass(prompt="Enter MongoDB Password: ") if not args.password else args.password
    pwd = "passwordthree"

    client = pymongo.MongoClient('mongodb+srv://{}:{}@{}/'.format(args.username, pwd, args.hostname)) 
    db = client["streamingvectors"]
    collection = db["lyrics"]

    print("## CONNECTED TO MongoDB Atlas ##")
    while(True):
        language = input("What is the language of the song? [es, en] - ")
        if(language == "es"):
            model = SentenceTransformer('mrm8488/distiluse-base-multilingual-cased-v2-finetuned-stsb_multi_mt-es')
            index_name = "lyrics_embeddings_es"
        else:
            model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
            index_name = "lyrics_embeddings_en"
        
        vectorsearch = input("What do you want the song to talk about? - ")
        embeddings = model.encode(vectorsearch, convert_to_tensor=True)
        vector = embeddings.tolist()

        pipeline = [
            {
                "$vectorSearch": {
                    "index": index_name,
                    "path": index_name,
                    "queryVector": vector,
                    "numCandidates": 10,
                    "limit": 3
                }
            },
            {
                '$project': {
                    'artist': 1, 
                    'title': 1, 
                    'year': 1, 
                    'genre': 1, 
                    'tags': 1, 
                    'lyrics' : {'$substr' : ['$lyrics', 0, 50]},
                    'score': {
                        '$meta': 'vectorSearchScore'
                    }
                }
            }
        ]
        # Execute the aggregation
        results = collection.aggregate(pipeline)

        # Print the results
        print('==============')
        for result in results:
            print(result)
            print('==============')
  
main()