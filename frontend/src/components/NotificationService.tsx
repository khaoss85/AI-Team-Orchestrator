"use client"

import React, { useState, useEffect } from 'react';

interface Notification {
  id: string;
  type: 'success' | 'error' | 'info' | 'warning';
  title: string;
  message: string;
  autoClose?: boolean;
  duration?: number;
}

interface NotificationServiceProps {
  children: React.ReactNode;
}

export const NotificationContext = React.createContext<{
  addNotification: (notification: Omit<Notification, 'id'>) => void;
  removeNotification: (id: string) => void;
  clearAll: () => void;
}>({
  addNotification: () => {},
  removeNotification: () => {},
  clearAll: () => {},
});

export const useNotifications = () => React.useContext(NotificationContext);

export const NotificationService: React.FC<NotificationServiceProps> = ({ children }) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  
  const addNotification = (notification: Omit<Notification, 'id'>) => {
    const id = Date.now().toString();
    const newNotification = {
      ...notification,
      id,
      autoClose: notification.autoClose ?? true,
      duration: notification.duration ?? 5000,
    };
    
    setNotifications(prev => [...prev, newNotification]);
    
    if (newNotification.autoClose) {
      setTimeout(() => {
        removeNotification(id);
      }, newNotification.duration);
    }
  };
  
  const removeNotification = (id: string) => {
    setNotifications(prev => prev.filter(notification => notification.id !== id));
  };
  
  const clearAll = () => {
    setNotifications([]);
  };
  
  return (
    <NotificationContext.Provider value={{ addNotification, removeNotification, clearAll }}>
      {children}
      <NotificationContainer 
        notifications={notifications} 
        removeNotification={removeNotification} 
      />
    </NotificationContext.Provider>
  );
};

const NotificationContainer: React.FC<{
  notifications: Notification[];
  removeNotification: (id: string) => void;
}> = ({ notifications, removeNotification }) => {
  if (notifications.length === 0) return null;
  
  return (
    <div className="fixed bottom-6 left-6 z-50 space-y-3 max-w-sm">
      {notifications.map(notification => (
        <NotificationItem 
          key={notification.id} 
          notification={notification} 
          onClose={() => removeNotification(notification.id)} 
        />
      ))}
    </div>
  );
};

const NotificationItem: React.FC<{
  notification: Notification;
  onClose: () => void;
}> = ({ notification, onClose }) => {
  const [progress, setProgress] = useState(100);
  
  useEffect(() => {
    if (notification.autoClose) {
      const interval = setInterval(() => {
        setProgress(prev => {
          const newProgress = prev - (100 / (notification.duration! / 100));
          return newProgress < 0 ? 0 : newProgress;
        });
      }, 100);
      
      return () => clearInterval(interval);
    }
  }, [notification.autoClose, notification.duration]);
  
  const getTypeStyles = () => {
    switch (notification.type) {
      case 'success':
        return 'bg-green-50 border-green-500 text-green-800';
      case 'error':
        return 'bg-red-50 border-red-500 text-red-800';
      case 'warning':
        return 'bg-yellow-50 border-yellow-500 text-yellow-800';
      case 'info':
      default:
        return 'bg-blue-50 border-blue-500 text-blue-800';
    }
  };
  
  const getTypeIcon = () => {
    switch (notification.type) {
      case 'success':
        return '✅';
      case 'error':
        return '❌';
      case 'warning':
        return '⚠️';
      case 'info':
      default:
        return 'ℹ️';
    }
  };
  
  return (
    <div className={`border-l-4 rounded-md shadow-lg ${getTypeStyles()} transform transition-all duration-300 hover:-translate-y-1`}>
      <div className="p-4">
        <div className="flex justify-between items-start">
          <div className="flex space-x-3">
            <span className="text-xl">{getTypeIcon()}</span>
            <div>
              <h3 className="font-medium">{notification.title}</h3>
              <p className="text-sm mt-1">{notification.message}</p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            ✕
          </button>
        </div>
      </div>
      
      {notification.autoClose && (
        <div className="h-1 bg-gray-200 rounded-b-md overflow-hidden">
          <div 
            className={`h-full ${
              notification.type === 'success' ? 'bg-green-500' :
              notification.type === 'error' ? 'bg-red-500' :
              notification.type === 'warning' ? 'bg-yellow-500' :
              'bg-blue-500'
            } transition-all ease-linear`}
            style={{ width: `${progress}%` }}
          ></div>
        </div>
      )}
    </div>
  );
};