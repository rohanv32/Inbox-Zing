import React, { useState, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { UserContext } from './UserContext';
import Swal from 'sweetalert2';

function Login({ onLogin, onNavigateToSignUp }) {
  const [formData, setFormData] = useState({ username: '', password: '' });
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const { setPoints, setStreak } = useContext(UserContext);
  const navigate = useNavigate();

  const handleChange = (e) => setFormData({ ...formData, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    console.log("Form Data: ", formData);

    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });

      console.log("Response status:", response.status);
      console.log("Response ok:", response.ok);

      if (response.ok) {
        const data = await response.json();
        console.log("Login success response data:", data);
        Swal.fire({
          title: "Meow-velous to see you! 🐾",
          text: "Stay curious and catch today’s top stories! 🐱✨",
          imageUrl: "https://media.tenor.com/yasH25NcmgUAAAAM/cat-anime.gif",
          imageWidth: 400,
          imageHeight: 300,
        });
        await onLogin(formData);

        // Fetch the current points from the server
        const userPointsResponse = await fetch(`${process.env.REACT_APP_BACKEND_URL}/points/${formData.username}`);
        if (userPointsResponse.ok) {
          const userPointsData = await userPointsResponse.json();
          console.log("Fetched user points from server:", userPointsData);

          // Calculate the new points (add login gift points)
          const updatedPoints = userPointsData.points + 10;

          // Update points on the backend
          const pointsUpdateResponse = await fetch(`${process.env.REACT_APP_BACKEND_URL}/points/update?username=${formData.username}&points=10`, {
            method: 'POST',
          });
          if (pointsUpdateResponse.ok) {
            console.log(`10 points added for login. Updated total: ${updatedPoints}`);
            setPoints(updatedPoints); // Update points in context
          } else {
            console.error("Failed to update points on the server.");
          }
        } else {
          console.error("Failed to fetch user points from the server.");
        }

        try {
          const streakResponse = await fetch(`${process.env.REACT_APP_BACKEND_URL}/streak/${formData.username}`);
          if (streakResponse.ok) {
            const streakData = await streakResponse.json();
            console.log("Fetched streak data:", streakData);

            // Update streak in context
            setStreak(streakData.streak);
            console.log("New streak data:", streakData);
          } else {
            console.error("Failed to fetch streak data.");
          }

        } catch (streakErr) {
          console.error("An error occurred while fetching streak:", streakErr);
        }

        // Fetch news for the logged-in user
        /* try {
            const newsResponse = await fetch(`/news/${formData.username}`);
            if (newsResponse.ok) {
                const newsData = await newsResponse.json();
                console.log("Fetched news data:", newsData); // Log the fetched news data
            } else {
                console.error("Failed to fetch news articles.");
            }
        } catch (newsErr) {
            console.error("An error occurred while fetching news:", newsErr);
        } */
      } else {
        const error = await response.json();
        console.error("Login error response:", error);
        Swal.fire({
          icon: "error",
          title: "Oops! 🐾",
          text: error.message,
          footer: "Looks like a curious kitty got into the code! 😺 Try again with a different username or sign up."
        });
        
      }
    } catch (err) {
      console.error("An error occurred:", err);
      Swal.fire({
        title: "Uh-oh, the purr-blem is real! 🐾", err,
        text: "Something went wrong, please try again in a whisker moment..",
        imageUrl: "https://media1.tenor.com/m/fAKIFrYkfpAAAAAd/sad-sad-cat.gif",
        imageWidth: 400,
        imageHeight: 300,
      });
    }
  };

  const onForgotPassword = () => {
    setShowForgotPassword(true);
  };

  const handleBackToLogin = () => {
    setShowForgotPassword(false);
  };

  if (showForgotPassword) {
    return (
      <ForgotPassword
        email={formData.username}
        onEmailChange={(e) => setFormData({ ...formData, username: e.target.value })}
        onSubmit={() => Swal.fire({
          position: "top-end",
          icon: "success",
          title: "🎉 Pawsome! Verification email sent! 🐾",
          showConfirmButton: false,
          timer: 1500
        })}        
        notification={"Please check your email for further instructions."}
        onBack={handleBackToLogin}
      />
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full p-8">
        <h1 className="text-center text-3xl font-bold mb-6">
          THE INBOX ZING!
        </h1>

        <h2 className="text-center text-xl mb-6">
          Welcome back
        </h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <div className="mt-1">
              <input
                id="username"
                name="username"
                type="text"
                placeholder="Username"
                required
                onChange={handleChange}
                className="block w-full bg-gray-200 rounded-sm py-2 px-4 text-gray-900 placeholder-gray-900"
              />
            </div>
          </div>

          <div>
            <div className="mt-1">
              <input
                id="password"
                name="password"
                type="password"
                placeholder="Password"
                required
                onChange={handleChange}
                className="block w-full bg-gray-200 rounded-sm py-2 px-4 text-gray-900 placeholder-gray-900"
              />
            </div>
          </div>

          <div>
            <button
              type="submit"
              className="w-full flex justify-center rounded-sm bg-[#D5C3C6] py-2 px-4 text-black"
            >
              Login
            </button>
          </div>

          <div className="text-center">
            {/* <a
              href="#"
              onClick={(e) => { e.preventDefault(); onForgotPassword(); }}
              className="underline"
            >
              Forgot password?
            </a> */}
          </div>

          <div className="text-center">
            <span>Don't have an account? </span>
            <button
              type="button"
              onClick={() => navigate('/signup')}
              className="underline"
            >
              Sign up
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function ForgotPassword({ email, onEmailChange, onSubmit, notification, onBack }) {
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    setSubmitted(true);
    onSubmit();
  };

  return (
    <div className="flex min-h-screen items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full p-8">
        <h1 className="text-center text-3xl font-bold mb-6">Forgot Password</h1>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <input
              type="email"
              value={email}
              onChange={onEmailChange}
              placeholder="Enter your email"
              required
              className="block w-full bg-gray-200 rounded-sm py-2 px-4 text-gray-900 placeholder-gray-900"
            />
          </div>
          <div>
            <button
              type="submit"
              className="w-full flex justify-center rounded-sm bg-[#D5C3C6] py-2 px-4 text-black"
            >
              Send Verification Email
            </button>
          </div>
        </form>
        {submitted && notification && (
          <div className="text-center text-green-600 mt-4">
            {notification}
          </div>
        )}
        <div className="text-center mt-4">
          <button
            type="button"
            onClick={onBack}
            className="underline"
          >
            Back to Login
          </button>
        </div>
      </div>
    </div>
  );
}

export default Login;