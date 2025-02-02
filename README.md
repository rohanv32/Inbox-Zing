# Inbox-Zing
# 📬 Inbox Zing - Full-Stack Application

Welcome to **Inbox Zing!** 🎉 This React-based application is designed to bring you the latest news and updates from various media outlets, all in one convenient place. Enjoy a sleek, intuitive interface with easy navigation options to set your preferences, customize your experience, and stay informed. Plus, earn points and level up as you read!


Follow the steps under the **Installation & Setup** Section below to run the application locally.


---

## 🚀 Features

- **🔒 Registration Page**: The entry point of the app provides options to **Sign Up** or **Login** to access your personalized news feed. Start by creating an account or logging into an existing one.

- **📰 News Feed**: Once logged in, you will be welcomed with a clean, card-based news feed with the latest articles. Each card contains:
  - Headline and source for quick identification.
  - A short snippet for a preview of the article.
  - Click on the article to learn more, and get a summarised version with the summary styles that you would prefer.
  - Earn points when you've completed reading your article, and redeem them for prizes(MYSK coffee!).

- **🔄 Preferences Setup**:
  - **Location and Language**: Tailor the content based on your **Country** and **Language** for a more localized news experience.
  - **Media Outlets Selection**: Choose from a range of popular media outlets (e.g., **Axios**, **Bloomberg**, **Reuters**, etc.) to filter the sources for your news feed.
  - **News Delivery Preferences**: Select your preferred **news update frequency** (e.g., every 12 hours) and **summary style** (e.g., brief or in-depth) to stay up-to-date in a way that suits your schedule.

- **🗑️ Account Management**:
  - **Delete Account**: If you wish to unsubscribe from the service, the app allows you to delete your account permanently.

- **Profile Page**
  - View your personal user preferences settings and statistics.

- **Account Deletion**
  - Easily delete your account if you no longer wish to use the service.

- **Podcast**
  - A Podcast feature, with your current news selection summarised in your preferred style for hand-free news updates!

- **Emails**
  - Get your news feed sent directly to your inbox, as and when you prefer.

- **🌐 Responsive Design**: Built to look great on desktop, tablet, and mobile devices for a seamless experience across any device.

---

## 📋 Prerequisites

Before you begin, make sure you have the following installed:

- **Node.js** (v14 or later) & **npm** (Node Package Manager)
  - [Download Node.js](https://nodejs.org/)
- Python 3.x
- [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) account for database setup
- [NewsAPI](https://newsapi.org) account to obtain an API key
- OpenAI API Key
- Groq API Key
- Sendgrid API Key
- An email account to send email from using Sendgrid
  
---

## 🛠️ Installation & Setup

To set up Inbox Zing locally, follow these steps:

### Frontend:

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/rohanv32/Inbox-Zing.git

2. **Navigate to the Frontend Directory**:
   ```bash
   cd frontend

3. **Configure Environment Variables**

   Create a .env File, make sure to replace username, password, and API keys with your actual credentials:

   ```bash
   REACT_APP_BACKEND_URL=http://localhost:8000
   PORT=3000
   REACT_APP_NEWS_API_KEY=your_news_api_key_here

5. **Install Dependencies**:
   ```bash
   npm install

### Backend:

1. **Navigate to the Backend Directory**
   
   ```bash
   cd backend

3. **Create a Virtual Environment**

   Creating a virtual environment helps keep your project dependencies isolated.

      ```bash
      python -m venv venv
      source venv/bin/activate  
      # On Windows use `venv\Scripts\activate`

4. **Install Dependencies**

   To install the required dependencies for the project, run:

      ```bash
      pip install -r requirements.txt

5. **Set Up MongoDB**

     Create a new cluster in MongoDB Atlas.
   
     Add a database user with read and write permissions.
   
     Whitelist your IP address for database access.
   
     Obtain your connection string from MongoDB Atlas and replace the placeholder in the code with your connection string.
   
6. **Configure Environment Variables**

   Create a .env File, make sure to replace username, password, and API keys with your actual credentials:
   
      ```bash
      REACT_APP_FRONTEND_URL=http://localhost:3000
      PORT=8000
      MONGO_URI=mongodb+srv://<username>:<password>@newcluster.hj9pw.mongodb.net/?retryWrites=true&w=majority&appName=NewCluster
      NEWS_API_KEY=your_news_api_key_here
      openai.api_key=your_openai_key_here
      REACT_APP_NEWS_API_KEY=your_news_api_key_here
      GROQ_API_KEY=your_groq_api_key_here
      SENDGRID_API_KEY=your_sendgrid_api_key_here
      SENDGRID_FROM_EMAIL=your_email_here

7. **Run the Backend Application**

     Once you have set up your virtual environment, installed dependencies, and configured MongoDB and NewsAPI, you can run the application's backend:

      ```bash
        python3 api.py
   
---

## ▶️ Running the Full Stack Application

After the setup is complete, you’re ready to launch Inbox Zing!

1. **Start the Development Server**:
   ```bash
   npm start
   ```
   This will launch the app on `http://localhost:3000`. Open this link in your browser to start using Inbox Zing.

---

## 🖼 Key Pages [Features]

### 1. Authentication Page
- **Sign Up** or **Login** to get started.

### 2. Preferences Setup
- Choose media outlets, country, and language to personalize your experience.
- Set your **news delivery frequency** and **summary style**.

### 3. News Feed
- A curated feed with the latest articles from selected sources.


### 4. Profile
- View user preferences settings and statistics.

### 5. Account Deletion
- Easily delete your account if you no longer wish to use the service.

### 6. Podcast
- Podcast for a hand-free news update!

---

## 📋 Notes to the User

- The podcast feature is dependent on the OpenAI API calls, so if you encounter any usage issues, please contact us and we will get it working as soon as we can.


## 📚 Usage Guide

1. **Sign Up / Login**: Sign up for a new account or log into an existing account to access the application.
2. **Customize Preferences**: Choose your preferred news sources, language, location, frequency of updates and summary style.
3. **View and Manage Feed**: Stay updated with the latest news in a format and frequency that suit your preferences.
4. **Profile**: Check current user preference setting and user reading statistics.
5. **Delete Account**: Remove your account anytime through the **Delete Account** page.
6. **Podcast**: Go to the podcast tab to generate a customized podcast.

---

## 🛠️ Tech Stack

- **Frontend**: ReactJS, JavaScript, HTML, CSS
- **Styling**: Styled-components / CSS Modules including SweetAlert2 for stylised alerts and Ant Design for Dark/Light Reading Mode
- **Backend**: Python, MongoDB, Pydantic, News API, Sendgrid API, OpenAI API

---

## 📌 Endpoints

| **Method** | **Endpoint**                    | **Description**                                                    |
|------------|---------------------------------|--------------------------------------------------------------------|
| POST       | `/signup`                       | To create a new user.                                              |
| POST       | `/verify_confirmation`          | To verify user by email.                                           |
| POST       | `/login`                        | To login user to send email updates.                               |
| PUT        | `/preferences/{username}`       | To modify user preferences.                                        |
| GET        | `/news/{username}`              | To fetch news articles according to user preferences.              |
| PATCH      | `/news/{username}/mark_as_read` | To mark news articles as read status.                              |
| GET        | `/news/{username}/statistics`   | To calculate user statistics.                                      |
| GET        | `/user/{username}`              | To get preferences for profile page display.                       |
| PUT        | `/user/{username}/password`     | To handle password update.                                         |
| DELETE     | `/user/{username}`              | To delete user and their stored data from the database.            |
| GET        | `/podcast/{username}`           | To retrieve podcast for the user.                                  |
| POST       | `/points/update`                | To update points earned by the user.                               |
| GET        | `/points/{username}`            | To fetch current points the user has.                              |
| GET        | `/news_sources`                 | To fetch and process news sources grouped by country and category. |
| GET        | `/streak/{username}`            | To get the user's reading streak statistic.                        |

---

## 🗃️ MongoDB Rationale

We chose **MongoDB** for this project due to the following reasons:
- **Schema Flexibility**: MongoDB allows for dynamic schemas, ideal for a news application where user preferences and articles can vary significantly.
- **Scalability**: It can handle large volumes of data efficiently, making it suitable for storing numerous articles fetched from various sources.
- **Performance**: MongoDB's document-oriented structure enables fast data retrieval, which is great for providing users with timely news updates.

Please take a look at InboxZingDatabase.pdf for the database architecture diagram.

---

## 📝 Design Decisions

- **React Components**: Each React component is modular and reusable, representing distinct UI parts (e.g., news card, preferences, authentication). This structure simplifies maintenance and scaling.
  
- **Card-Based News Feed**: A card layout enhances readability, allowing users to scan headlines and snippets, with clear options for dismissing articles.

- **Responsive Design**: Built using CSS media queries and Grid layouts, the app provides a seamless experience across devices.

- **User-based Customization**: Customizable preferences (e.g., update frequency, language, sources) make the app flexible and tailored to individual needs, boosting engagement.

## ⚙️ Technical Choices 

- **React**: Selected for its component-based structure, efficient rendering, and rich ecosystem, ideal for dynamic and interactive UIs.
  
- **Styled-Components**: Used for component-based styling, preventing style conflicts and aiding large-scale styling management for large apps and extensive features.

- **JavaScript**: Chosen for its popularity and seamless integration with React, allowing for a clean codebase compatible with modern tools and features.
  
---

## 🥳 Wireframe

Please navigate to the Figma link below for a prototype of the application.
**Link to Figma**: https://www.figma.com/design/bobVvvYCEht8CUIDfDtgos/InboxZing?node-id=0-1&t=1iDVuQ9jCMgNMdjh-1

Refer to 'InboxZing Figma Wireframe and Data Flow Diagram.pdf' for the latest Figma wireframes and Data Flow Chart.

---

## ➕ Additional Features

- **On-demand podcast voice cloning**
- **Personalised news consumption experience for user**
- **Localised features for university students to build community traction**
- **Short-form news and gamification for user engagement**
- **Language translation**

---

## 🤖 AI Usage

- **Code Suggestions and Debugging**: Leveraged AI to generate code snippets, troubleshoot issues, and suggest improvements, especially in CSS and component rendering logic.
- **Documentation Assistance**: AI was used to streamline the creation of project documentation and provide a structured approach to the README and component documentation.

---

## 📄 License
This project is licensed under the MIT license.
