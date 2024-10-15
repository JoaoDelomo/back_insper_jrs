from pymongo import MongoClient

def get_db():
    client = MongoClient('mongodb+srv://admin:admin@delomo.zxqnf.mongodb.net/')
    db = client['JRs']
    return db
