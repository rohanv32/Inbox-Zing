import React, { useEffect, useState, useRef } from "react";
import { useNavigate } from 'react-router-dom';
import { Spin, Alert } from "antd";
import { PlayCircleOutlined, PauseCircleOutlined } from "@ant-design/icons";
import "react-h5-audio-player/lib/styles.css";
import Swal from 'sweetalert2';

const Podcast = ({ username, themeMode }) => {
  const [audioUrl, setAudioUrl] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const popupShownRef = useRef(false);
  const audioRef = useRef(null);

  const navigate = useNavigate();

  useEffect(() => {
    const fetchPodcast = async () => {
      if (popupShownRef.current) return;
      popupShownRef.current = true;
      setIsLoading(true);
      setError(null);

      try {
        const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/podcast/${username}`);
        if (!response.ok) {
          popupShownRef.current = true;
          //throw new Error("The podcast feature is not currently available, please try again later.");
          await Swal.fire({
                  title: "😸 says...",
                  text: "The podcast feature is not currently available, please try again later.",
                  imageUrl: "https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExZGNkNmR3eDRtejQ2ODEwNWJlZ2p3Z2xlMXQ2MDRyczQ3Nm1ocm5oaSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/qUIm5wu6LAAog/giphy.gif",
                  imageWidth: 400,
                  imageHeight: 200,
                  confirmButtonText: "I understand",
                  padding: "2em",
                  showCloseButton: false,
            }).then((result) => {
              if (result.isConfirmed) {
                navigate("/newsfeed");
              }
            });
        }

        const audioUrl = `${process.env.REACT_APP_BACKEND_URL}/podcast/${username}`;
        setAudioUrl(audioUrl);
      } catch (error) {
        setError(error.message);
      } finally {
        setIsLoading(false);
      }
    };

    if (username && !popupShownRef.current) {
      fetchPodcast();
    }
  }, [username, navigate]);

  const handlePlayPause = () => {
    const audioElement = audioRef.current;

    if (audioElement) {
      if (isPlaying) {
        audioElement.pause();
        setIsPlaying(false);
      } else {
        audioElement.play()
          .then(() => setIsPlaying(true))
          .catch((error) => {
            console.error("Audio playback error:", error);
            setIsPlaying(false);
          });
      }
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center" style={{ backgroundColor: themeMode === 'Dark' ? '#1a1a1a' : '#f9f9f9' }}>
      <div
        className="max-w-lg w-full p-8 text-center rounded-lg shadow-lg"
        style={{
          background: 'linear-gradient(to bottom, #a64af7, #6d25b0)', // Purple gradient
          color: '#ffffff', // White text for contrast
        }}
      >
        <h1 className="text-4xl font-bold mb-8">🎙️ Podcast for {username}</h1>

        {isLoading ? (
          <div className="flex justify-center items-center">
            <Spin size="large" tip="Loading your podcast..." />
          </div>
        ) : error ? (
          <Alert message="Error" description={error} type="error" showIcon />
        ) : (
          <div className="podcast-audio">
            <h2 className="text-2xl font-semibold mb-4">
              {isPlaying ? "Now Playing" : "Paused"}
            </h2>
            {audioUrl ? (
              <div className="relative">
                <div
                  className="p-4 rounded-lg shadow-md mb-4"
                  style={{
                    background: '#7a27c7', // Slightly darker purple for the inner box
                  }}
                >
                  <audio
                    id="podcast-audio"
                    ref={audioRef}
                    src={audioUrl}
                    onEnded={() => setIsPlaying(false)}
                    className="hidden"
                  />
                  <button
                    onClick={handlePlayPause}
                    className="text-6xl focus:outline-none"
                    style={{
                      color: '#ffffff', // White icon color
                    }}
                  >
                    {isPlaying ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
                  </button>
                </div>
                <div className="text-sm italic" style={{ color: '#e5e5e5' }}>
                  {isPlaying ? "Enjoy the podcast!" : "Click to play"}
                </div>
              </div>
            ) : (
              <p className="text-gray-500">No audio available</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Podcast;
