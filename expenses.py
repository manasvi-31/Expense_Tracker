import pandas as pd
from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017')
db = client['expense_tracker']  # Replace 'your_database' with your actual database name
collection = db['expenses']  # Replace 'your_collection' with your actual collection name

# Retrieve data from MongoDB
cursor = collection.find({})  # You can add query filters here if needed

# Convert data to DataFrame
df = pd.DataFrame(list(cursor))

# Write DataFrame to CSV file
df.to_csv('mongodb_data.csv', index=False)  # 'mongodb_data.csv' is the output file name
 