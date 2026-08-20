/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_GOOGLE_CLIENT_ID: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

// Google Identity Services SDK global types
interface GoogleCredentialResponse {
  credential: string;
  select_by: string;
  clientId?: string;
}

interface GoogleIdConfiguration {
  client_id: string;
  callback: (response: GoogleCredentialResponse) => void;
  auto_select?: boolean;
  cancel_on_tap_outside?: boolean;
  context?: string;
  itp_support?: boolean;
  ux_mode?: 'popup' | 'redirect';
}

interface GoogleAccountsId {
  initialize: (config: GoogleIdConfiguration) => void;
  prompt: (momentListener?: (notification: any) => void) => void;
  renderButton: (parent: HTMLElement, options: any) => void;
  disableAutoSelect: () => void;
  cancel: () => void;
}

interface GoogleAccounts {
  id: GoogleAccountsId;
}

interface Google {
  accounts: GoogleAccounts;
}

declare global {
  interface Window {
    google?: Google;
  }
}
