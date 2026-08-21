// src/components/AuthModal.tsx
import React, { useState } from 'react';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onLoginSuccess: (user: { email: string; name: string }) => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({
  isOpen,
  onClose,
  onLoginSuccess,
}) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [error, setError] = useState('');
  const [view, setView] = useState<'signin' | 'signup' | 'forgot'>('signin');
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  if (!isOpen) return null;

  const handleEmailSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const res = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({
          username: email,
          password: password,
        }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Sign in failed. Check credentials.');
      }

      const tokenData = await res.json();
      localStorage.setItem('access_token', tokenData.access_token);
      localStorage.setItem('refresh_token', tokenData.refresh_token);

      // Fetch user profile info
      const meRes = await fetch('/api/v1/auth/me', {
        headers: { Authorization: `Bearer ${tokenData.access_token}` },
      });

      if (!meRes.ok) throw new Error('Failed to retrieve user profile.');

      const meData = await meRes.json();
      onLoginSuccess({
        email: meData.email,
        name: meData.name || meData.email.split('@')[0],
      });
      resetForm();
    } catch (err: any) {
      setError(err.message || 'An error occurred during sign in.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleEmailSignUp = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const regRes = await fetch('/api/v1/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: email,
          password: password,
          name: name,
        }),
      });

      if (!regRes.ok) {
        const data = await regRes.json();
        throw new Error(data.detail || 'Registration failed.');
      }

      // Auto login after successful sign up
      const loginRes = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({
          username: email,
          password: password,
        }),
      });

      if (!loginRes.ok) throw new Error('Auto login failed. Proceed to Sign In.');

      const tokenData = await loginRes.json();
      localStorage.setItem('access_token', tokenData.access_token);
      localStorage.setItem('refresh_token', tokenData.refresh_token);

      onLoginSuccess({
        email: email,
        name: name || email.split('@')[0],
      });
      resetForm();
    } catch (err: any) {
      setError(err.message || 'An error occurred during registration.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleCredentialResponse = async (response: any) => {
    setError('');
    setIsLoading(true);

    try {
      const res = await fetch('/api/v1/auth/google', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: response.credential }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Google authentication failed.');
      }

      const tokenData = await res.json();
      localStorage.setItem('access_token', tokenData.access_token);
      localStorage.setItem('refresh_token', tokenData.refresh_token);

      const meRes = await fetch('/api/v1/auth/me', {
        headers: { Authorization: `Bearer ${tokenData.access_token}` },
      });

      if (!meRes.ok) throw new Error('Failed to retrieve user profile.');

      const meData = await meRes.json();
      onLoginSuccess({
        email: meData.email,
        name: meData.name || meData.email.split('@')[0],
      });
      resetForm();
    } catch (err: any) {
      setError(err.message || 'An error occurred during Google sign in.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleOAuthClick = async (provider: 'google' | 'github' | 'metamask') => {
    setError('');
    if (provider === 'metamask') {
      alert('MetaMask authentication is a simulated feature for demo purposes.');
      onLoginSuccess({ email: 'web3_researcher@avm.net', name: 'AVM Scholar' });
      onClose();
      return;
    }

    if (provider === 'github') {
      alert('GitHub authentication is a simulated feature for demo purposes.');
      onLoginSuccess({ email: 'github_academic@avm.net', name: 'Git Scholar' });
      onClose();
      return;
    }

    // Google Auth Flow
    const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
    if (!clientId) {
      setError('Google Sign-In is not configured. Please set VITE_GOOGLE_CLIENT_ID.');
      return;
    }

    if (!window.google?.accounts?.id) {
      setError('Google Sign-In SDK is still loading. Please try again in a moment.');
      return;
    }

    try {
      window.google.accounts.id.initialize({
        client_id: clientId,
        callback: handleGoogleCredentialResponse,
        auto_select: false,
        cancel_on_tap_outside: true,
        context: 'signin',
        ux_mode: 'popup',
      });
      window.google.accounts.id.prompt((notification: any) => {
        if (notification.isNotDisplayed() || notification.isSkippedMoment()) {
          const btnContainer = document.getElementById('google-signin-btn');
          if (btnContainer) {
            window.google!.accounts.id.renderButton(btnContainer, {
              theme: 'outline',
              size: 'large',
              width: '100%',
              text: 'signin_with',
              shape: 'rectangular',
            });
          }
        }
      });
    } catch (err) {
      setError('Failed to initialize Google Sign-In. Please try again.');
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
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs transition-all"
      onClick={handleBackdropClick}
    >
      <div className="relative w-full max-w-md mx-4 bg-[#0D1626] rounded-xl shadow-2xl border border-[#1B2536] overflow-hidden animate-fade-in-down text-[#E5E7EB] p-6 space-y-6">
        {/* Close Button */}
        <button
          onClick={() => { onClose(); resetForm(); }}
          className="absolute top-4 right-4 text-zinc-400 hover:text-white transition-colors p-1.5 rounded-lg hover:bg-zinc-900 z-10 outline-none"
        >
          <span className="material-symbols-outlined text-[18px]">close</span>
        </button>

        {/* Header */}
        <div className="space-y-1">
          <div className="flex items-center gap-2.5">
            <span className="material-symbols-outlined text-primary text-[24px]">science</span>
            <span className="text-[18px] font-bold text-white tracking-tight">Research Lab</span>
          </div>
          <p className="text-[12px] text-zinc-400">
            {view === 'signin' && 'Sign in to access Deep Research mode and save your reports.'}
            {view === 'signup' && 'Create an account to unlock all research capabilities.'}
            {view === 'forgot' && 'Enter your email and we\'ll send a reset link.'}
          </p>
        </div>

        {/* OAuth Providers */}
        {view !== 'forgot' && (
          <div className="space-y-2">
            <button
              onClick={() => handleOAuthClick('google')}
              disabled={isLoading}
              className="w-full flex items-center justify-center gap-2.5 px-4 py-2 bg-[#070B13] border border-[#1B2536] rounded-lg hover:border-zinc-700 hover:bg-zinc-900 transition-all text-[13px] font-medium text-white cursor-pointer disabled:opacity-50 outline-none"
            >
              <svg width="16" height="16" viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg" className="shrink-0">
                <path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844a4.14 4.14 0 01-1.796 2.716v2.259h2.908c1.702-1.567 2.684-3.875 2.684-6.615z" fill="#4285F4"/>
                <path d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 009 18z" fill="#34A853"/>
                <path d="M3.964 10.71A5.41 5.41 0 013.682 9c0-.593.102-1.17.282-1.71V4.958H.957A8.997 8.997 0 000 9c0 1.452.348 2.827.957 4.042l3.007-2.332z" fill="#FBBC05"/>
                <path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 00.957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58z" fill="#EA4335"/>
              </svg>
              Continue with Google
            </button>
            <div id="google-signin-btn" className="w-full" />

            <button
              onClick={() => handleOAuthClick('github')}
              disabled={isLoading}
              className="w-full flex items-center justify-center gap-2.5 px-4 py-2 bg-[#24292f] border border-[#24292f] rounded-lg hover:bg-[#32383f] transition-all text-[13px] font-medium text-white cursor-pointer disabled:opacity-50 outline-none"
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="white" xmlns="http://www.w3.org/2000/svg" className="shrink-0">
                <path fillRule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>
              </svg>
              Continue with GitHub
            </button>

            <button
              onClick={() => handleOAuthClick('metamask')}
              disabled={isLoading}
              className="w-full flex items-center justify-center gap-2.5 px-4 py-2 bg-[#070B13] border border-[#1B2536] rounded-lg hover:border-zinc-700 hover:bg-zinc-900 transition-all text-[13px] font-medium text-white cursor-pointer disabled:opacity-50 outline-none"
            >
              <span className="text-[16px] shrink-0">🦊</span>
              Continue with MetaMask
            </button>

            {/* Divider */}
            <div className="flex items-center gap-3 py-1">
              <div className="flex-1 h-px bg-[#1B2536]" />
              <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider">or</span>
              <div className="flex-1 h-px bg-[#1B2536]" />
            </div>
          </div>
        )}

        {/* Email/Password Form */}
        <div>
          {error && (
            <div className="mb-4 px-3 py-2 bg-red-900/20 border border-red-500/20 rounded-lg text-[12px] text-red-400 flex items-center gap-2">
              <span className="material-symbols-outlined text-[16px]">error</span>
              {error}
            </div>
          )}

          {view === 'signin' && (
            <form onSubmit={handleEmailSignIn} className="space-y-4">
              <div>
                <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest block mb-1.5">Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="w-full px-3 py-2 bg-[#070B13] border border-[#1B2536] rounded-lg text-[13px] text-white placeholder-zinc-600 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all"
                  required
                />
              </div>
              <div>
                <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest block mb-1.5">Password</label>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full px-3 py-2 bg-[#070B13] border border-[#1B2536] rounded-lg text-[13px] text-white placeholder-zinc-600 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all pr-10"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-white transition-colors outline-none"
                  >
                    <span className="material-symbols-outlined text-[16px]">{showPassword ? 'visibility_off' : 'visibility'}</span>
                  </button>
                </div>
              </div>

              <div className="flex justify-end">
                <button
                  type="button"
                  onClick={() => setView('forgot')}
                  className="text-[12px] text-primary hover:underline cursor-pointer outline-none font-semibold"
                >
                  Forgot password?
                </button>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-2 bg-primary text-white rounded-lg text-[13px] font-semibold hover:bg-blue-600 transition-all disabled:opacity-50 cursor-pointer mt-1"
              >
                {isLoading ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="material-symbols-outlined animate-spin text-[16px]">progress_activity</span>
                    Signing in...
                  </span>
                ) : 'Sign In'}
              </button>

              <p className="text-center text-[12px] text-zinc-400 mt-4">
                Don't have an account?{' '}
                <button type="button" onClick={() => setView('signup')} className="text-primary font-bold hover:underline cursor-pointer outline-none">
                  Sign Up
                </button>
              </p>
            </form>
          )}

          {view === 'signup' && (
            <form onSubmit={handleEmailSignUp} className="space-y-4">
              <div>
                <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest block mb-1.5">Full Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Jane Doe"
                  className="w-full px-3 py-2 bg-[#070B13] border border-[#1B2536] rounded-lg text-[13px] text-white placeholder-zinc-600 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all"
                  required
                />
              </div>
              <div>
                <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest block mb-1.5">Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="w-full px-3 py-2 bg-[#070B13] border border-[#1B2536] rounded-lg text-[13px] text-white placeholder-zinc-600 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all"
                  required
                />
              </div>
              <div>
                <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest block mb-1.5">Password</label>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Min. 8 characters"
                    className="w-full px-3 py-2 bg-[#070B13] border border-[#1B2536] rounded-lg text-[13px] text-white placeholder-zinc-600 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all pr-10"
                    minLength={8}
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-white transition-colors outline-none"
                  >
                    <span className="material-symbols-outlined text-[16px]">{showPassword ? 'visibility_off' : 'visibility'}</span>
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-2 bg-primary text-white rounded-lg text-[13px] font-semibold hover:bg-blue-600 transition-all disabled:opacity-50 cursor-pointer mt-2"
              >
                {isLoading ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="material-symbols-outlined animate-spin text-[16px]">progress_activity</span>
                    Creating account...
                  </span>
                ) : 'Create Account'}
              </button>

              <p className="text-center text-[12px] text-zinc-400 mt-4">
                Already have an account?{' '}
                <button type="button" onClick={() => setView('signin')} className="text-primary font-bold hover:underline cursor-pointer outline-none">
                  Sign In
                </button>
              </p>
            </form>
          )}

          {view === 'forgot' && (
            <form onSubmit={(e) => { e.preventDefault(); setError(''); setView('signin'); }} className="space-y-4">
              <div>
                <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest block mb-1.5">Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="w-full px-3 py-2 bg-[#070B13] border border-[#1B2536] rounded-lg text-[13px] text-white placeholder-zinc-600 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all"
                  required
                />
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-2 bg-primary text-white rounded-lg text-[13px] font-semibold hover:bg-blue-600 transition-all disabled:opacity-50 cursor-pointer mt-2"
              >
                Send Reset Link
              </button>

              <p className="text-center text-[12px] text-zinc-400 mt-4">
                <button type="button" onClick={() => setView('signin')} className="text-primary font-bold hover:underline cursor-pointer outline-none">
                  ← Back to Sign In
                </button>
              </p>
            </form>
          )}

          {/* Terms */}
          {view !== 'forgot' && (
            <p className="text-center text-[10px] text-zinc-500 mt-5 leading-relaxed">
              By continuing, you agree to our{' '}
              <a href="#" className="underline hover:text-zinc-400">Terms of Service</a> and{' '}
              <a href="#" className="underline hover:text-zinc-400">Privacy Policy</a>
            </p>
          )}
        </div>

        {/* Loading overlay */}
        {isLoading && (
          <div className="absolute inset-0 bg-[#0D1626]/85 backdrop-blur-[1px] flex items-center justify-center rounded-xl">
            <div className="flex flex-col items-center gap-2">
              <span className="material-symbols-outlined animate-spin text-primary text-[28px]">progress_activity</span>
              <span className="text-[12px] text-zinc-300 font-medium">Authenticating...</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
