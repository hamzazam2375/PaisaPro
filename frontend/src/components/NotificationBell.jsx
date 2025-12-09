import { useState, useEffect } from 'react';
import './NotificationBell.css';

const NotificationBell = () => {
    const [notifications, setNotifications] = useState([]);
    const [unreadCount, setUnreadCount] = useState(0);
    const [showDropdown, setShowDropdown] = useState(false);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        fetchNotifications();
        // Poll for new notifications every 30 seconds
        const interval = setInterval(fetchNotifications, 30000);
        return () => clearInterval(interval);
    }, []);

    const fetchNotifications = async () => {
        try {
            const response = await fetch('/api/notifications/', {
                credentials: 'include'
            });
            const data = await response.json();
            setNotifications(data.notifications || []);
            setUnreadCount(data.unread_count || 0);
        } catch (err) {
            console.error('Failed to fetch notifications', err);
        }
    };

    const markAsRead = async (notificationId) => {
        try {
            await fetch(`/api/notifications/${notificationId}/read/`, {
                method: 'POST',
                credentials: 'include',
                headers: {
                    'X-CSRFToken': document.cookie.split('csrftoken=')[1]?.split(';')[0]
                }
            });
            fetchNotifications();
        } catch (err) {
            console.error('Failed to mark notification as read', err);
        }
    };

    const markAllAsRead = async () => {
        setLoading(true);
        try {
            await fetch('/api/notifications/read-all/', {
                method: 'POST',
                credentials: 'include',
                headers: {
                    'X-CSRFToken': document.cookie.split('csrftoken=')[1]?.split(';')[0]
                }
            });
            fetchNotifications();
        } catch (err) {
            console.error('Failed to mark all as read', err);
        } finally {
            setLoading(false);
        }
    };

    const clearAllNotifications = async () => {
        setLoading(true);
        try {
            await fetch('/api/notifications/clear-all/', {
                method: 'POST',
                credentials: 'include',
                headers: {
                    'X-CSRFToken': document.cookie.split('csrftoken=')[1]?.split(';')[0]
                }
            });
            fetchNotifications();
        } catch (err) {
            console.error('Failed to clear notifications', err);
        } finally {
            setLoading(false);
        }
    };

    const getNotificationIcon = (type) => {
        switch (type) {
            case 'unusual_spending':
                return '⚠️';
            case 'budget_alert':
                return '💰';
            case 'savings_goal':
                return '🎯';
            default:
                return '📢';
        }
    };

    return (
        <div className="notification-bell-container">
            <button
                className="notification-bell-btn"
                onClick={() => setShowDropdown(!showDropdown)}
            >
                <i className="fas fa-bell"></i>
                {unreadCount > 0 && (
                    <span className="notification-badge">{unreadCount}</span>
                )}
            </button>

            {showDropdown && (
                <div className="notification-dropdown">
                    <div className="notification-header">
                        <h4>Notifications</h4>
                        <div className="notification-actions">
                            {unreadCount > 0 && (
                                <button
                                    className="mark-all-read-btn"
                                    onClick={markAllAsRead}
                                    disabled={loading}
                                    title="Mark all as read"
                                >
                                    {loading ? 'Marking...' : 'Mark all read'}
                                </button>
                            )}
                            {notifications.length > 0 && (
                                <button
                                    className="clear-all-btn"
                                    onClick={clearAllNotifications}
                                    disabled={loading}
                                    title="Clear all notifications"
                                >
                                    <i className="fas fa-trash-alt"></i>
                                </button>
                            )}
                        </div>
                    </div>

                    <div className="notification-list">
                        {notifications.length === 0 ? (
                            <div className="no-notifications">
                                <i className="fas fa-check-circle"></i>
                                <p>No notifications</p>
                            </div>
                        ) : (
                            notifications.map((notification) => (
                                <div
                                    key={notification.id}
                                    className={`notification-item ${!notification.is_read ? 'unread' : ''}`}
                                    onClick={() => markAsRead(notification.id)}
                                >
                                    <div className="notification-icon">
                                        {getNotificationIcon(notification.type)}
                                    </div>
                                    <div className="notification-content">
                                        <h5>{notification.title}</h5>
                                        <p>{notification.message && notification.message.replace(/(PKR|Rs\.?)/gi, '$')}</p>
                                        <span className="notification-time">
                                            {new Date(notification.created_at).toLocaleString()}
                                        </span>
                                    </div>
                                    {!notification.is_read && (
                                        <div className="unread-indicator"></div>
                                    )}
                                </div>
                            ))
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

export default NotificationBell;
