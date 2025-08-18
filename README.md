# Personalized-Book-Tracker-and-Recommender

Welcome to **SmartReads** - a personalized book tracking and recommendation system built using AWS cloud services and an interactive Streamlit frontend. This project helps users track their reading journey and get personalized recommendations based on their history, authors and genres.

## 🚀 Project Overview

- Designed as a serverless, event-driven application
- Built on AWS DynamoDB, Lambda, S3, SNS, IAM and CloudWatch
- Provides personalized book recommendations using scoring logic
- Sends automated welcome emails to newly registered users
- Offers an easy-to-use Streamlit web interface

## 📂 Project Structure

- config/
   - `aws_config.py`: AWS configuration & credentials

- dashboard/
   - `dashboard_cli.py`: CLI-based dashboard utilities
   - `report_generator.py`: Report generation logic

- data/
    - `book_dataset.csv`: Book dataset (raw)
   - `book_dataset.json`: Preprocessed dataset (for S3)
   - `goodreads_data.csv`: Source dataset
   - `convert.py`: Conversion utilities
   - `preprocess.py`: Dataset preprocessing

- db_module/
   - `dynamo_handler.py`: DynamoDB operations (CRUD)
   - `schema_setup.py`: Table schema creation

- reading_tracker/
    - `tracker.py`: Tracks user reading activity

- `app.py`: Streamlit frontend app
- `requirements.txt`: Dependencies
- `LICENSE`
- `readme.txt` 

## 🛠️ Getting Started

You can try SmartReads instantly using our hosted Streamlit app:  
👉 [https://smart-reads.streamlit.app/](https://smart-reads.streamlit.app/)

## 🌐 Website

- Frontend: Streamlit  
- Backend: AWS Lambda, DynamoDB, S3, SNS  
- Monitoring: AWS CloudWatch

## 🧠 Model Overview

Our system leverages two intelligent Lambda functions to deliver a personalized user journey:

### 🤖 Book Recommendation Engine  
- Loads book dataset from S3 and caches it for quick access  
- Uses unified scoring logic:
  - +5 for favorite authors  
  - +2 for matching genres  
  - Excludes books already read  
- Ensures author diversity in suggestions  
- Fallback to globally popular books if needed  
- Updates user profile in DynamoDB with Top 5 recommendations  

### 🔔 Welcome Notification
- Triggered by:  
  - New user registration (DynamoDB Stream)  
  - SNS subscription confirmations  
  - Scheduled EventBridge polls  
- Subscribes users to SNS Topic via email  
- Sends a personalized welcome email with user details  
- Marks users in DynamoDB with `welcome_sent = True`  
- Fault-tolerant with retry support via polling  

Together, these ensure users are welcomed instantly and receive fresh, intelligent book recommendations in real time.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
