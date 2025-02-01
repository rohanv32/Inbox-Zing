import hashlib
import requests
import os
from pymongo import MongoClient
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Cookie, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import List, Optional
from bson import ObjectId
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import certifi
import openai
import tempfile
from openai import OpenAI
from pydub import AudioSegment
from pydub.utils import which
from pydub.utils import mediainfo
import time
from groq import Groq
import asyncio
import re
import secrets
import gridfs
from io import BytesIO
from fastapi.responses import StreamingResponse

# Model used to Capture user sign up credentials.
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    points: int = 0
    last_login: Optional[datetime] = None
    confirmation_code: Optional[str] = None

# Model used to capture login credentials for logging in of an existing user
class UserLogin(BaseModel):
    username: str
    password: str

# Model that is used to Stores the user's news preferences
class UserPreferences(BaseModel):
    country: str
    category: str
    sources: str
    summaryStyle: str
    frequency: int

# Model used to capture the news articles that match user preferences
class NewsArticle(BaseModel):
    title: str
    source: str
    description: str
    url: str
    published_at: Optional[str]
    summary: str

class UserPreferencesResponse(BaseModel):
    username: str
    preferences: dict

class UpdatePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class VerifyConfirmationCodeRequest(BaseModel):
    email: str
    code: str

# loading the env variables and starting the fastapi
load_dotenv()
fast_app = FastAPI()

# connect to database (mongoDB)
MONGO_URI = os.getenv("MONGO_URI")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
openai.api_key = os.getenv("openai.api_key")

client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client['news_app']
users_collection = db['users']
news_articles_collection = db['news_articles']
fs = gridfs.GridFS(db)
grok_api_key = os.environ.get("GROQ_API_KEY")
grok_client = Groq(api_key=grok_api_key)

temp_users_collection = db['temp_users']

# uniqueness of email and username maintained
users_collection.create_index([("email", 1)], unique=True)
users_collection.create_index([("username", 1)], unique=True)
NEWS_API_URL = "https://newsapi.org/v2/top-headlines"

# Password hashing function
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# Helper function to check the password hash
def verify_password(stored_password: str, provided_password: str) -> bool:
    return stored_password == hash_password(provided_password)

def fetch_news(preferences: UserPreferences) -> List[dict]:
    articles = []
    page = 1  # Start fetching from the first page
    while len(articles) < 10:  # Keep fetching until we have 10 articles
        params = {
            'apiKey': NEWS_API_KEY,
            'sources': preferences.sources,  # Use the sources parameter
            'pageSize': 10,  # Fetch 10 articles per request
            'page': page  # Fetch the next page
        }
        response = requests.get(NEWS_API_URL, params=params)
        
        if response.status_code == 200:
            new_articles = response.json().get('articles', [])
            
            # Filter articles to ensure they have complete data
            for article in new_articles:
                if all(key in article and article[key] for key in ['title', 'description', 'urlToImage', 'content']):
                    articles.append(article)
                
                # Stop if we already have 10 complete articles
                if len(articles) >= 10:
                    break
        page += 1  # Move to the next page
        # If no new articles were fetched, break the loop to prevent an infinite loop
        if not new_articles:
            break
    return articles[:10]

def summarize_article(article: dict, summary_style: str) -> str:
    content = article.get("content") or article.get("title") or "No content or title available."
    if summary_style == "Brief":
        prompt = f"Summarize this article briefly, keeping it insightful, yet concise. Please go straight into the summary, do not repeat the prompt in any way.: {content}"
    elif summary_style == "Detailed":
        prompt = f"Summarize this article in detail, but keep it interesting and thought-provoking. Please go straight into the summary, do not repeat the prompt in any way.: {content}"
    elif summary_style == "ELI5":
        prompt = f"Explain the key points of this article like I'm five years old, in a concise, yet interesting manner. Please go straight into the summary, do not repeat the prompt in any way.: {content}"
    elif summary_style == "Humorous":
        prompt = f"Summarize this article in a humorous way, to aid the user in understanding and taking away the most from the daily news through humor. Please go straight into the summary, do not repeat the prompt in any way.: {content}"
    elif summary_style == "Storytelling":
        prompt = f"Turn this article into a storytelling format, that keeps the user engrossed and helps them come away learning new things. Please go straight into the summary, do not repeat the prompt in any way.: {content}"
    elif summary_style == "Poetic":
        prompt = f"Turn this article into a poetic recitation, that is intriguing, yet informative: {content}"
    else:
        prompt = f"Provide a generic summary of this article: {content}"
    chat_completion = grok_client.chat.completions.create(
        messages=[
            {"role": "user", "content": prompt}
        ],
        model="llama3-8b-8192",
    )
    response = chat_completion.choices[0].message.content.strip()
    def clean_summary(summary: str, style: str) -> str:
        
        patterns = [
            r"^Here(('|’)s| is) a summary of the article.*?:",
            r"^Summarize(d|s|ing|ion).*?:",
            r"^Explain(ed|ing|s).*?:",
            r"^This article is about.*?:",
            r"^Turn(ed|ing|s) into.*?:",
        ]
        combined_pattern = re.compile("|".join(patterns), re.IGNORECASE)
        return re.sub(combined_pattern, "", summary).strip()
    cleaned_response = clean_summary(response, summary_style)
    return cleaned_response
        
def send_news_summary_email(user_email: str, username: str, articles: List[dict], summary_style: str):
    # Get SendGrid API Key from environment
    sendgrid_api_key = os.getenv('SENDGRID_API_KEY')
    sendgrid_email=os.getenv('SENDGRID_FROM_EMAIL')
    
    # Prepare email content
    email_body = f"Hi {username},\n\nHere's your news summary:\n\n"
    
    for article in articles:
        email_body += f"Title: {article['title']}\n"
        email_body += f"Summary: {article.get('summary', 'No summary available')}\n\n"
    
    email_body += "Stay informed!\n"
    # Create email message
    message = Mail(
        from_email=sendgrid_email,  # Must be a verified sender in SendGrid
        to_emails=user_email,
        subject=f'{username}, Your News Summary',
        html_content=f'<pre>{email_body}</pre>'
    )
    try:
        # Send email using SendGrid
        sg = SendGridAPIClient(sendgrid_api_key)
        response = sg.send(message)
        print(f"Email sent to {user_email}. Status Code: {response.status_code}")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
    
# All endpoints are added below
@fast_app.get("/status")
async def get_status(username: str = Cookie(None)):
    if username:
        # If a username cookie is present, it means the user is logged in
        return {"isLoggedIn": True, "username": username}
    else:
        # If no cookie, the user is not logged in
        return {"isLoggedIn": False, "username": None}
    
def send_confirmation_email(user_email: str, confirmation_code: str):
    # Get SendGrid API Key from environment
    sendgrid_api_key = os.getenv('SENDGRID_API_KEY')
    sendgrid_email = os.getenv('SENDGRID_FROM_EMAIL')

    # Prepare email content
    email_body = f"Hi,\n\nYour confirmation code is: {confirmation_code}\n\nPlease use this code to confirm your account.\n\nStay informed!"

    # Create email message
    message = Mail(
        from_email=sendgrid_email,  # Must be a verified sender in SendGrid
        to_emails=user_email,
        subject='Confirm Your Account',
        html_content=f'<pre>{email_body}</pre>'
    )

    try:
        # Send email using SendGrid
        sg = SendGridAPIClient(sendgrid_api_key)
        response = sg.send(message)
        print(f"Email sent to {user_email}. Status Code: {response.status_code}")
        
        # Updating the temporary user document with the new confirmation code, if multiple
        temp_users_collection.update_one(
            {"email": user_email},
            {"$set": {"confirmation_code": confirmation_code}}
        )

        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def export_newsfeed_as_html(articles):
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Inbox Zing - News Feed</title>
        <style>
            /* Your existing styles */
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">Your Personalized News Feed</div>
            {"".join(
                f'''
                <div class="article">
                    <h2>{article['title']}</h2>
                    <img src="{article.get('urlToImage', '')}" alt="{article['title']}"/>
                    <p>{article['summary']}</p>
                    <a href="{article['url']}" target="_blank">Read More</a>
                </div>
                ''' for article in articles
            )}
        </div>
    </body>
    </html>
    """
    return html_content





def send_newsfeed_html_email(user_email: str, username: str, html_content: str):
    # Get SendGrid API Key from environment
    sendgrid_api_key = os.getenv('SENDGRID_API_KEY')
    sendgrid_email = os.getenv('SENDGRID_FROM_EMAIL')

    # Create email with HTML content
    message = Mail(
        from_email=sendgrid_email,
        to_emails=user_email,
        subject=f'{username}, Your Personalized News Feed',
        html_content=html_content
    )

    try:
        # Send the email
        sg = SendGridAPIClient(sendgrid_api_key)
        response = sg.send(message)
        print(f"Email sent to {user_email}. Status Code: {response.status_code}")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

@fast_app.post("/signup")
async def signup(user: UserCreate):
    # Hash the user's password for security
    hashed_password = hash_password(user.password)

    # Check if the email already exists in registered users
    existing_user = users_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered. Please log in, or sign up with a new Email")

    # Check if the username already exists
    existing_user = users_collection.find_one({"username": user.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    # Create the user document
    new_user = {
        "username": user.username,
        "email": user.email,
        "password": hashed_password,
        "created_at": datetime.now(),
        "points": 0,
        "streak": 0,
        "last_login": None
    }

    # Try to insert the new user into the database
    try:
        users_collection.insert_one(new_user)
        return {"message": "Signup successful!"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error during signup: {str(e)}")



""" @fast_app.post("/signup")
async def signup(user: UserCreate):
    # Hash the user's password for security
    hashed_password = hash_password(user.password)
# Couple of checks to make sure there are no duplicate users

     # Check if the email already exists in registered users
    existing_user = users_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered. Please log in, or sign up with a new Email")

    # Check if the username already exists
    existing_user = users_collection.find_one({"username": user.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
        

    # Generate a confirmation code
    confirmation_code = secrets.token_hex(6)  

    # Create the temporary user document
    temp_user = {
        "username": user.username,
        "email": user.email,
        "password": hashed_password,
        "created_at": datetime.now(),
        "points": 0,
        "streak": 0,
        "last_login": None,
        "confirmation_code": confirmation_code
    }

    # Try to insert the temporary user into the database
    try:
        temp_users_collection.insert_one(temp_user)

        send_confirmation_email(user.email, confirmation_code)

        return {"message": "Signup initiated! Please check your email to confirm your account!"}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error initiating signup: {str(e)}")


@fast_app.post("/verify_confirmation")
async def verify_confirmation(request: VerifyConfirmationCodeRequest):
    temp_user = temp_users_collection.find_one({"email": request.email})
    if not temp_user:
        raise HTTPException(status_code=404, detail="User not found")

    if temp_user["confirmation_code"] == request.code:
        # Create the new user document
        new_user = {
            "username": temp_user["username"],
            "email": temp_user["email"],
            "password": temp_user["password"],
            "created_at": temp_user["created_at"],
            "points": temp_user["points"],
            "streak": temp_user["streak"],
            "last_login": temp_user["last_login"],
        }

        # Try to insert the new user into the database
        try:
            users_collection.insert_one(new_user)
            temp_users_collection.delete_one({"email": request.email})
            return {"message": "Account confirmed successfully"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error confirming account: {str(e)}")
    else:
        raise HTTPException(status_code=400, detail="Invalid confirmation code") """
    
# # Endpoint to handle logging in a user
# @fast_app.post("/login")
# async def login(user: UserLogin):
#     db_user = users_collection.find_one({"username": user.username})
#     if db_user and db_user["password"] == hash_password(user.password):
#       # if username and password match user in db, login is successful
#         print("Backend login successful for:", user.username)
#         now = datetime.now()
#         last_login = db_user.get("last_login")
#         streak = db_user.get("streak", 0)
#         if last_login:
#             last_login_date = last_login.date()
#             if now.date() == last_login_date + timedelta(days=1):
#                 streak += 1  # Increment streak for consecutive days
#             elif now.date() > last_login_date + timedelta(days=1):
#                 streak = 0  # Reset streak for missed days
#         # Update last_login and streak
#         users_collection.update_one(
#             {"username": user.username},
#             {"$set": {"last_login": now, "streak": streak}}
#         )
#         return JSONResponse(content={"message": "Login successful", "username": user.username})
#         # if error display this message
#     raise HTTPException(status_code=401, detail="Invalid username or password")
@fast_app.post("/login")
async def login(user: UserLogin):
    db_user = users_collection.find_one({"username": user.username})
    if db_user and db_user["password"] == hash_password(user.password):
        print("Backend login successful for:", user.username)
        now = datetime.now()
        last_login = db_user.get("last_login")
        streak = db_user.get("streak", 0)
        # Check if preferences exist and frequency is set
        if "preferences" in db_user and "frequency" in db_user["preferences"]:
            # Check if it's time to send an email
            last_email_sent = db_user.get("last_email_sent")
            frequency_hours = db_user["preferences"]["frequency"]
            # If no last email sent or time since last email exceeds frequency
            if not last_email_sent or (now - last_email_sent).total_seconds() / 3600 >= frequency_hours:
                # Fetch news articles
                try:
                    # Use the existing get_news function to fetch articles
                    news_response = await get_news(user.username)
                    articles = news_response.get("articles", [])
                    # Send email if articles exist
                    if articles:
                        summarized_articles = []
                        for article in articles:
                            summary = article.get('summary', 'No summary available')
                            source_name = article.get('source', 'Unknown Source')
                            summarized_articles.append({
                                "title": article['title'],
                                "source": source_name,
                                "description": article['description'],
                                "url": article['url'],
                                "published_at": article.get('publishedAt'),
                                "urlToImage": article.get('urlToImage'),
                                "summary": summary,
                                "isRead": False
                            })
                         # Export news feed as HTML
                        html_content = export_newsfeed_as_html(summarized_articles)
                        # Send the HTML email
                        email_sent = send_newsfeed_html_email(
                            user_email=db_user["email"],
                            username=user.username,
                            html_content=html_content
                        )
                        # Update last email sent time if email was sent successfully
                        if email_sent:
                            users_collection.update_one(
                                {"username": user.username},
                                {"$set": {"last_email_sent": now}}
                            )
                except Exception as e:
                    print(f"Error processing news for email: {e}")
        if last_login:
            last_login_date = last_login.date()
            if now.date() == last_login_date + timedelta(days=1):
                streak += 1  
            elif now.date() > last_login_date + timedelta(days=1):
                streak = 0 
        # Update last_login and streak
        users_collection.update_one(
            {"username": user.username},
            {"$set": {"last_login": now, "streak": streak}}
        )
        return JSONResponse(content={"message": "Login successful", "username": user.username})
    
    raise HTTPException(status_code=401, detail="Invalid username or password")

# Endpoint to handle modifying of previously set user preferences
@fast_app.put("/preferences/{username}")
async def update_preferences(username: str, preferences: UserPreferences):
    print(f"Attempting to update preferences for username: {username}")
  # Update the user's preferences in the database accordingly
    result = users_collection.update_one(
        {"username": username},
        {"$set": {"preferences": preferences.dict()}}
    )
    # error handling if prefs are updated successfully
    # if error, user not found displayed
    print(f"Update result: {result.modified_count}")
    if result.modified_count:
        # Construct the path to the audio file
        audio_dir = os.path.join("src", "audio")
        final_audio_file = os.path.join(audio_dir, f"{username}_final_podcast_audio.wav")
        # Check if the audio file exists and delete it if it does
        if os.path.exists(final_audio_file):
            os.remove(final_audio_file)
            print(f"Deleted existing audio file: {final_audio_file}")
        return {"message": "Preferences updated successfully"}
    raise HTTPException(status_code=404, detail="User not found")
    
@fast_app.get("/news/{username}")
async def get_news(username: str):
    user = users_collection.find_one({"username": username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    preferences = user.get("preferences")
    if not preferences:
        raise HTTPException(status_code=400, detail="User preferences not set")
    user_news_doc = news_articles_collection.find_one({"username": username})
    # Check if the preferences have changed (e.g., compare the stored preferences with the current ones)
    if user_news_doc and user_news_doc['preferences'] == preferences:
        if datetime.now() - user_news_doc['fetched_at'] < timedelta(hours=preferences['frequency']):
            # Return the stored articles if they are recent enough
            articles = user_news_doc['articles']
        else:
            # Fetch new articles if the frequency has passed
            fetched_articles = fetch_news(UserPreferences(**preferences))
            articles = []
            for article in fetched_articles:
                summary = summarize_article(article, preferences['summaryStyle'])
                articles.append({
                    "title": article['title'],
                    "source": article['source']['name'],
                    "description": article['description'],
                    "url": article['url'],
                    "published_at": article.get('publishedAt'),
                    "urlToImage": article.get('urlToImage'),
                    "summary": summary,
                    "isRead": False 
                })
            # Update the user's document with the new articles
            news_articles_collection.update_one(
                {"username": username},
                {
                    "$set": {
                        "username": username,
                        "fetched_at": datetime.now(),
                        "preferences": preferences,
                        "articles": articles
                    }
                },
                upsert=True
            )
    else:
        # If preferences have changed, fetch new articles regardless of frequency
        fetched_articles = fetch_news(UserPreferences(**preferences))
        articles = []
        for article in fetched_articles:
            summary = summarize_article(article, preferences['summaryStyle'])
            articles.append({
                "title": article['title'],
                "source": article['source']['name'],
                "description": article['description'],
                "url": article['url'],
                "published_at": article.get('publishedAt'),
                "urlToImage": article.get('urlToImage'),
                "summary": summary,
                "isRead": False
            })
        # Update the user's document with the new articles and preferences
        news_articles_collection.update_one(
            {"username": username},
            {
                "$set": {
                    "username": username,
                    "fetched_at": datetime.now(),
                    "preferences": preferences,
                    "articles": articles
                }
            },
            upsert=True
        )
    return {"articles": articles}

@fast_app.patch("/news/{username}/mark_as_read")
async def mark_article_as_read(username: str, article_url: str, readingTime: int = 0):
    # Find the user
    user = users_collection.find_one({"username": username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Find the user's news document
    user_news_doc = news_articles_collection.find_one({"username": username})
    if not user_news_doc:
        raise HTTPException(status_code=404, detail="No news data found for this user")
    # Update the "isRead" state for the specific article
    updated_articles = []
    for article in user_news_doc["articles"]:
        if article["url"] == article_url:
            article["isRead"] = True  # Mark as read
            article["readingTime"] = readingTime
        updated_articles.append(article)
    
    # Update the document with the new "isRead" state
    news_articles_collection.update_one(
        {"username": username},
        {
            "$set": {
                "articles": updated_articles
            }
        }
    )
    return {"message": "Article marked as read", "url": article_url}

@fast_app.get("/news/{username}/statistics")
async def get_news_statistics(username: str):
    user = users_collection.find_one({"username": username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Fetch the user's news data
    user_news_doc = news_articles_collection.find_one({"username": username})
    if not user_news_doc:
        raise HTTPException(status_code=404, detail="No news data found for this user")
    
    # Calculate statistics
    total_articles = len(user_news_doc["articles"])
    read_articles = sum(1 for article in user_news_doc["articles"] if article["isRead"])
    unread_articles = total_articles - read_articles
    
    # Calculate total time spent (assuming each article has a 'timeSpent' field in seconds)
    total_time_spent = sum(article.get("readingTime", 0) for article in user_news_doc["articles"])
    return {
        "articlesRead": read_articles,
        "articlesLeft": unread_articles,
        "readingTime": total_time_spent,
    }

# Endpoint to get preferences for the Profile Page display
@fast_app.get("/user/{username}", response_model=UserPreferencesResponse)
async def get_user_preferences(username: str):
    user = users_collection.find_one({"username": username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"username": user["username"], "preferences": user.get("preferences", {})}

# Endpoint to handle password update
@fast_app.put("/user/{username}/password")
async def update_user_password(username: str, request: UpdatePasswordRequest):
    # Fetch user from the database
    user = users_collection.find_one({"username": username})
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Verify current password
    if not verify_password(user['password'], request.current_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    # Hash new password
    hashed_password = hash_password(request.new_password)
    # Update the password in the database
    result = users_collection.update_one(
        {"username": username},
        {"$set": {"password": hashed_password}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Password unchanged")
    
    return {"message": "Password updated successfully"}

# Endpoint to get all news articles stored in the database
@fast_app.get("/news_articles/")
async def get_news_articles():
    articles = list(news_articles_collection.find())
    # for mongoDB : Change the news ObjectIds to string same as endpoint 4
    for article in articles:
        article["_id"] = str(article["_id"])
    return articles

# Endpoint to delete a user from the database with their stored data
@fast_app.delete("/user/{username}")
async def delete_user(username: str):
    # if user is found in db, delete from the database
    result = users_collection.delete_one({"username": username})
    if result.deleted_count:
      # delete the news articles as well
        news_articles_collection.delete_many({"username": username})
        podcasts = db.podcasts.find({"username": username})
        for podcast in podcasts:
            file_id = podcast.get("audio_file_id")
            if file_id:
                # Remove the associated audio file from GridFS
                fs.delete(file_id)
                print(f"Deleted audio file with file_id: {file_id}")
        
        # Delete the podcast records from the podcasts collection
        db.podcasts.delete_many({"username": username})
        
        return {"message": f"User {username} and articles associated with the account are deleted"}
    # error handling part when the user is not found
    raise HTTPException(status_code=404, detail="User not found")

async def generate_podcast_script(articles, summary_style, username):
    if not isinstance(articles, list) or not articles:
        print("No articles or invalid structure provided.")
        raise HTTPException(status_code=500, detail="No articles found or invalid article structure.")
    
    try:
        news_content = ""
        for idx, article in enumerate(articles, 1):
            title = article.get('title', 'No Title')
            description = article.get('description', 'No Description Available')
            source = article.get('source', 'Unknown Source') 
            news_content += f"{idx}. Title: {title}\nSource: {source}\nSummary: {description}\n\n"
        prompt = (
            f"You are a creative assistant skilled in writing engaging and entertaining podcast scripts. "
            f"Below is a collection of summarized news articles. Create a seamless and personalized 2-minute podcast script for a user named {username}, based on these articles. "
            f"Tailor the script to the summary style specified ({summary_style}) and focus on making it conversational, lively, and relatable.\n\n"
            f"Begin with a warm, energetic introduction that includes sound effects or a musical cue (e.g., '🎵 [Music fades in] Good morning, {username}! Welcome to your personalized news podcast!'). "
            f"Show personality, like a friendly host talking directly to {username}.\n\n"
            f"For each article:\n"
            f"{news_content}" 
            f"- Summarize it concisely, mentioning the title, key points, and the source. Provide insights, context, or interesting interpretations beyond just reading the title and description. "
            f"- Add rhetorical questions (e.g., 'Can you believe it?' or 'What do you think about this?') to engage {username}.\n"
            f"- Incorporate humor, light commentary, or thought-provoking remarks to make the podcast engaging.\n"
            f"- Ensure that humor used in summaries of serious topics, such as those related to death or accidents, remains sensitive and respectful. Strive to make it engaging and lighthearted without being insensitive or inappropriate.\n"
            f"- Transition smoothly between stories.\n\n"
            f"Conclude with an upbeat outro, thanking {username} and urging them to stay curious and motivated.\n"
            f" A motivational call-to-action for NYUAD students: 'Stay informed, keep earning points, and remember—once you hit 500 points, you’re just one free coffee from MYSC away!'.\n"
            f" End on an uplifting note, urging {username} to stay curious and motivated.\n"
            f"Ensure the podcast fits within 2 minutes (~300 words), sounds like it’s delivered by a charismatic and lively host."
        )
        # OpenAI API call using the updated syntax
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo", 
            messages=[
                {"role": "system", "content": "You are a helpful assistant writing podcast scripts."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        podcast_text = response.choices[0].message.content.strip()
        #print("Generated Podcast Script:", podcast_text)
        return podcast_text
    except Exception as e:
        print("Error during podcast script generation:", e)
        raise HTTPException(status_code=500, detail="An error occurred while generating the podcast script.")
    
async def generate_podcast_audio(script):
    try:
        
        # OpenAI API for text-to-speech (TTS)
        response = openai.audio.speech.create(
            model="tts-1",
            voice="alloy", 
            input=script
        )
        print("TTS Response:", response)
        
        audio_data = response.content

        return audio_data
    
    except Exception as e:
        print("Error during TTS conversion:", e)
        raise HTTPException(status_code=500, detail="An error occurred while converting text to speech.")

# Storing audio directly into GridFS
async def store_audio_to_gridfs(audio_data, username):
    try:
        print(f"Storing audio of size: {len(audio_data)} bytes")
        filename = f"{username}_podcast_audio.mp3"

        file_id = fs.put(audio_data, filename=filename)
        print(f"Stored audio with file_id: {file_id}") 

        return file_id
    except Exception as e:
        print("Error storing audio to GridFS:", e)
        raise HTTPException(status_code=500, detail="An error occurred while storing audio to GridFS.")
    

@fast_app.get("/podcast/{username}")
async def create_podcast(username: str):
    try:
        # Checking if the podcast exists by username and articles
        user = users_collection.find_one({"username": username})
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")

        # Checking for the user's existing podcast
        user_news = news_articles_collection.find_one({"username": username})
        if not user_news or not user_news.get("articles"):
            raise HTTPException(status_code=404, detail="No articles found for this user.")
        
        # Checking if the podcast with the same articles exists
        articles = user_news["articles"]
        existing_podcast = db.podcasts.find_one({"username": username})

        if existing_podcast:
            existing_articles = existing_podcast.get("articles", [])

            if articles != existing_articles:
                print("Not the same articles.")

                file_id = existing_podcast.get("audio_file_id")
                if file_id:
                    print("The files were found.")
                    fs.delete(file_id)
                    print(f"Deleted audio file with file_id: {file_id}")

                db.podcasts.delete_many({"username": username})
                print(f"Deleted existing podcast record for username: {username}")

            else:
                
                file_id = existing_podcast["audio_file_id"]
                print(f"Found existing podcast with file_id: {file_id}")
                audio_file = fs.get(file_id)
                return StreamingResponse(BytesIO(audio_file.read()), media_type="audio/mpeg")

        # Generating a new podcast if no match is found
        preferences = user.get("preferences", {})
        summary_style = preferences.get("summaryStyle", "brief")
        podcast_script = await generate_podcast_script(articles, summary_style, username)

        audio_data = await generate_podcast_audio(podcast_script)

        # Storing the podcast audio to GridFS
        file_id = await store_audio_to_gridfs(audio_data, username)
        print(f"Generated new file_id: {file_id}")  

        db.podcasts.insert_one({
            "username": username,
            "articles": articles,
            "audio_file_id": file_id,
            "created_at": time.time()
        })

        return JSONResponse(content={"audio_url": f"/audio/{str(file_id)}"})
    except HTTPException as e:
        print(f"Error in podcast endpoint: {e.detail}")
        return JSONResponse(content={"error": e.detail}, status_code=e.status_code)
    except Exception as e:
        print("Unexpected error in podcast endpoint:", e)
        return JSONResponse(content={"error": "An unexpected error occurred."}, status_code=500)

@fast_app.get("/audio/{file_id}")
async def get_audio(file_id: str):
    try:
        
        object_id = ObjectId(file_id)  
        print(f"Fetching audio with ObjectId: {object_id}") 

        file = fs.get(object_id)  
        print(f"Found file in GridFS with ObjectId: {object_id}")  

        audio_content = file.read() 
        print(f"Audio file size: {len(audio_content)} bytes")  

        return StreamingResponse(BytesIO(audio_content), media_type="audio/mpeg")
    except Exception as e:
        print("Error fetching audio from GridFS:", e)
        raise HTTPException(status_code=404, detail="Audio file not found.")
    
# The points update endpoint
@fast_app.post("/points/update")
async def update_user_points(username: str, points: int):
    user = users_collection.find_one({"username": username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    # Update user points in the database
    new_points = user["points"] + points
    users_collection.update_one(
        {"username": username},
        {"$set": {"points": new_points}}
    )
    return {"message": f"Points updated. New total: {new_points}"}

# New endpoint to fetch current points
@fast_app.get("/points/{username}")
async def get_user_points(username: str):
    user = users_collection.find_one({"username": username}, {"_id": 0, "points": 1})
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return {"username": username, "points": user["points"]}


@fast_app.get("/news_sources")
async def fetch_news_sources():
    """
    Fetch and process news sources grouped by country and category.
    """
    if not NEWS_API_KEY:
        raise HTTPException(status_code=500, detail="API key is not configured.")

    try:
        response = requests.get(
            f"https://newsapi.org/v2/top-headlines/sources?apiKey={NEWS_API_KEY}"
        )
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)
        sources_data = response.json().get("sources", [])

        # Process data into a nested structure: country -> category -> sources
        country_data = {}
        for source in sources_data:
            country = source.get("country")
            category = source.get("category")
            source_id = source.get("id")
            source_name = source.get("name")

            if not country or not category or not source_id or not source_name:
                continue

            if country not in country_data:
                country_data[country] = {}
            if category not in country_data[country]:
                country_data[country][category] = []

            country_data[country][category].append({"id": source_id, "name": source_name})

        return {
            "countries": list(country_data.keys()),
            "data": country_data,
        }
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch data: {str(e)}")

@fast_app.get("/streak/{username}")
async def get_streak(username: str):
    user = users_collection.find_one({"username": username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"streak": user.get("streak", 0)}

REACT_APP_FRONTEND_URL = os.getenv("REACT_APP_FRONTEND_URL", "http://localhost:3000")  # default to localhost if not set
PORT = int(os.getenv("PORT", 8000))
fast_app.add_middleware(
    CORSMiddleware,
    allow_origins=[REACT_APP_FRONTEND_URL],  # Adjust if your frontend is hosted elsewhere
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(fast_app, host="0.0.0.0", port=PORT)