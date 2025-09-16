import { useEffect, useState } from 'react'
import './NotificationSystem.css'

let notificationId = 0

export const NotificationSystem = () => {
  const [notifications, setNotifications] = useState([])

  useEffect(() => {
    // Listen for notification events
    const handleNotification = (event) => {
      const notification = {
        id: notificationId++,
        ...event.detail,
        timestamp: Date.now()
      }
      
      setNotifications(prev => [...prev, notification])
      
      // Auto remove after duration
      setTimeout(() => {
        setNotifications(prev => prev.filter(n => n.id !== notification.id))
      }, notification.duration || 3000)
    }

    window.addEventListener('game-notification', handleNotification)
    return () => window.removeEventListener('game-notification', handleNotification)
  }, [])

  return (
    <div className="notification-system">
      {notifications.map(notification => (
        <div 
          key={notification.id} 
          className={`notification notification-${notification.type}`}
        >
          {notification.type === 'xp' && (
            <div className="notification-xp">
              <i className="fas fa-star"></i>
              <span>+{notification.amount} XP</span>
            </div>
          )}
          
          {notification.type === 'level-up' && (
            <div className="notification-level-up">
              <i className="fas fa-trophy"></i>
              <div>
                <div className="level-up-text">LEVEL UP!</div>
                <div className="level-info">Level {notification.newLevel}</div>
              </div>
            </div>
          )}
          
          {notification.type === 'achievement' && (
            <div className="notification-achievement">
              <i className={`fas ${notification.icon}`}></i>
              <div>
                <div className="achievement-title">Achievement Unlocked!</div>
                <div className="achievement-name">{notification.name}</div>
                <div className="achievement-desc">{notification.description}</div>
              </div>
            </div>
          )}
          
          {notification.type === 'skill' && (
            <div className="notification-skill">
              <i className="fas fa-arrow-up"></i>
              <span>{notification.skill} +{notification.amount}</span>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

// Helper functions to trigger notifications
export const showXPNotification = (amount) => {
  window.dispatchEvent(new CustomEvent('game-notification', {
    detail: {
      type: 'xp',
      amount,
      duration: 2000
    }
  }))
}

export const showLevelUpNotification = (newLevel, oldLevel) => {
  window.dispatchEvent(new CustomEvent('game-notification', {
    detail: {
      type: 'level-up',
      newLevel,
      oldLevel,
      duration: 4000
    }
  }))
}

export const showAchievementNotification = (achievement) => {
  window.dispatchEvent(new CustomEvent('game-notification', {
    detail: {
      type: 'achievement',
      name: achievement.name,
      description: achievement.description,
      icon: achievement.icon,
      duration: 5000
    }
  }))
}

export const showSkillNotification = (skill, amount) => {
  window.dispatchEvent(new CustomEvent('game-notification', {
    detail: {
      type: 'skill',
      skill,
      amount,
      duration: 2500
    }
  }))
}

export default NotificationSystem