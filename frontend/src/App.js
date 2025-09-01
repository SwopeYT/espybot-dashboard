import { useState, useEffect } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, useNavigate, useLocation } from "react-router-dom";
import axios from "axios";
import { AuthProvider, useAuth } from "./AuthContext";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Configure axios defaults
axios.defaults.withCredentials = true;

// Icon Components
const DashboardIcon = () => (
  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
    <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z"/>
  </svg>
);

const VoiceIcon = () => (
  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
    <path fillRule="evenodd" d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z" clipRule="evenodd"/>
  </svg>
);

const CommandsIcon = () => (
  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
    <path fillRule="evenodd" d="M12.316 3.051a1 1 0 01.633 1.265l-4 12a1 1 0 11-1.898-.632l4-12a1 1 0 011.265-.633zM5.707 6.293a1 1 0 010 1.414L3.414 10l2.293 2.293a1 1 0 11-1.414 1.414l-3-3a1 1 0 010-1.414l3-3a1 1 0 011.414 0zm8.586 0a1 1 0 011.414 0l3 3a1 1 0 010 1.414l-3 3a1 1 0 11-1.414-1.414L16.586 10l-2.293-2.293a1 1 0 010-1.414z" clipRule="evenodd"/>
  </svg>
);

const LogsIcon = () => (
  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
    <path d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm0 2h12v10H4V5zm2 2a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm0 3a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm0 3a1 1 0 011-1h4a1 1 0 110 2H7a1 1 0 01-1-1z"/>
  </svg>
);

const SupportIcon = () => (
  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd"/>
  </svg>
);

const DiscordIcon = () => (
  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
    <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z"/>
  </svg>
);

const AppContent = () => {
  const [selectedServer, setSelectedServer] = useState(null);
  const { user, isAuthenticated, loading, login, logout } = useAuth();

  const handleServerSelect = (server) => {
    setSelectedServer(server);
  };

  const handleServerChange = () => {
    setSelectedServer(null);
  };

  const handleSignOut = () => {
    logout();
    setSelectedServer(null);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-dark flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-espyBlue border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <div className="text-white text-xl font-title mb-2">LOADING</div>
          <div className="text-gray-400 text-sm">authenticating...</div>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-dark flex items-center justify-center">
        <div className="text-center">
          <img 
            src="https://customer-assets.emergentagent.com/job_community-hub-71/artifacts/b6udatu7_IMG_0965.jpeg"
            alt="ESPY Bot Logo"
            className="h-20 w-20 object-cover rounded-full border-2 border-espyBlue mx-auto mb-6"
          />
          <h1 className="text-2xl font-title text-white mb-4">ESPYBOT DASHBOARD</h1>
          <p className="text-gray-400 mb-6">Sign in with Discord to manage your bot</p>
          <button
            onClick={login}
            className="bg-gradient-to-r from-espyBlue to-blue-600 hover:from-blue-600 hover:to-blue-700 px-6 py-3 rounded-lg text-white font-medium flex items-center space-x-2 mx-auto"
          >
            <DiscordIcon />
            <span>Sign in with Discord</span>
          </button>
        </div>
      </div>
    );
  }

  if (!selectedServer) {
    return <ServerSelection onServerSelect={handleServerSelect} />;
  }

  return (
    <div className="App bg-dark min-h-screen">
      <BrowserRouter>
        <div className="text-center p-20">
          <h1 className="text-4xl font-title text-white mb-4">ESPYBOT DASHBOARD</h1>
          <p className="text-gray-400">Your Discord bot management interface</p>
          <p className="text-espyBlue mt-4">Managing: {selectedServer?.name}</p>
        </div>
      </BrowserRouter>
    </div>
  );
};

const ServerSelection = ({ onServerSelect }) => {
  const [guilds, setGuilds] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchGuilds = async () => {
      try {
        const response = await axios.get(`${API}/bot/guilds`);
        setGuilds(response.data);
      } catch (error) {
        console.error("Error fetching guilds:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchGuilds();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-dark flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-espyBlue border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <div className="text-white text-xl font-title mb-2">LOADING SERVERS</div>
          <div className="text-gray-400 text-sm">connecting to your discord servers...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-dark flex items-center justify-center p-4">
      <div className="bg-dark-card rounded-2xl border border-gray-800 p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <img 
            src="https://customer-assets.emergentagent.com/job_community-hub-71/artifacts/b6udatu7_IMG_0965.jpeg"
            alt="ESPY Bot Logo"
            className="h-16 w-16 object-cover rounded-full border-2 border-espyBlue mx-auto mb-4"
          />
          <h1 className="text-2xl font-title text-white mb-2">SELECT SERVER</h1>
          <p className="text-gray-400">choose which discord server to manage</p>
        </div>

        {guilds.length === 0 ? (
          <div className="text-center py-8">
            <div className="w-12 h-12 bg-gray-800 rounded-lg flex items-center justify-center mx-auto mb-4">
              <DiscordIcon />
            </div>
            <div className="text-gray-300 font-medium mb-2">no servers found</div>
            <div className="text-sm text-gray-500">make sure espy bot is added to your server</div>
          </div>
        ) : (
          <div className="space-y-3">
            {guilds.map(guild => (
              <button
                key={guild.id}
                onClick={() => onServerSelect(guild)}
                className="w-full bg-gray-800 hover:bg-gray-700 border border-gray-700 hover:border-espyBlue rounded-xl p-4 text-left transition-colors"
              >
                <div className="flex items-center space-x-3">
                  {guild.icon ? (
                    <img 
                      src={guild.icon}
                      alt={`${guild.name} icon`}
                      className="w-12 h-12 rounded-lg object-cover"
                    />
                  ) : (
                    <div className="w-12 h-12 bg-gradient-to-br from-espyBlue to-blue-600 rounded-lg flex items-center justify-center text-white font-bold">
                      {guild.name.charAt(0)}
                    </div>
                  )}
                  <div>
                    <div className="text-white font-medium">{guild.name}</div>
                    <div className="text-sm text-gray-400">{guild.member_count} members</div>
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

const App = () => {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
};

export default App;
