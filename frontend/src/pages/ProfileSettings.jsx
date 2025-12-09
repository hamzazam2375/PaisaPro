import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { authAPI } from '../services/api';
import './FinancialPages.css';

const ProfileSettings = () => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        first_name: '',
        last_name: '',
        email: ''
    });
    const [loading, setLoading] = useState(false);
    const [success, setSuccess] = useState('');
    const [error, setError] = useState('');
    const [showOtpInput, setShowOtpInput] = useState(false);
    const [otp, setOtp] = useState('');
    const [pendingEmail, setPendingEmail] = useState('');
    const [showDeleteModal, setShowDeleteModal] = useState(false);
    const [deleteConfirmation, setDeleteConfirmation] = useState('');
    const [deleteLoading, setDeleteLoading] = useState(false);

    useEffect(() => {
        if (user) {
            setFormData({
                first_name: user.first_name || '',
                last_name: user.last_name || '',
                email: user.email || ''
            });
        }
    }, [user]);

    useEffect(() => {
        if (showDeleteModal) {
            // Prevent body scroll when modal is open
            document.body.style.overflow = 'hidden';
        } else {
            document.body.style.overflow = 'unset';
        }
        return () => {
            document.body.style.overflow = 'unset';
        };
    }, [showDeleteModal]);

    const handleChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value
        });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setSuccess('');
        setLoading(true);

        try {
            const response = await authAPI.updateProfile({
                first_name: formData.first_name,
                last_name: formData.last_name,
                email: formData.email
            });

            if (response.data.requires_otp) {
                setPendingEmail(formData.email);
                setShowOtpInput(true);
                setSuccess('OTP sent to your new email! Please verify below.');
            } else {
                setSuccess('Profile updated successfully!');
            }
            setTimeout(() => setSuccess(''), 5000);
        } catch (err) {
            setError(err.response?.data?.error || 'Failed to update profile');
        } finally {
            setLoading(false);
        }
    };

    const handleVerifyOtp = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            await authAPI.verifyEmailChange({ otp });
            setShowOtpInput(false);
            setOtp('');
            setSuccess('Email verified and updated successfully!');
            // Refresh user data
            window.location.reload();
        } catch (err) {
            setError(err.response?.data?.error || 'Invalid or expired OTP');
        } finally {
            setLoading(false);
        }
    };

    const handleLogout = async () => {
        try {
            await logout();
            navigate('/');
        } catch (err) {
            console.error('Logout failed', err);
        }
    };

    const handleDeleteAccount = async (e) => {
        e.preventDefault();
        if (deleteConfirmation !== 'DELETE') {
            setError('Please type DELETE to confirm account deletion');
            return;
        }

        setError('');
        setDeleteLoading(true);

        try {
            await authAPI.deleteAccount();
            setShowDeleteModal(false);
            await logout();
            navigate('/');
        } catch (err) {
            setError(err.response?.data?.error || 'Failed to delete account');
            setDeleteLoading(false);
        }
    };

    return (
        <div className="financial-page-container">
            <header className="dashboard-header">
                <div className="header-left">
                    <h1 className="logo">PaisaPro</h1>
                    <p style={{ margin: 0, fontSize: '0.85rem', color: 'rgba(255,255,255,0.6)' }}>
                        Profile Settings
                    </p>
                </div>
                <div className="header-right">
                    <Link to="/dashboard" className="nav-link">Dashboard</Link>
                    <button onClick={handleLogout} className="btn btn-secondary">Logout</button>
                </div>
            </header>

            <main className="financial-page-main">
                <div className="page-card">
                    <h2>👤 Profile Settings</h2>
                    <p className="page-description">Manage your account information</p>

                    {error && <div className="alert alert-error">{error}</div>}
                    {success && <div className="alert alert-success">{success}</div>}

                    {showOtpInput && (
                        <div className="income-setup-overlay" style={{ background: 'rgba(0,0,0,0.8)', position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
                            <div className="income-setup-modal" style={{ background: '#2d2d2d', padding: '2rem', borderRadius: '12px', maxWidth: '500px', width: '90%' }}>
                                <h3 style={{ color: '#fff', marginBottom: '1rem' }}>Verify New Email</h3>
                                <p style={{ color: 'rgba(255,255,255,0.8)', marginBottom: '1.5rem' }}>
                                    We sent a verification code to <strong>{pendingEmail}</strong>
                                </p>
                                <form onSubmit={handleVerifyOtp}>
                                    <div className="form-group">
                                        <label htmlFor="otp" style={{ color: '#fff' }}>Enter OTP:</label>
                                        <input
                                            type="text"
                                            id="otp"
                                            value={otp}
                                            onChange={(e) => setOtp(e.target.value)}
                                            placeholder="Enter 6-digit code"
                                            maxLength="6"
                                            required
                                            style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', border: '1px solid #444', background: '#1a1a1a', color: '#fff' }}
                                        />
                                    </div>
                                    <div className="form-actions" style={{ marginTop: '1.5rem', display: 'flex', gap: '1rem' }}>
                                        <button type="submit" className="btn btn-primary" disabled={loading}>
                                            {loading ? 'Verifying...' : 'Verify OTP'}
                                        </button>
                                        <button type="button" className="btn btn-secondary" onClick={() => { setShowOtpInput(false); setOtp(''); }}>
                                            Cancel
                                        </button>
                                    </div>
                                </form>
                            </div>
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="financial-form">
                        <div className="form-group">
                            <label htmlFor="first_name">First Name:</label>
                            <input
                                type="text"
                                id="first_name"
                                name="first_name"
                                value={formData.first_name}
                                onChange={handleChange}
                                required
                            />
                        </div>

                        <div className="form-group">
                            <label htmlFor="last_name">Last Name:</label>
                            <input
                                type="text"
                                id="last_name"
                                name="last_name"
                                value={formData.last_name}
                                onChange={handleChange}
                                required
                            />
                        </div>

                        <div className="form-group">
                            <label htmlFor="email">Email Address:</label>
                            <input
                                type="email"
                                id="email"
                                name="email"
                                value={formData.email}
                                onChange={handleChange}
                                required
                            />
                            <small style={{ color: 'rgba(255,255,255,0.6)' }}>
                                Changing email will require OTP verification
                            </small>
                        </div>

                        <div className="form-group">
                            <label>Account Created:</label>
                            <input
                                type="text"
                                value={user?.date_joined ? new Date(user.date_joined).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' }) : 'N/A'}
                                disabled
                            />
                            <small style={{ color: 'rgba(255,255,255,0.6)' }}>
                                Your account registration date
                            </small>
                        </div>

                        <div className="form-group">
                            <label>Username:</label>
                            <input
                                type="text"
                                value={user?.username || ''}
                                disabled
                            />
                            <small style={{ color: 'rgba(255,255,255,0.6)' }}>
                                Username cannot be changed
                            </small>
                        </div>

                        <div className="form-actions">
                            <button type="submit" className="btn btn-primary" disabled={loading}>
                                {loading ? 'Updating...' : 'Update Profile'}
                            </button>
                            <Link to="/dashboard" className="btn btn-link">Cancel</Link>
                        </div>
                    </form>

                    <div className="profile-section" style={{ marginTop: '2rem', paddingTop: '2rem', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
                        <h3>🔒 Security</h3>
                        <p style={{ color: 'rgba(255,255,255,0.7)', marginBottom: '1rem' }}>Update your account password securely</p>
                        <Link to="/forgot-password" className="btn btn-secondary" style={{ marginTop: '1rem' }}>
                            Change Password
                        </Link>
                    </div>

                    <div className="profile-section" style={{ marginTop: '2rem', paddingTop: '2rem', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
                        <h3>⚠️ Danger Zone</h3>
                        <p style={{ color: 'rgba(255,255,255,0.7)', marginBottom: '1rem' }}>Permanently delete your account and all associated data</p>
                        <button
                            onClick={() => setShowDeleteModal(true)}
                            className="btn"
                            style={{ marginTop: '1rem', background: 'rgba(220, 38, 38, 0.2)', color: '#ef4444', border: '1px solid rgba(220, 38, 38, 0.5)' }}
                        >
                            Delete Account
                        </button>
                    </div>

                    <Link to="/dashboard" className="back-link">← Back to Dashboard</Link>
                </div>
            </main>

            {showDeleteModal && (
                <div className="modal d-block" style={{ backgroundColor: 'rgba(0,0,0,0.8)', position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, zIndex: 9999 }}>
                    <div className="modal-dialog modal-dialog-centered">
                        <div className="modal-content" style={{ border: '1px solid rgba(220, 38, 38, 0.5)' }}>
                            <div className="modal-header" style={{ borderBottom: '1px solid rgba(220, 38, 38, 0.3)' }}>
                                <h5 className="modal-title" style={{ color: '#ef4444' }}>⚠️ Delete Account</h5>
                            </div>
                            <div className="modal-body">
                                <p style={{ color: 'rgba(255,255,255,0.9)', marginBottom: '1rem', lineHeight: '1.6' }}>
                                    This action <strong>cannot be undone</strong>. This will permanently delete your account and remove all your data from our servers.
                                </p>
                                <div style={{ background: 'rgba(220, 38, 38, 0.1)', padding: '1rem', borderRadius: '8px', border: '1px solid rgba(220, 38, 38, 0.3)', marginBottom: '1.5rem' }}>
                                    <p style={{ color: 'rgba(255,255,255,0.9)', marginBottom: '0.5rem', fontWeight: '600' }}>This will permanently delete:</p>
                                    <ul style={{ color: 'rgba(255,255,255,0.8)', paddingLeft: '1.5rem', marginBottom: 0 }}>
                                        <li>Your user account and profile</li>
                                        <li>All transaction history</li>
                                        <li>All budget data and financial records</li>
                                        <li>All savings and expense records</li>
                                        <li>All notifications and settings</li>
                                    </ul>
                                </div>
                                <form onSubmit={handleDeleteAccount}>
                                    <div className="mb-3">
                                        <label htmlFor="deleteConfirmation" className="form-label" style={{ color: '#fff' }}>
                                            Type <strong style={{ color: '#ef4444' }}>DELETE</strong> to confirm:
                                        </label>
                                        <input
                                            type="text"
                                            id="deleteConfirmation"
                                            className="form-control"
                                            value={deleteConfirmation}
                                            onChange={(e) => setDeleteConfirmation(e.target.value)}
                                            placeholder="Type DELETE"
                                            required
                                        />
                                    </div>
                                    <div className="d-flex gap-2">
                                        <button
                                            type="submit"
                                            className="btn btn-danger flex-fill"
                                            disabled={deleteLoading || deleteConfirmation !== 'DELETE'}
                                            style={{ opacity: (deleteLoading || deleteConfirmation !== 'DELETE') ? 0.5 : 1 }}
                                        >
                                            {deleteLoading ? 'Deleting...' : 'Delete My Account'}
                                        </button>
                                        <button
                                            type="button"
                                            className="btn btn-secondary flex-fill"
                                            onClick={() => { setShowDeleteModal(false); setDeleteConfirmation(''); }}
                                            disabled={deleteLoading}
                                        >
                                            Cancel
                                        </button>
                                    </div>
                                </form>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ProfileSettings;
