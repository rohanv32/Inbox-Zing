// required imports made

import React, { createContext, useState, useContext, useEffect } from 'react';
import Swal from 'sweetalert2';

export const defaultPreferences = {
  country: 'us',
  category: 'general',
  sources: 'cnn,abc-news',
  summaryStyle: 'Brief', 
  frequency: 24,
};

// User context intiated
export const UserContext = createContext();

// UserProvider component to provide the user state to the app
export function UserProvider({ children }) {
  // User state
  const [username, setUsername] = useState('');
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [preferences, setPreferences] = useState(defaultPreferences);

  const [points, setPoints] = useState(() => {
    const savedPoints = localStorage.getItem('points');
    return savedPoints ? parseInt(savedPoints, 10) : 0;
  });
  const [streak, setStreak] = useState(0);
  const [milestone, setMilestone] = useState(false);
  const [doublePoints, setDoublePoints] = useState(false);

  // Log when username or login status changes
  useEffect(() => {
    console.log('Username updated in context:', username);
  }, [username]);

  useEffect(() => {
    const storedUsername = localStorage.getItem('username');
    if (storedUsername) {
      setUsername(storedUsername);
    }
  }, []);
  
  useEffect(() => {
    // username kept syncing with local storage
    if (username) {
      localStorage.setItem('username', username);
    }
  }, [username]);

  useEffect(() => {
    if (points > 0) {
      localStorage.setItem('points', points);
    }
  }, [points]);

  useEffect(() => {
    console.log('Login status changed:', isLoggedIn);
  }, [isLoggedIn]);

  // double points on weekends feature
  useEffect(() => {
    const day = new Date().getDay();
    setDoublePoints(day === 6 || day === 0); 
  }, []);

  // Earning points handeler
  const earnPoints = () => {
    let earnedPoints = 10; // Base points and then incremeneted

    // Apply streak bonus: +10% per day in a streak, max 50%
    if (streak > 0) {
      earnedPoints += Math.min(streak, 5) * 0.1 * earnedPoints;
    }

    // double points feature
    if (doublePoints) {
      earnedPoints *= 2;
    }

    setPoints((prev) => prev + earnedPoints);
    setStreak((prev) => prev + 1);

    // check if reached milestones for rewards
    if (!milestone && points + earnedPoints >= 100) {
      setMilestone(true);
      Swal.fire({
        title: "Congrats! You reached 100 points!",
        width: 600,
        padding: "3em",
        color: "#716add",
        background: "#fff url(/images/trees.png)",
        backdrop: `
          rgba(0,0,123,0.4)
          url("/images/nyan-cat.gif")
          left top
          no-repeat
        `
      });
    }
  };

  // streak is reset every 24 hours so can recount
  useEffect(() => {
    const resetStreak = () => setStreak(0);
    const timer = setInterval(resetStreak, 24 * 60 * 60 * 1000);
    return () => clearInterval(timer);
  }, []);

  // Return the context provider with relevant values
  return (
    <UserContext.Provider value={{ username, setUsername, isLoggedIn, setIsLoggedIn, preferences, setPreferences, points,
      streak,
      milestone,
      doublePoints,
      earnPoints,
      setPoints, 
      setStreak}}>
      {children}
    </UserContext.Provider>
  );
}

export const useUserContext = () => useContext(UserContext);

// hook to access username and login state
export const useUsername = () => {
  const { username } = useUserContext();
  return username;
};

export const useIsLoggedIn = () => {
  const { isLoggedIn } = useUserContext();
  return isLoggedIn;
};

// Convenience hook to access both the state and setters 
export const useUserActions = () => {
  const { username, setUsername, isLoggedIn, setIsLoggedIn, preferences, setPreferences } = useUserContext();
  return { username, setUsername, isLoggedIn, setIsLoggedIn, preferences, setPreferences };
};
