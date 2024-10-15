from pymongo import MongoClient
import os


def get_db():
    mongo_user = os.getenv('MONGO_USER')
    mongo_password = os.getenv('MONGO_PASSWORD')
    connection_string = f"mongodb+srv://{mongo_user}:{mongo_password}@delomo.zxqnf.mongodb.net/?authSource=admin&retryWrites=true&w=majority"
    
    client = MongoClient(connection_string)
    db = client['Jrs']  
    return db
