import React, { useState, useEffect, useCallback } from 'react';

// Google Client ID — must match backend GOOGLE_CLIENT_ID
const GOOGLE_CLIENT_ID = '474511502741-ftafb9rf41sia9i40uja5fj1higolm6v.apps.googleusercontent.com';

// API base — proxied by Vite in dev
const API_BASE = '/api/v1';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onLoginSuccess: (user: { email: string; name: string }) => void;
}

type AuthView = 'signin' | 'signup' | 'forgot';

// Extend window for Google Identity Services
declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: any) => void;
          renderButton: (element: HTMLElement, config: any) => void;
          prompt: () => void;
          cancel: () => void;
        };
      };
    };
  }
}

export const AuthModal: React.FC<AuthModalProps> = ({ isOpen, onClose, onLoginSuccess }) => {
  const [view, setView] = useState<AuthView>('signin');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  // Load Google Identity Services script
  useEffect(() => {
    if (document.getElementById('google-gsi-script')) return;
    const script = document.createElement('script');
    script.id = 'google-gsi-script';
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    document.head.appendChild(script);
  }, []);

  // Handle Google credential response
  const handleGoogleCredentialResponse = useCallback(async (response: any) => {
    setIsLoading(true);
    setError('');
    try {
      const res = await fetch(`${API_BASE}/auth/google`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id_token: response.credential }),
      });
      const data = await res.json();

      if (!res.ok || !data.success) {
        setError(data.message || 'Google authentication failed.');
        setIsLoading(false);
        return;
      }

      // Store Larp tokens — same as email/password login
      const tokenData = data.data;
      localStorage.setItem('access_token', tokenData.access_token);
      localStorage.setItem('refresh_token', tokenData.refresh_token);

      // Fetch user profile using the Larp token
      const meRes = await fetch(`${API_BASE}/auth/me`, {
        headers: { 'Authorization': `Bearer ${tokenData.access_token}` },
      });

      let userName = '';
      let userEmail = '';
      if (meRes.ok) {
        const meData = await meRes.json();
        if (meData.success && meData.data) {
          userName = meData.data.full_name || meData.data.email?.split('@')[0] || '';
          userEmail = meData.data.email || '';
        }
      }

      // If /auth/me didn't work, decode basic info from response
      if (!userEmail) {
        // Parse the JWT to get the user ID (we don't have email in the token)
        // Fall back to using the Google credential info
        try {
          const payload = JSON.parse(atob(response.credential.split('.')[1]));
          userEmail = payload.email || '';
          userName = payload.name || userEmail.split('@')[0];
        } catch {
          userEmail = 'google-user';
          userName = 'Google User';
        }
      }

      onLoginSuccess({ email: userEmail, name: userName });
      resetForm();
    } catch (err: any) {
      setError(err.message || 'Google authentication failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  }, [onLoginSuccess]);

  // Initialize Google button when modal opens and GSI is loaded
  useEffect(() => {
    if (!isOpen || view === 'forgot') return;

    const initializeGoogle = () => {
      if (!window.google?.accounts?.id) return;

      window.google.accounts.id.initialize({
        client_id: GOOGLE_CLIENT_ID,
        callback: handleGoogleCredentialResponse,
        auto_select: false,
        cancel_on_tap_outside: true,
      });

      // Render the Google button into our container
      const buttonContainer = document.getElementById('google-signin-button');
      if (buttonContainer) {
        buttonContainer.innerHTML = '';
        window.google.accounts.id.renderButton(buttonContainer, {
          type: 'standard',
          theme: 'outline',
          size: 'large',
          width: '100%',
          text: 'continue_with',
          shape: 'rectangular',
          logo_alignment: 'left',
        });
      }
    };

    // Try immediately, then retry after script loads
    initializeGoogle();
    const interval = setInterval(() => {
      if (window.google?.accounts?.id) {
        initializeGoogle();
        clearInterval(interval);
      }
    }, 200);

    return () => clearInterval(interval);
  }, [isOpen, view, handleGoogleCredentialResponse]);

  if (!isOpen) return null;

  const handleEmailSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();

      if (!res.ok || !data.success) {
        setError(data.message || 'Invalid email or password.');
        setIsLoading(false);
        return;
      }

      const tokenData = data.data;
      localStorage.setItem('access_token', tokenData.access_token);
      localStorage.setItem('refresh_token', tokenData.refresh_token);

      onLoginSuccess({ email, name: email.split('@')[0] });
      resetForm();
    } catch (err: any) {
      setError(err.message || 'Login failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleEmailSignUp = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, full_name: name }),
      });
      const data = await res.json();

      if (!res.ok || !data.success) {
        setError(data.message || 'Registration failed.');
        setIsLoading(false);
        return;
      }

      // Auto-login after registration
      const loginRes = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      const loginData = await loginRes.json();

      if (loginRes.ok && loginData.success) {
        const tokenData = loginData.data;
        localStorage.setItem('access_token', tokenData.access_token);
        localStorage.setItem('refresh_token', tokenData.refresh_token);
      }

      onLoginSuccess({ email, name });
      resetForm();
    } catch (err: any) {
      setError(err.message || 'Registration failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const resetForm = () => {
    setEmail('');
    setPassword('');
    setName('');
    setError('');
    setView('signin');
    setIsLoading(false);
  };

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
      resetForm();
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm transition-all"
      onClick={handleBackdropClick}
    >
      <div className="relative w-full max-w-md mx-4 bg-surface rounded-xl shadow-2xl border border-outline-variant overflow-hidden animate-fade-in-down">
        {/* Close Button */}
        <button
          onClick={() => { onClose(); resetForm(); }}
          className="absolute top-4 right-4 text-on-surface-variant hover:text-on-surface transition-colors p-1 rounded-full hover:bg-surface-variant z-10"
        >
          <span className="material-symbols-outlined text-[20px]">close</span>
        </button>

        {/* Header */}
        <div className="px-8 pt-8 pb-4">
          <div className="flex items-center gap-2.5 mb-1">
            <span className="material-symbols-outlined text-primary text-[28px] fill-1">science</span>
            <span className="text-[22px] font-bold text-on-surface tracking-tight">Research Lab</span>
          </div>
          <p className="text-[14px] text-on-surface-variant mt-1">
            {view === 'signin' && 'Sign in to access Deep Research mode and save your reports.'}
            {view === 'signup' && 'Create an account to unlock all research capabilities.'}
            {view === 'forgot' && 'Enter your email and we\'ll send a reset link.'}
          </p>
        </div>

        {/* OAuth Providers */}
        {view !== 'forgot' && (
          <div className="px-8 space-y-2.5">
            {/* Real Google Sign-In button rendered by GSI */}
            <div
              id="google-signin-button"
              className="w-full flex items-center justify-center min-h-[44px]"
            />

            <button
              disabled={isLoading}
              className="w-full flex items-center justify-center gap-3 px-4 py-2.5 bg-[#24292f] border border-[#24292f] rounded-lg hover:bg-[#32383f] transition-all text-[14px] font-medium text-white cursor-pointer disabled:opacity-50"
            >
              <svg width="18" height="18" viewBox="0 0 16 16" fill="white" xmlns="http://www.w3.org/2000/svg">
                <path fillRule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>
              </svg>
              Continue with GitHub
            </button>

            <button
              disabled={isLoading}
              className="w-full flex items-center justify-center gap-3 px-4 py-2.5 bg-surface border border-outline-variant rounded-lg hover:bg-surface-container-low transition-all text-[14px] font-medium text-on-surface cursor-pointer disabled:opacity-50"
            >
              <span className="text-[18px]">🦊</span>
              Continue with MetaMask
            </button>

            {/* Divider */}
            <div className="flex items-center gap-3 py-2">
              <div className="flex-1 h-px bg-outline-variant" />
              <span className="text-[12px] text-on-surface-variant font-medium uppercase tracking-wider">or</span>
              <div className="flex-1 h-px bg-outline-variant" />
            </div>
          </div>
        )}

        {/* Email/Password Form */}
        <div className="px-8 pb-8">
          {error && (
            <div className="mb-4 px-3 py-2 bg-error-container rounded-lg text-[13px] text-on-error-container flex items-center gap-2">
              <span className="material-symbols-outlined text-[16px]">error</span>
              {error}
            </div>
          )}

          {view === 'signin' && (
            <form onSubmit={handleEmailSignIn} className="space-y-3">
              <div>
                <label className="text-[12px] font-semibold text-on-surface-variant uppercase tracking-wider block mb-1">Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="w-full px-3 py-2.5 bg-surface-container-low border border-outline-variant rounded-lg text-[14px] text-on-surface placeholder-outline focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all"
                  required
                />
              </div>
              <div>
                <label className="text-[12px] font-semibold text-on-surface-variant uppercase tracking-wider block mb-1">Password</label>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full px-3 py-2.5 bg-surface-container-low border border-outline-variant rounded-lg text-[14px] text-on-surface placeholder-outline focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all pr-10"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-on-surface-variant hover:text-on-surface transition-colors"
                  >
                    <span className="material-symbols-outlined text-[18px]">{showPassword ? 'visibility_off' : 'visibility'}</span>
                  </button>
                </div>
              </div>

              <div className="flex justify-end">
                <button
                  type="button"
                  onClick={() => setView('forgot')}
                  className="text-[13px] text-primary hover:underline cursor-pointer"
                >
                  Forgot password?
                </button>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-2.5 bg-primary text-on-primary rounded-lg text-[14px] font-semibold hover:opacity-90 transition-all disabled:opacity-50 cursor-pointer mt-1"
              >
                {isLoading ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="material-symbols-outlined animate-spin text-[18px]">progress_activity</span>
                    Signing in...
                  </span>
                ) : 'Sign In'}
              </button>

              <p className="text-center text-[13px] text-on-surface-variant mt-4">
                Don't have an account?{' '}
                <button type="button" onClick={() => setView('signup')} className="text-primary font-semibold hover:underline cursor-pointer">
                  Sign Up
                </button>
              </p>
            </form>
          )}

          {view === 'signup' && (
            <form onSubmit={handleEmailSignUp} className="space-y-3">
              <div>
                <label className="text-[12px] font-semibold text-on-surface-variant uppercase tracking-wider block mb-1">Full Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Jane Doe"
                  className="w-full px-3 py-2.5 bg-surface-container-low border border-outline-variant rounded-lg text-[14px] text-on-surface placeholder-outline focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all"
                  required
                />
              </div>
              <div>
                <label className="text-[12px] font-semibold text-on-surface-variant uppercase tracking-wider block mb-1">Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="w-full px-3 py-2.5 bg-surface-container-low border border-outline-variant rounded-lg text-[14px] text-on-surface placeholder-outline focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all"
                  required
                />
              </div>
              <div>
                <label className="text-[12px] font-semibold text-on-surface-variant uppercase tracking-wider block mb-1">Password</label>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Min. 8 characters"
                    className="w-full px-3 py-2.5 bg-surface-container-low border border-outline-variant rounded-lg text-[14px] text-on-surface placeholder-outline focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all pr-10"
                    minLength={8}
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-on-surface-variant hover:text-on-surface transition-colors"
                  >
                    <span className="material-symbols-outlined text-[18px]">{showPassword ? 'visibility_off' : 'visibility'}</span>
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-2.5 bg-primary text-on-primary rounded-lg text-[14px] font-semibold hover:opacity-90 transition-all disabled:opacity-50 cursor-pointer mt-2"
              >
                {isLoading ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="material-symbols-outlined animate-spin text-[18px]">progress_activity</span>
                    Creating account...
                  </span>
                ) : 'Create Account'}
              </button>

              <p className="text-center text-[13px] text-on-surface-variant mt-4">
                Already have an account?{' '}
                <button type="button" onClick={() => setView('signin')} className="text-primary font-semibold hover:underline cursor-pointer">
                  Sign In
                </button>
              </p>
            </form>
          )}

          {view === 'forgot' && (
            <form onSubmit={(e) => { e.preventDefault(); setError(''); setView('signin'); }} className="space-y-3">
              <div>
                <label className="text-[12px] font-semibold text-on-surface-variant uppercase tracking-wider block mb-1">Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="w-full px-3 py-2.5 bg-surface-container-low border border-outline-variant rounded-lg text-[14px] text-on-surface placeholder-outline focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all"
                  required
                />
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-2.5 bg-primary text-on-primary rounded-lg text-[14px] font-semibold hover:opacity-90 transition-all disabled:opacity-50 cursor-pointer mt-2"
              >
                Send Reset Link
              </button>

              <p className="text-center text-[13px] text-on-surface-variant mt-4">
                <button type="button" onClick={() => setView('signin')} className="text-primary font-semibold hover:underline cursor-pointer">
                  ← Back to Sign In
                </button>
              </p>
            </form>
          )}

          {/* Terms */}
          {view !== 'forgot' && (
            <p className="text-center text-[11px] text-outline mt-5 leading-relaxed">
              By continuing, you agree to our{' '}
              <a href="#" className="underline hover:text-on-surface-variant">Terms of Service</a> and{' '}
              <a href="#" className="underline hover:text-on-surface-variant">Privacy Policy</a>
            </p>
          )}
        </div>

        {/* Loading overlay */}
        {isLoading && (
          <div className="absolute inset-0 bg-surface/60 backdrop-blur-[2px] flex items-center justify-center rounded-xl">
            <div className="flex flex-col items-center gap-2">
              <span className="material-symbols-outlined animate-spin text-primary text-[32px]">progress_activity</span>
              <span className="text-[13px] text-on-surface-variant font-medium">Authenticating...</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
