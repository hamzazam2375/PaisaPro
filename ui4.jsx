import React, { useState, useEffect } from 'react';
import { 
  ShoppingCart, 
  BarChart3, 
  Search, 
  User,
  DollarSign,
  Plus,
  Trash2,
  RefreshCw,
  CheckCircle,
  TrendingUp,
  ExternalLink,
  Loader2,
  Package,
  ArrowLeft,
  LogOut
} from 'lucide-react';

const API_BASE = 'http://localhost:8000/api';

export default function PaisaProApp() {
  const [currentView, setCurrentView] = useState('dashboard');
  const [user, setUser] = useState(null);
  const [shoppingLists, setShoppingLists] = useState([]);
  const [currentList, setCurrentList] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showUserMenu, setShowUserMenu] = useState(false);

  // Initialize user on app start
  useEffect(() => {
    initializeUser();
  }, []);

  useEffect(() => {
    if (currentView === 'dashboard' && user) {
      fetchUserLists();
    }
  }, [currentView, user]);

  const initializeUser = () => {
    const savedUser = localStorage.getItem('paisapro_user');
    if (savedUser) {
      setUser(JSON.parse(savedUser));
    } else {
      const newUser = {
        id: `user_${Date.now()}`,
        name: generateRandomName(),
        email: '',
        created_at: new Date().toISOString()
      };
      setUser(newUser);
      localStorage.setItem('paisapro_user', JSON.stringify(newUser));
    }
  };

  const generateRandomName = () => {
    const firstNames = ['Alex', 'Sam', 'Taylor', 'Jordan', 'Casey', 'Morgan', 'Riley', 'Avery'];
    const lastNames = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis'];
    const firstName = firstNames[Math.floor(Math.random() * firstNames.length)];
    const lastName = lastNames[Math.floor(Math.random() * lastNames.length)];
    return `${firstName} ${lastName}`;
  };

  const updateUserName = (newName) => {
    if (newName.trim() && user) {
      const updatedUser = { ...user, name: newName.trim() };
      setUser(updatedUser);
      localStorage.setItem('paisapro_user', JSON.stringify(updatedUser));
      setShowUserMenu(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('paisapro_user');
    setUser(null);
    setShoppingLists([]);
    setCurrentList(null);
    initializeUser();
    setShowUserMenu(false);
  };

  const fetchUserLists = async () => {
    if (!user) return;
    
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/user/${user.id}/lists`);
      const data = await response.json();
      if (data.success) {
        setShoppingLists(data.lists);
      }
    } catch (err) {
      setError('Failed to fetch shopping lists');
    } finally {
      setLoading(false);
    }
  };

  const createNewList = async (listName, items) => {
    if (!user) return;
    
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/cart/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: user.id,
          list_name: listName,
          items: items
        })
      });
      const data = await response.json();
      if (data.success) {
        await fetchUserLists();
        setCurrentView('dashboard');
      }
    } catch (err) {
      setError('Failed to create list');
    } finally {
      setLoading(false);
    }
  };

  const fetchListDetails = async (listId) => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/cart/${listId}/optimized`);
      const data = await response.json();
      if (data) {
        setCurrentList(data);
      }
    } catch (err) {
      setError('Failed to fetch list details');
    } finally {
      setLoading(false);
    }
  };

  const refreshPrices = async (listId) => {
    try {
      setLoading(true);
      await fetch(`${API_BASE}/cart/${listId}/refresh-prices`, { method: 'POST' });
      await fetchListDetails(listId);
    } catch (err) {
      setError('Failed to refresh prices');
    } finally {
      setLoading(false);
    }
  };

  const deleteList = async (listId) => {
    if (!user) return;
    
    try {
      setLoading(true);
      await fetch(`${API_BASE}/cart/${listId}?user_id=${user.id}`, { method: 'DELETE' });
      await fetchUserLists();
    } catch (err) {
      setError('Failed to delete list');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(to bottom right, #0f172a, #1e293b, #0f172a)',
      color: '#f1f5f9',
      fontFamily: 'system-ui, -apple-system, sans-serif'
    }}>
      {/* Header */}
      <div style={{
        borderBottom: '1px solid #334155',
        backgroundColor: 'rgba(15, 23, 42, 0.8)',
        backdropFilter: 'blur(10px)',
        position: 'sticky',
        top: 0,
        zIndex: 10
      }}>
        <div style={{
          maxWidth: '1200px',
          margin: '0 auto',
          padding: '16px 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div style={{display: 'flex', alignItems: 'center', gap: '12px'}}>
            <div style={{
              padding: '10px',
              background: 'linear-gradient(to bottom right, #10b981, #059669)',
              borderRadius: '10px'
            }}>
              <ShoppingCart size={24} color="#fff" />
            </div>
            <div>
              <h1 style={{
                fontSize: '22px',
                fontWeight: 'bold',
                background: 'linear-gradient(to right, #34d399, #10b981)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                margin: 0
              }}>
                PaisaPro
              </h1>
              <p style={{color: '#94a3b8', fontSize: '13px', margin: '2px 0 0 0'}}>
                Smart Shopping Cart Optimizer
              </p>
            </div>
          </div>

          <div style={{display: 'flex', alignItems: 'center', gap: '16px', position: 'relative'}}>
            <button
              onClick={() => setCurrentView('compare')}
              style={{
                padding: '8px 16px',
                background: 'transparent',
                border: '1px solid #334155',
                borderRadius: '8px',
                color: '#f1f5f9',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                fontSize: '14px',
                transition: 'all 0.3s'
              }}
              onMouseEnter={(e) => {
                e.target.style.backgroundColor = '#1e293b';
                e.target.style.borderColor = '#10b981';
              }}
              onMouseLeave={(e) => {
                e.target.style.backgroundColor = 'transparent';
                e.target.style.borderColor = '#334155';
              }}
            >
              <Search size={16} />
              Compare Prices
            </button>
            
            {/* User Menu */}
            <div style={{position: 'relative'}}>
              <button
                onClick={() => setShowUserMenu(!showUserMenu)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '8px 12px',
                  backgroundColor: '#1e293b',
                  border: '1px solid #334155',
                  borderRadius: '8px',
                  color: '#e2e8f0',
                  cursor: 'pointer',
                  fontSize: '14px',
                  transition: 'all 0.3s'
                }}
                onMouseEnter={(e) => {
                  e.target.style.borderColor = '#10b981';
                }}
                onMouseLeave={(e) => {
                  if (!showUserMenu) {
                    e.target.style.borderColor = '#334155';
                  }
                }}
              >
                <User size={16} color="#94a3b8" />
                <span>{user?.name || 'Guest'}</span>
              </button>

              {showUserMenu && (
                <div style={{
                  position: 'absolute',
                  top: '100%',
                  right: 0,
                  marginTop: '8px',
                  backgroundColor: '#1e293b',
                  border: '1px solid #334155',
                  borderRadius: '8px',
                  padding: '8px',
                  minWidth: '200px',
                  boxShadow: '0 10px 25px rgba(0, 0, 0, 0.5)',
                  zIndex: 1000
                }}>
                  <div style={{
                    padding: '12px',
                    borderBottom: '1px solid #334155',
                    marginBottom: '8px'
                  }}>
                    <div style={{
                      fontSize: '14px',
                      fontWeight: '600',
                      color: '#f1f5f9',
                      marginBottom: '4px'
                    }}>
                      {user?.name}
                    </div>
                    <div style={{
                      fontSize: '12px',
                      color: '#94a3b8'
                    }}>
                      User ID: {user?.id}
                    </div>
                  </div>

                  <div style={{padding: '8px 12px', marginBottom: '8px'}}>
                    <input
                      type="text"
                      placeholder="Change your name"
                      defaultValue={user?.name}
                      onKeyPress={(e) => {
                        if (e.key === 'Enter') {
                          updateUserName(e.target.value);
                        }
                      }}
                      style={{
                        width: '100%',
                        padding: '8px',
                        backgroundColor: '#0f172a',
                        border: '1px solid #334155',
                        borderRadius: '6px',
                        color: '#f1f5f9',
                        fontSize: '14px',
                        outline: 'none'
                      }}
                    />
                    <div style={{
                      fontSize: '11px',
                      color: '#64748b',
                      marginTop: '4px'
                    }}>
                      Press Enter to save
                    </div>
                  </div>

                  <button
                    onClick={logout}
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      background: 'transparent',
                      border: '1px solid #334155',
                      borderRadius: '6px',
                      color: '#ef4444',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      fontSize: '14px',
                      transition: 'all 0.3s'
                    }}
                    onMouseEnter={(e) => {
                      e.target.style.backgroundColor = 'rgba(239, 68, 68, 0.1)';
                    }}
                    onMouseLeave={(e) => {
                      e.target.style.backgroundColor = 'transparent';
                    }}
                  >
                    <LogOut size={14} />
                    New User Session
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Navigation */}
        <div style={{
          maxWidth: '1200px',
          margin: '0 auto',
          padding: '0 24px 16px',
          display: 'flex',
          gap: '8px'
        }}>
          <button
            onClick={() => setCurrentView('dashboard')}
            style={{
              padding: '8px 16px',
              background: currentView === 'dashboard' ? '#10b981' : 'transparent',
              border: '1px solid',
              borderColor: currentView === 'dashboard' ? '#10b981' : '#334155',
              borderRadius: '8px',
              color: currentView === 'dashboard' ? '#fff' : '#94a3b8',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '14px',
              transition: 'all 0.3s'
            }}
          >
            <BarChart3 size={16} />
            My Lists
          </button>
          
          {currentView === 'list' && (
            <button
              onClick={() => setCurrentView('dashboard')}
              style={{
                padding: '8px 16px',
                background: 'transparent',
                border: '1px solid #334155',
                borderRadius: '8px',
                color: '#94a3b8',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                fontSize: '14px',
                transition: 'all 0.3s'
              }}
              onMouseEnter={(e) => {
                e.target.style.backgroundColor = '#1e293b';
                e.target.style.borderColor = '#10b981';
              }}
              onMouseLeave={(e) => {
                e.target.style.backgroundColor = 'transparent';
                e.target.style.borderColor = '#334155';
              }}
            >
              <ArrowLeft size={16} />
              Back to Lists
            </button>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div style={{
        maxWidth: '1200px',
        margin: '0 auto',
        padding: '24px',
        minHeight: 'calc(100vh - 120px)'
      }}>
        {error && (
          <div style={{
            marginBottom: '16px',
            padding: '12px 16px',
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid #ef4444',
            borderRadius: '10px',
            color: '#fca5a5',
            fontSize: '14px'
          }}>
            {error}
          </div>
        )}

        {loading && (
          <div style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            padding: '40px'
          }}>
            <Loader2 size={32} color="#10b981" className="spin" />
          </div>
        )}

        {!user ? (
          <div style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            padding: '60px 20px',
            color: '#94a3b8'
          }}>
            <Loader2 size={32} className="spin" />
            <span style={{marginLeft: '12px'}}>Initializing user session...</span>
          </div>
        ) : (
          <>
            {currentView === 'dashboard' && (
              <DashboardView 
                shoppingLists={shoppingLists}
                onCreateList={createNewList}
                onViewList={(list) => {
                  setCurrentList(list);
                  setCurrentView('list');
                  fetchListDetails(list.id);
                }}
                onDeleteList={deleteList}
                user={user}
              />
            )}

            {currentView === 'list' && currentList && (
              <ListView 
                list={currentList}
                onRefreshPrices={() => refreshPrices(currentList.list_id)}
                onBack={() => setCurrentView('dashboard')}
                user={user}
              />
            )}

            {currentView === 'compare' && (
              <PriceComparisonView user={user} />
            )}
          </>
        )}
      </div>

      {/* Close user menu when clicking outside */}
      {showUserMenu && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            zIndex: 999
          }}
          onClick={() => setShowUserMenu(false)}
        />
      )}

      <style>{`
        .spin {
          animation: spin 1s linear infinite;
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        
        *::-webkit-scrollbar {
          width: 6px;
        }
        *::-webkit-scrollbar-track {
          background: #0f172a;
        }
        *::-webkit-scrollbar-thumb {
          background: #334155;
          border-radius: 3px;
        }
        *::-webkit-scrollbar-thumb:hover {
          background: #475569;
        }
      `}</style>
    </div>
  );
}

// Dashboard Component
function DashboardView({ shoppingLists, onCreateList, onViewList, onDeleteList, user }) {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newListName, setNewListName] = useState('');
  const [items, setItems] = useState([{ product_name: '', quantity: 1 }]);

  const handleCreateList = () => {
    const validItems = items.filter(item => item.product_name.trim());
    if (newListName.trim() && validItems.length > 0) {
      onCreateList(newListName.trim(), validItems);
      setNewListName('');
      setItems([{ product_name: '', quantity: 1 }]);
      setShowCreateForm(false);
    }
  };

  const addItem = () => {
    setItems([...items, { product_name: '', quantity: 1 }]);
  };

  const updateItem = (index, field, value) => {
    const newItems = [...items];
    newItems[index][field] = value;
    setItems(newItems);
  };

  const removeItem = (index) => {
    if (items.length > 1) {
      setItems(items.filter((_, i) => i !== index));
    }
  };

  return (
    <div>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        marginBottom: '24px'
      }}>
        <div>
          <h2 style={{
            fontSize: '24px',
            fontWeight: 'bold',
            color: '#f1f5f9',
            margin: '0 0 8px 0'
          }}>
            My Shopping Lists
          </h2>
          <p style={{color: '#94a3b8', fontSize: '14px', margin: 0}}>
            Welcome back, {user?.name}! 🛍️
          </p>
        </div>
        
        <button
          onClick={() => setShowCreateForm(true)}
          style={{
            padding: '10px 20px',
            background: 'linear-gradient(to right, #10b981, #059669)',
            border: 'none',
            borderRadius: '8px',
            color: '#fff',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '14px',
            fontWeight: '600',
            transition: 'all 0.3s'
          }}
          onMouseEnter={(e) => {
            e.target.style.background = 'linear-gradient(to right, #34d399, #10b981)';
          }}
          onMouseLeave={(e) => {
            e.target.style.background = 'linear-gradient(to right, #10b981, #059669)';
          }}
        >
          <Plus size={18} />
          New List
        </button>
      </div>

      {showCreateForm && (
        <div style={{
          backgroundColor: '#1e293b',
          border: '1px solid #334155',
          borderRadius: '12px',
          padding: '20px',
          marginBottom: '24px'
        }}>
          <h3 style={{color: '#f1f5f9', marginBottom: '16px'}}>Create New Shopping List</h3>
          
          <div style={{marginBottom: '16px'}}>
            <input
              type="text"
              placeholder="List Name (e.g., Weekly Groceries)"
              value={newListName}
              onChange={(e) => setNewListName(e.target.value)}
              style={{
                width: '100%',
                padding: '12px',
                backgroundColor: '#0f172a',
                border: '1px solid #334155',
                borderRadius: '8px',
                color: '#f1f5f9',
                fontSize: '14px',
                outline: 'none'
              }}
            />
          </div>

          <div style={{marginBottom: '16px'}}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '12px'
            }}>
              <label style={{color: '#94a3b8', fontSize: '14px', fontWeight: '500'}}>
                Items
              </label>
              <button
                onClick={addItem}
                style={{
                  padding: '6px 12px',
                  background: 'transparent',
                  border: '1px solid #334155',
                  borderRadius: '6px',
                  color: '#10b981',
                  cursor: 'pointer',
                  fontSize: '12px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px'
                }}
              >
                <Plus size={14} />
                Add Item
              </button>
            </div>

            {items.map((item, index) => (
              <div key={index} style={{
                display: 'flex',
                gap: '12px',
                marginBottom: '8px',
                alignItems: 'center'
              }}>
                <input
                  type="text"
                  placeholder="Product name"
                  value={item.product_name}
                  onChange={(e) => updateItem(index, 'product_name', e.target.value)}
                  style={{
                    flex: 1,
                    padding: '8px 12px',
                    backgroundColor: '#0f172a',
                    border: '1px solid #334155',
                    borderRadius: '6px',
                    color: '#f1f5f9',
                    fontSize: '14px',
                    outline: 'none'
                  }}
                />
                <input
                  type="number"
                  min="1"
                  value={item.quantity}
                  onChange={(e) => updateItem(index, 'quantity', parseInt(e.target.value) || 1)}
                  style={{
                    width: '80px',
                    padding: '8px 12px',
                    backgroundColor: '#0f172a',
                    border: '1px solid #334155',
                    borderRadius: '6px',
                    color: '#f1f5f9',
                    fontSize: '14px',
                    outline: 'none'
                  }}
                />
                <button
                  onClick={() => removeItem(index)}
                  disabled={items.length === 1}
                  style={{
                    padding: '8px',
                    background: 'transparent',
                    border: '1px solid #334155',
                    borderRadius: '6px',
                    color: items.length === 1 ? '#475569' : '#ef4444',
                    cursor: items.length === 1 ? 'not-allowed' : 'pointer'
                  }}
                >
                  <Trash2 size={14} />
                </button>
              </div>
            ))}
          </div>

          <div style={{display: 'flex', gap: '12px', justifyContent: 'flex-end'}}>
            <button
              onClick={() => setShowCreateForm(false)}
              style={{
                padding: '10px 20px',
                background: 'transparent',
                border: '1px solid #334155',
                borderRadius: '8px',
                color: '#94a3b8',
                cursor: 'pointer',
                fontSize: '14px'
              }}
            >
              Cancel
            </button>
            <button
              onClick={handleCreateList}
              disabled={!newListName.trim() || !items.some(item => item.product_name.trim())}
              style={{
                padding: '10px 20px',
                background: !newListName.trim() || !items.some(item => item.product_name.trim()) 
                  ? '#334155' 
                  : 'linear-gradient(to right, #10b981, #059669)',
                border: 'none',
                borderRadius: '8px',
                color: '#fff',
                cursor: !newListName.trim() || !items.some(item => item.product_name.trim()) 
                  ? 'not-allowed' 
                  : 'pointer',
                fontSize: '14px',
                fontWeight: '600'
              }}
            >
              Create List
            </button>
          </div>
        </div>
      )}

      <div style={{
        display: 'grid',
        gap: '16px',
        gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))'
      }}>
        {shoppingLists.map((list) => (
          <div
            key={list.id}
            style={{
              backgroundColor: '#1e293b',
              border: '1px solid #334155',
              borderRadius: '12px',
              padding: '20px',
              cursor: 'pointer',
              transition: 'all 0.3s'
            }}
            onClick={() => onViewList(list)}
            onMouseEnter={(e) => {
              e.target.style.borderColor = '#10b981';
              e.target.style.transform = 'translateY(-2px)';
            }}
            onMouseLeave={(e) => {
              e.target.style.borderColor = '#334155';
              e.target.style.transform = 'translateY(0)';
            }}
          >
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'flex-start',
              marginBottom: '12px'
            }}>
              <h3 style={{
                color: '#f1f5f9',
                fontSize: '18px',
                fontWeight: '600',
                margin: 0
              }}>
                {list.name}
              </h3>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDeleteList(list.id);
                }}
                style={{
                  padding: '6px',
                  background: 'transparent',
                  border: 'none',
                  color: '#94a3b8',
                  cursor: 'pointer',
                  borderRadius: '4px'
                }}
                onMouseEnter={(e) => {
                  e.target.style.color = '#ef4444';
                  e.target.style.backgroundColor = 'rgba(239, 68, 68, 0.1)';
                }}
                onMouseLeave={(e) => {
                  e.target.style.color = '#94a3b8';
                  e.target.style.backgroundColor = 'transparent';
                }}
              >
                <Trash2 size={16} />
              </button>
            </div>

            <div style={{color: '#94a3b8', fontSize: '14px', marginBottom: '16px'}}>
              Created: {new Date(list.created_at).toLocaleDateString()}
            </div>

            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <div style={{display: 'flex', alignItems: 'center', gap: '8px'}}>
                <Package size={14} color="#94a3b8" />
                <span style={{color: '#94a3b8', fontSize: '13px'}}>
                  {list.item_count || 0} items
                </span>
              </div>
              
              {list.purchased_count > 0 && (
                <div style={{display: 'flex', alignItems: 'center', gap: '4px'}}>
                  <CheckCircle size={14} color="#10b981" />
                  <span style={{color: '#10b981', fontSize: '13px'}}>
                    {list.purchased_count} purchased
                  </span>
                </div>
              )}
            </div>
          </div>
        ))}

        {shoppingLists.length === 0 && !showCreateForm && (
          <div style={{
            gridColumn: '1 / -1',
            textAlign: 'center',
            padding: '60px 20px',
            color: '#94a3b8'
          }}>
            <ShoppingCart size={48} style={{marginBottom: '16px', opacity: 0.5}} />
            <h3 style={{color: '#94a3b8', marginBottom: '8px'}}>No shopping lists yet</h3>
            <p>Create your first shopping list to start comparing prices!</p>
          </div>
        )}
      </div>
    </div>
  );
}

// List View Component
function ListView({ list, onRefreshPrices, onBack, user }) {
  const [newItem, setNewItem] = useState('');

  // Safe calculation for total savings
  const totalSavings = list?.items ? list.items.reduce((sum, item) => sum + (item.potential_savings_pkr || 0), 0) : 0;

  const addItem = async () => {
    if (newItem.trim() && list?.list_id) {
      try {
        await fetch(`${API_BASE}/cart/${list.list_id}/add-item?product_name=${encodeURIComponent(newItem)}&quantity=1`);
        setNewItem('');
        window.location.reload();
      } catch (err) {
        console.error('Failed to add item');
      }
    }
  };

  const markPurchased = async (itemId) => {
    try {
      await fetch(`${API_BASE}/cart/item/${itemId}/purchased`, { method: 'POST' });
      window.location.reload();
    } catch (err) {
      console.error('Failed to mark item as purchased');
    }
  };

  if (!list) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        padding: '60px 20px',
        color: '#94a3b8'
      }}>
        <Loader2 size={32} className="spin" />
        <span style={{marginLeft: '12px'}}>Loading list data...</span>
      </div>
    );
  }

  return (
    <div>
      {/* List Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        marginBottom: '24px'
      }}>
        <div>
          <h2 style={{
            fontSize: '24px',
            fontWeight: 'bold',
            color: '#f1f5f9',
            margin: '0 0 8px 0'
          }}>
            {list.list_name || 'Shopping List'}
          </h2>
          <div style={{color: '#94a3b8', fontSize: '14px'}}>
            Last updated: {list.optimization_timestamp ? new Date(list.optimization_timestamp).toLocaleString() : 'Loading...'}
          </div>
        </div>

        <div style={{display: 'flex', gap: '12px'}}>
          <button
            onClick={onRefreshPrices}
            style={{
              padding: '10px 20px',
              background: 'transparent',
              border: '1px solid #334155',
              borderRadius: '8px',
              color: '#f1f5f9',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontSize: '14px',
              transition: 'all 0.3s'
            }}
            onMouseEnter={(e) => {
              e.target.style.backgroundColor = '#1e293b';
              e.target.style.borderColor = '#10b981';
            }}
            onMouseLeave={(e) => {
              e.target.style.backgroundColor = 'transparent';
              e.target.style.borderColor = '#334155';
            }}
          >
            <RefreshCw size={16} />
            Refresh Prices
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '16px',
        marginBottom: '24px'
      }}>
        <div style={{
          backgroundColor: '#1e293b',
          border: '1px solid #334155',
          borderRadius: '12px',
          padding: '20px'
        }}>
          <div style={{color: '#94a3b8', fontSize: '14px', marginBottom: '8px'}}>Total Cost</div>
          <div style={{color: '#f1f5f9', fontSize: '24px', fontWeight: 'bold'}}>
            Rs. {(list.total_cart_cost_pkr || 0).toLocaleString()}
          </div>
          <div style={{color: '#94a3b8', fontSize: '12px'}}>
            ${(list.total_cart_cost_usd || 0).toLocaleString()}
          </div>
        </div>

        <div style={{
          backgroundColor: '#1e293b',
          border: '1px solid #334155',
          borderRadius: '12px',
          padding: '20px'
        }}>
          <div style={{color: '#94a3b8', fontSize: '14px', marginBottom: '8px'}}>Potential Savings</div>
          <div style={{color: '#10b981', fontSize: '24px', fontWeight: 'bold'}}>
            Rs. {totalSavings.toLocaleString()}
          </div>
          <div style={{color: '#94a3b8', fontSize: '12px'}}>By choosing cheapest options</div>
        </div>

        <div style={{
          backgroundColor: '#1e293b',
          border: '1px solid #334155',
          borderRadius: '12px',
          padding: '20px'
        }}>
          <div style={{color: '#94a3b8', fontSize: '14px', marginBottom: '8px'}}>Items</div>
          <div style={{color: '#f1f5f9', fontSize: '24px', fontWeight: 'bold'}}>
            {(list.items || []).length}
          </div>
          <div style={{color: '#94a3b8', fontSize: '12px'}}>In this list</div>
        </div>
      </div>

      {/* Add Item */}
      <div style={{
        backgroundColor: '#1e293b',
        border: '1px solid #334155',
        borderRadius: '12px',
        padding: '16px',
        marginBottom: '24px',
        display: 'flex',
        gap: '12px'
      }}>
        <input
          type="text"
          placeholder="Add new item..."
          value={newItem}
          onChange={(e) => setNewItem(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && addItem()}
          style={{
            flex: 1,
            padding: '12px',
            backgroundColor: '#0f172a',
            border: '1px solid #334155',
            borderRadius: '8px',
            color: '#f1f5f9',
            fontSize: '14px',
            outline: 'none'
          }}
        />
        <button
          onClick={addItem}
          disabled={!newItem.trim()}
          style={{
            padding: '12px 24px',
            background: !newItem.trim() ? '#334155' : 'linear-gradient(to right, #10b981, #059669)',
            border: 'none',
            borderRadius: '8px',
            color: '#fff',
            cursor: !newItem.trim() ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '14px',
            fontWeight: '600'
          }}
        >
          <Plus size={16} />
          Add
        </button>
      </div>

      {/* Items List */}
      <div style={{display: 'flex', flexDirection: 'column', gap: '16px'}}>
        {list.items && list.items.length > 0 ? (
          list.items.map((item) => (
            <div
              key={item.item_id}
              style={{
                backgroundColor: '#1e293b',
                border: '1px solid #334155',
                borderRadius: '12px',
                padding: '20px'
              }}
            >
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'flex-start',
                marginBottom: '16px'
              }}>
                <div style={{flex: 1}}>
                  <h3 style={{
                    color: '#f1f5f9',
                    fontSize: '18px',
                    fontWeight: '600',
                    margin: '0 0 8px 0'
                  }}>
                    {item.product_name}
                  </h3>
                  <div style={{color: '#94a3b8', fontSize: '14px'}}>
                    Quantity: {item.quantity}
                  </div>
                </div>

                <div style={{textAlign: 'right'}}>
                  <div style={{
                    color: '#10b981',
                    fontSize: '20px',
                    fontWeight: 'bold',
                    marginBottom: '4px'
                  }}>
                    Rs. {(item.total_cost_pkr || 0).toLocaleString()}
                  </div>
                  <div style={{color: '#94a3b8', fontSize: '12px'}}>
                    ${(item.total_cost_usd || 0).toLocaleString()}
                  </div>
                </div>
              </div>

              {/* Recommendations */}
              {item.recommendations && item.recommendations.length > 0 && (
                <div style={{
                  backgroundColor: '#0f172a',
                  border: '1px solid #334155',
                  borderRadius: '8px',
                  padding: '16px'
                }}>
                  <div style={{
                    color: '#94a3b8',
                    fontSize: '14px',
                    fontWeight: '600',
                    marginBottom: '12px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  }}>
                    <TrendingUp size={14} />
                    Top Recommendations
                  </div>

                  <div style={{display: 'flex', flexDirection: 'column', gap: '8px'}}>
                    {item.recommendations.map((rec, index) => (
                      <div
                        key={index}
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          padding: '12px',
                          backgroundColor: index === 0 ? 'rgba(16, 185, 129, 0.1)' : 'transparent',
                          border: index === 0 ? '1px solid #10b981' : '1px solid #334155',
                          borderRadius: '6px'
                        }}
                      >
                        <div style={{flex: 1}}>
                          <div style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px',
                            marginBottom: '4px'
                          }}>
                            <span style={{
                              color: index === 0 ? '#10b981' : '#94a3b8',
                              fontSize: '14px',
                              fontWeight: '600'
                            }}>
                              {rec.source}
                            </span>
                            {index === 0 && (
                              <span style={{
                                backgroundColor: '#10b981',
                                color: '#fff',
                                fontSize: '10px',
                                padding: '2px 6px',
                                borderRadius: '4px'
                              }}>
                                CHEAPEST
                              </span>
                            )}
                          </div>
                          <div style={{color: '#e2e8f0', fontSize: '13px'}}>
                            {rec.product_name}
                          </div>
                        </div>

                        <div style={{textAlign: 'right'}}>
                          <div style={{
                            color: index === 0 ? '#10b981' : '#f1f5f9',
                            fontSize: '16px',
                            fontWeight: '600',
                            marginBottom: '2px'
                          }}>
                            Rs. {(rec.price_pkr || 0).toLocaleString()}
                          </div>
                          <div style={{color: '#94a3b8', fontSize: '11px'}}>
                            ${(rec.price_usd || 0).toLocaleString()}
                          </div>
                        </div>

                        <a
                          href={rec.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          style={{
                            marginLeft: '12px',
                            padding: '6px',
                            backgroundColor: '#334155',
                            borderRadius: '4px',
                            color: '#94a3b8',
                            textDecoration: 'none',
                            display: 'flex',
                            alignItems: 'center'
                          }}
                          onMouseEnter={(e) => {
                            e.target.style.backgroundColor = '#475569';
                            e.target.style.color = '#f1f5f9';
                          }}
                          onMouseLeave={(e) => {
                            e.target.style.backgroundColor = '#334155';
                            e.target.style.color = '#94a3b8';
                          }}
                        >
                          <ExternalLink size={14} />
                        </a>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {item.potential_savings_pkr > 0 && (
                <div style={{
                  color: '#10b981',
                  fontSize: '13px',
                  marginTop: '12px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}>
                  <DollarSign size={14} />
                  Potential savings: Rs. {(item.potential_savings_pkr || 0).toLocaleString()} 
                  by choosing {item.recommendations?.[0]?.source || 'cheapest option'}
                </div>
              )}

              <button
                onClick={() => markPurchased(item.item_id)}
                style={{
                  marginTop: '16px',
                  padding: '8px 16px',
                  background: 'transparent',
                  border: '1px solid #334155',
                  borderRadius: '6px',
                  color: '#94a3b8',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  fontSize: '13px',
                  transition: 'all 0.3s'
                }}
                onMouseEnter={(e) => {
                  e.target.style.borderColor = '#10b981';
                  e.target.style.color = '#10b981';
                }}
                onMouseLeave={(e) => {
                  e.target.style.borderColor = '#334155';
                  e.target.style.color = '#94a3b8';
                }}
              >
                <CheckCircle size={14} />
                Mark as Purchased
              </button>
            </div>
          ))
        ) : (
          <div style={{
            textAlign: 'center',
            padding: '60px 20px',
            color: '#94a3b8'
          }}>
            <Package size={48} style={{marginBottom: '16px', opacity: 0.5}} />
            <h3 style={{color: '#94a3b8', marginBottom: '8px'}}>No items in this list</h3>
            <p>Add items above to start comparing prices!</p>
          </div>
        )}
      </div>
    </div>
  );
}

// Price Comparison Component
function PriceComparisonView({ user }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const searchPrices = async () => {
    if (!query.trim()) return;
    
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/compare?query=${encodeURIComponent(query)}&top_n=20`);
      const data = await response.json();
      if (data.success) {
        setResults(data.products);
      }
    } catch (err) {
      console.error('Search failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        marginBottom: '24px'
      }}>
        <div>
          <h2 style={{
            fontSize: '24px',
            fontWeight: 'bold',
            color: '#f1f5f9',
            margin: '0 0 8px 0'
          }}>
            Compare Prices
          </h2>
          <p style={{color: '#94a3b8', fontSize: '14px', margin: 0}}>
            Find the best deals across stores, {user?.name}! 🔍
          </p>
        </div>
      </div>

      {/* Search */}
      <div style={{
        backgroundColor: '#1e293b',
        border: '1px solid #334155',
        borderRadius: '12px',
        padding: '20px',
        marginBottom: '24px'
      }}>
        <div style={{display: 'flex', gap: '12px'}}>
          <input
            type="text"
            placeholder="Search for products (e.g., iPhone 14, Samsung TV)..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && searchPrices()}
            style={{
              flex: 1,
              padding: '12px 16px',
              backgroundColor: '#0f172a',
              border: '1px solid #334155',
              borderRadius: '8px',
              color: '#f1f5f9',
              fontSize: '14px',
              outline: 'none'
            }}
          />
          <button
            onClick={searchPrices}
            disabled={!query.trim() || loading}
            style={{
              padding: '12px 24px',
              background: (!query.trim() || loading) ? '#334155' : 'linear-gradient(to right, #10b981, #059669)',
              border: 'none',
              borderRadius: '8px',
              color: '#fff',
              cursor: (!query.trim() || loading) ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontSize: '14px',
              fontWeight: '600'
            }}
          >
            {loading ? <Loader2 size={16} className="spin" /> : <Search size={16} />}
            Search
          </button>
        </div>
      </div>

      {/* Results */}
      {results.length > 0 && (
        <div>
          <div style={{
            color: '#94a3b8',
            fontSize: '14px',
            marginBottom: '16px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            <Package size={16} />
            Found {results.length} products for "{query}"
          </div>

          <div style={{display: 'flex', flexDirection: 'column', gap: '12px'}}>
            {results.map((product, index) => (
              <div
                key={index}
                style={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #334155',
                  borderRadius: '12px',
                  padding: '16px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}
              >
                <div style={{flex: 1}}>
                  <div style={{
                    color: '#f1f5f9',
                    fontSize: '16px',
                    fontWeight: '600',
                    marginBottom: '4px'
                  }}>
                    {product.name}
                  </div>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  }}>
                    <span style={{
                      backgroundColor: product.source === 'Daraz' ? '#ff6b35' : '#3b82f6',
                      color: '#fff',
                      fontSize: '11px',
                      padding: '2px 8px',
                      borderRadius: '4px'
                    }}>
                      {product.source}
                    </span>
                    <a
                      href={product.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{
                        color: '#94a3b8',
                        fontSize: '12px',
                        textDecoration: 'none',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px'
                      }}
                      onMouseEnter={(e) => {
                        e.target.style.color = '#10b981';
                      }}
                      onMouseLeave={(e) => {
                        e.target.style.color = '#94a3b8';
                      }}
                    >
                      View Product
                      <ExternalLink size={12} />
                    </a>
                  </div>
                </div>

                <div style={{textAlign: 'right'}}>
                  <div style={{
                    color: '#10b981',
                    fontSize: '18px',
                    fontWeight: 'bold',
                    marginBottom: '2px'
                  }}>
                    Rs. {(product.price_pkr || 0).toLocaleString()}
                  </div>
                  <div style={{color: '#94a3b8', fontSize: '12px'}}>
                    ${(product.price_usd || 0).toLocaleString()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {results.length === 0 && query && !loading && (
        <div style={{
          textAlign: 'center',
          padding: '60px 20px',
          color: '#94a3b8'
        }}>
          <Search size={48} style={{marginBottom: '16px', opacity: 0.5}} />
          <h3 style={{color: '#94a3b8', marginBottom: '8px'}}>No products found</h3>
          <p>Try searching for different products or check your spelling</p>
        </div>
      )}
    </div>
  );
}