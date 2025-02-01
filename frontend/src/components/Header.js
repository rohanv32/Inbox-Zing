import React, { useState, useEffect } from 'react';
import { Dialog, DialogPanel } from '@headlessui/react';
import { Bars3Icon, XMarkIcon } from '@heroicons/react/24/outline';
import { useUserContext } from './UserContext';
import { useNavigate, useLocation } from 'react-router-dom';

const Header = ({ isLoggedIn, onLogout, onLogoClick, themeMode, toggleTheme }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);

  const { points } = useUserContext();
  const navigate = useNavigate();
  const location = useLocation();

  const navigation = isLoggedIn
    ? [
        { name: 'News Feed', path: '/newsfeed', emoji: '📰' },
        { name: 'Preferences', path: '/preferences', emoji: '⚙️' },
        { name: 'Delete Account', path: '/deleteuser', emoji: '🗑️' },
        { name: 'Profile', path: '/profile', emoji: '👤' },
        { name: 'Logout', onClick: onLogout, emoji: '🚪' },
      ]
    : [];

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const handleNavigation = (path, onClick) => {
    if (onClick) {
      onClick();
    } else if (path) {
      navigate(path);
    }
    setMobileMenuOpen(false);
  };

  const isDarkMode = themeMode === 'Dark';

  return (
    <header
      className={`fixed inset-x-0 top-0 z-50 transition-all duration-300 ${
        isScrolled
          ? isDarkMode
            ? 'bg-gray-900 shadow-md'
            : 'bg-white shadow-md'
          : 'bg-transparent'
      }`}
    >
      <nav className="flex items-center justify-between p-6 lg:px-8">
        <div className="flex lg:flex-1 items-center">
          <button onClick={onLogoClick} className="-m-1.5 p-1.5">
            <span className="sr-only">Inbox Zing</span>
            <h1 className={`text-xl font-bold ${isDarkMode ? 'text-white' : 'text-black'}`}>Inbox Zing</h1>
          </button>
          {isLoggedIn && (
            <span className="ml-4 px-4 py-2 text-sm font-semibold text-white bg-gradient-to-r from-blue-500 to-purple-500 rounded-full shadow-md">
              💎 Points: {points}
            </span>
          )}
        </div>

        <div className="flex lg:hidden">
          <button
            onClick={() => setMobileMenuOpen(true)}
            className={`-m-2.5 inline-flex items-center justify-center rounded-md p-2.5 ${
              isDarkMode ? 'text-white' : 'text-gray-700'
            }`}
          >
            <span className="sr-only">Open main menu</span>
            <Bars3Icon className="h-6 w-6" aria-hidden="true" />
          </button>
        </div>

        <div className="hidden lg:flex lg:gap-x-12">
          {navigation.map((item) => (
            <button
              key={item.name}
              onClick={() => handleNavigation(item.path, item.onClick)}
              className={`text-sm font-semibold ${
                location.pathname === item.path
                  ? 'text-blue-500'
                  : isDarkMode
                  ? 'text-white'
                  : 'text-black'
              } hover:text-blue-500 transition-colors duration-200 px-3 py-2 rounded-md hover:bg-opacity-10 ${
                isDarkMode ? 'hover:bg-white' : 'hover:bg-black'
              }`}
            >
              {item.emoji} {item.name}
            </button>
          ))}
          <button
            onClick={toggleTheme}
            className={`text-sm font-semibold ${
              isDarkMode ? 'text-white' : 'text-black'
            } hover:text-blue-500 transition-colors duration-200 px-3 py-2 rounded-md hover:bg-opacity-10 ${
              isDarkMode ? 'hover:bg-white' : 'hover:bg-black'
            }`}
          >
            {isDarkMode ? '☀️' : '🌙'}
          </button>
        </div>
      </nav>

      <Dialog as="div" className="lg:hidden" open={mobileMenuOpen} onClose={() => setMobileMenuOpen(false)}>
        <div className="fixed inset-0 z-50" />
        <DialogPanel className={`fixed inset-y-0 right-0 z-50 w-full overflow-y-auto px-6 py-6 sm:max-w-sm sm:ring-1 sm:ring-gray-900/10 ${
          isDarkMode ? 'bg-gray-900 text-white' : 'bg-white text-black'
        }`}>
          <div className="flex items-center justify-between">
            <button onClick={onLogoClick} className="-m-1.5 p-1.5">
              <span className="sr-only">Inbox Zing</span>
              <h1 className={`text-xl font-bold ${isDarkMode ? 'text-white' : 'text-black'}`}>Inbox Zing</h1>
            </button>
            <button
              onClick={() => setMobileMenuOpen(false)}
              className="-m-2.5 rounded-md p-2.5"
            >
              <span className="sr-only">Close menu</span>
              <XMarkIcon className={`h-6 w-6 ${isDarkMode ? 'text-white' : 'text-gray-700'}`} />
            </button>
          </div>
          <div className="mt-6 flow-root">
            <div className="-my-6 divide-y divide-gray-500/10">
              <div className="space-y-2 py-6">
                {navigation.map((item) => (
                  <button
                    key={item.name}
                    onClick={() => handleNavigation(item.path, item.onClick)}
                    className={`block rounded-lg px-3 py-2 text-base font-semibold ${
                      location.pathname === item.path ? 'text-blue-500' : isDarkMode ? 'text-white' : 'text-black'
                    } hover:bg-opacity-10 ${isDarkMode ? 'hover:bg-white' : 'hover:bg-black'}`}
                  >
                    {item.emoji} {item.name}
                  </button>
                ))}
                <button
                  onClick={toggleTheme}
                  className={`block rounded-lg px-3 py-2 text-base font-semibold ${
                    isDarkMode ? 'text-white' : 'text-black'
                  } hover:bg-opacity-10 ${isDarkMode ? 'hover:bg-white' : 'hover:bg-black'}`}
                >
                  {isDarkMode ? '☀️ Light Mode' : '🌙 Dark Mode'}
                </button>
              </div>
            </div>
          </div>
        </DialogPanel>
      </Dialog>
    </header>
  );
};

export default Header;
