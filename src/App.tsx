import { type ReactNode, useState, useEffect, useRef } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ErrorBoundary } from '@/components/error-boundary';
import { Toaster } from '@/components/ui/toaster';
import { TooltipProvider } from '@/components/ui/tooltip';
import NotFound from '@/pages/not-found';
import { Route, Switch, useLocation, Router as WouterRouter } from 'wouter';
import { 
  Terminal, Shield, Lock, Unlock, FileJson, 
  ArrowRight, BookOpen, Clock, Activity, Loader2,
  CheckCircle2, XCircle, Trash2
} from 'lucide-react';

const queryClient = new QueryClient();

// API Configuration
// Use empty string to default to same host, or configure if needed.
const API_BASE = '';

type LogEntry = {
  id: string;
  time: string;
  method: string;
  url: string;
  status: number | null;
  duration: number;
  requestBody?: any;
  responseBody?: any;
  error?: string;
};

function AuthLab() {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('access_token'));
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isLoading, setIsLoading] = useState<Record<string, boolean>>({});
  const consoleRef = useRef<HTMLDivElement>(null);

  // Auto-scroll console
  useEffect(() => {
    if (consoleRef.current) {
      consoleRef.current.scrollTop = consoleRef.current.scrollHeight;
    }
  }, [logs]);

  // Sync token to localStorage
  useEffect(() => {
    if (token) {
      localStorage.setItem('access_token', token);
    } else {
      localStorage.removeItem('access_token');
    }
  }, [token]);

  const formatTime = () => {
    const now = new Date();
    return `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}.${now.getMilliseconds().toString().padStart(3, '0')}`;
  };

  const executeRequest = async (
    actionName: string, 
    method: string, 
    endpoint: string, 
    body?: any, 
    useAuth = false,
    isFormData = false
  ) => {
    setIsLoading(prev => ({ ...prev, [actionName]: true }));
    const startTime = performance.now();
    
    const headers: Record<string, string> = {};
    if (!isFormData && body) {
      headers['Content-Type'] = 'application/json';
    }
    if (useAuth && token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    let fetchOptions: RequestInit = {
      method,
      headers,
    };

    if (body) {
      if (isFormData) {
        const formData = new URLSearchParams();
        for (const [k, v] of Object.entries(body)) {
          formData.append(k, v as string);
        }
        fetchOptions.body = formData;
        headers['Content-Type'] = 'application/x-www-form-urlencoded';
      } else {
        fetchOptions.body = JSON.stringify(body);
      }
    }

    const log: LogEntry = {
      id: Math.random().toString(36).substring(2, 9),
      time: formatTime(),
      method,
      url: endpoint,
      status: null,
      duration: 0,
      requestBody: body
    };

    try {
      const res = await fetch(`${API_BASE}${endpoint}`, fetchOptions);
      const duration = Math.round(performance.now() - startTime);
      
      log.status = res.status;
      log.duration = duration;

      const text = await res.text();
      try {
        log.responseBody = JSON.parse(text);
      } catch {
        log.responseBody = text || null;
      }

      setLogs(prev => [...prev, log]);
      setIsLoading(prev => ({ ...prev, [actionName]: false }));
      
      return { status: res.status, data: log.responseBody };
    } catch (err: any) {
      const duration = Math.round(performance.now() - startTime);
      log.duration = duration;
      log.error = err.message || 'Network error';
      
      setLogs(prev => [...prev, log]);
      setIsLoading(prev => ({ ...prev, [actionName]: false }));
      
      return { status: 0, error: err.message };
    }
  };

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    await executeRequest('signup', 'POST', '/auth/signup', { email, password });
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    const res = await executeRequest('login', 'POST', '/auth/login', { email, password }, false, false);
    // Support either direct access_token or nested data
    const new_token = res.data?.access_token || res.data?.data?.access_token || res.data?.session?.access_token;
    if (res.status === 200 && new_token) {
      setToken(new_token);
    }
  };

  const handleLogout = async () => {
    await executeRequest('logout', 'POST', '/auth/logout', undefined, true);
    setToken(null);
  };

  const handleGetMe = () => executeRequest('me', 'GET', '/auth/me', undefined, true);
  const handleAdminCheck = () => executeRequest('admin', 'GET', '/auth/admin-check', undefined, true);
  const handleClearLogs = () => setLogs([]);

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col font-sans selection:bg-primary/30">
      {/* Header */}
      <header className="h-16 border-b border-border bg-card/50 backdrop-blur flex items-center justify-between px-6 sticky top-0 z-10">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-primary/10 flex items-center justify-center border border-primary/20 text-primary">
            <Shield className="w-4 h-4" />
          </div>
          <div>
            <h1 className="font-semibold text-sm tracking-tight">FlyRank Auth Lab</h1>
            <div className="text-xs text-muted-foreground flex items-center gap-1.5 mt-0.5">
              <div className={`w-1.5 h-1.5 rounded-full ${token ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.5)]' : 'bg-zinc-600'}`}></div>
              {token ? 'Authenticated Session' : 'Unauthenticated'}
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          <a href="/docs" target="_blank" className="text-sm text-muted-foreground hover:text-primary transition-colors flex items-center gap-2 px-3 py-1.5 rounded-md hover:bg-primary/10">
            <BookOpen className="w-4 h-4" />
            Swagger UI
          </a>
        </div>
      </header>

      <main className="flex-1 max-w-7xl w-full mx-auto p-4 md:p-6 grid grid-cols-1 lg:grid-cols-12 gap-6 h-auto lg:h-[calc(100vh-4rem)]">
        
        {/* Left Column: Controls */}
        <div className="lg:col-span-4 flex flex-col gap-6 lg:overflow-y-auto pr-0 lg:pr-2 pb-6 console-scrollbar">
          
          {/* Identity Card */}
          <div className="rounded-xl border border-border bg-card shadow-sm overflow-hidden flex flex-col">
            <div className="px-5 py-4 border-b border-border bg-muted/20 flex items-center gap-2">
              <Lock className="w-4 h-4 text-muted-foreground" />
              <h2 className="font-medium text-sm">Identity Management</h2>
            </div>
            
            <div className="p-5 flex flex-col gap-4">
              {token ? (
                <div className="flex flex-col gap-4">
                  <div className="p-4 rounded-lg bg-green-500/10 border border-green-500/20 text-sm">
                    <div className="flex items-center gap-2 text-green-500 font-medium mb-1">
                      <Unlock className="w-4 h-4" />
                      Session Active
                    </div>
                    <div className="text-muted-foreground font-mono text-xs break-all mt-2">
                      <span className="text-zinc-500 select-none">Token: </span>
                      {token.substring(0, 24)}...{token.substring(token.length - 8)}
                    </div>
                  </div>
                  
                  <button 
                    onClick={handleLogout}
                    disabled={isLoading['logout']}
                    className="w-full flex items-center justify-center gap-2 bg-secondary hover:bg-secondary/80 text-foreground py-2 px-4 rounded-md text-sm font-medium transition-colors disabled:opacity-50 border border-border"
                  >
                    {isLoading['logout'] ? <Loader2 className="w-4 h-4 animate-spin" /> : <Shield className="w-4 h-4" />}
                    Log Out
                  </button>
                </div>
              ) : (
                <form className="flex flex-col gap-4" onSubmit={(event) => event.preventDefault()}>
                  <div className="space-y-3">
                    <div>
                      <label className="block text-xs font-medium text-muted-foreground mb-1.5">Email Address</label>
                      <input 
                        type="email" 
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        autoComplete="email"
                        className="w-full bg-background border border-border rounded-md px-3 py-2 text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all placeholder:text-zinc-600"
                        placeholder="developer@flyrank.local"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-muted-foreground mb-1.5">Password</label>
                      <input 
                        type="password" 
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        autoComplete="current-password"
                        className="w-full bg-background border border-border rounded-md px-3 py-2 text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all placeholder:text-zinc-600"
                        placeholder="••••••••"
                      />
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-3 mt-2">
                    <button 
                      type="button"
                      onClick={handleSignup}
                      disabled={isLoading['signup'] || !email || !password}
                      className="flex items-center justify-center gap-2 bg-secondary hover:bg-secondary/80 text-foreground py-2 px-4 rounded-md text-sm font-medium transition-colors disabled:opacity-50 border border-border"
                    >
                      {isLoading['signup'] ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Sign Up'}
                    </button>
                    <button 
                      type="button"
                      onClick={handleLogin}
                      disabled={isLoading['login'] || !email || !password}
                      className="flex items-center justify-center gap-2 bg-primary hover:bg-primary/90 text-primary-foreground py-2 px-4 rounded-md text-sm font-medium transition-colors disabled:opacity-50"
                    >
                      {isLoading['login'] ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Log In'}
                    </button>
                  </div>
                </form>
              )}
            </div>
          </div>

          {/* Resources Card */}
          <div className="rounded-xl border border-border bg-card shadow-sm overflow-hidden flex flex-col">
            <div className="px-5 py-4 border-b border-border bg-muted/20 flex items-center gap-2">
              <Activity className="w-4 h-4 text-muted-foreground" />
              <h2 className="font-medium text-sm">Protected Resources</h2>
            </div>
            
            <div className="p-5 flex flex-col gap-3">
              <div className="flex flex-col gap-2">
                <div className="text-xs text-muted-foreground">Standard Protected Route</div>
                <button 
                  onClick={handleGetMe}
                  disabled={isLoading['me']}
                  className="flex items-center justify-between w-full bg-background hover:bg-muted border border-border py-2.5 px-3 rounded-md text-sm transition-colors group disabled:opacity-50 text-left"
                >
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-xs font-semibold text-primary bg-primary/10 px-1.5 py-0.5 rounded">GET</span>
                    <span className="font-mono text-xs">/auth/me</span>
                  </div>
                  {isLoading['me'] ? <Loader2 className="w-3.5 h-3.5 animate-spin text-muted-foreground" /> : <ArrowRight className="w-3.5 h-3.5 text-muted-foreground group-hover:text-foreground transition-colors" />}
                </button>
              </div>

              <div className="flex flex-col gap-2 mt-2">
                <div className="text-xs text-muted-foreground">Admin Protected Route</div>
                <button 
                  onClick={handleAdminCheck}
                  disabled={isLoading['admin']}
                  className="flex items-center justify-between w-full bg-background hover:bg-muted border border-border py-2.5 px-3 rounded-md text-sm transition-colors group disabled:opacity-50 text-left"
                >
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-xs font-semibold text-primary bg-primary/10 px-1.5 py-0.5 rounded">GET</span>
                    <span className="font-mono text-xs">/auth/admin-check</span>
                  </div>
                  {isLoading['admin'] ? <Loader2 className="w-3.5 h-3.5 animate-spin text-muted-foreground" /> : <ArrowRight className="w-3.5 h-3.5 text-muted-foreground group-hover:text-foreground transition-colors" />}
                </button>
              </div>
            </div>
          </div>
          
        </div>

        {/* Right Column: Console */}
        <div className="lg:col-span-8 flex flex-col rounded-xl border border-border bg-card shadow-sm overflow-hidden min-h-[500px] lg:min-h-0 lg:h-full">
          <div className="px-5 py-3 border-b border-border bg-muted/20 flex items-center justify-between shrink-0">
            <div className="flex items-center gap-2">
              <Terminal className="w-4 h-4 text-muted-foreground" />
              <h2 className="font-medium text-sm">Network Console</h2>
            </div>
            {logs.length > 0 && (
              <button 
                onClick={handleClearLogs}
                className="text-xs flex items-center gap-1.5 text-muted-foreground hover:text-foreground transition-colors"
              >
                <Trash2 className="w-3.5 h-3.5" />
                Clear
              </button>
            )}
          </div>
          
          <div 
            ref={consoleRef}
            className="flex-1 bg-[#09090b] p-4 overflow-y-auto console-scrollbar font-mono text-[13px] flex flex-col gap-4"
          >
            {logs.length === 0 ? (
              <div className="h-full flex items-center justify-center text-zinc-600 flex-col gap-3">
                <Terminal className="w-8 h-8 opacity-20" />
                <span>Waiting for network activity...</span>
              </div>
            ) : (
              logs.map((log) => (
                <div key={log.id} className="border border-zinc-800 rounded-lg bg-zinc-900/50 overflow-hidden flex flex-col animate-in fade-in slide-in-from-bottom-2 duration-300">
                  <div className="px-4 py-2 border-b border-zinc-800 flex flex-wrap items-center justify-between gap-4 bg-zinc-900">
                    <div className="flex items-center gap-3">
                      <span className={`font-semibold text-xs px-1.5 py-0.5 rounded ${
                        log.method === 'GET' ? 'bg-blue-500/10 text-blue-400' : 
                        log.method === 'POST' ? 'bg-green-500/10 text-green-400' : 
                        'bg-zinc-500/10 text-zinc-400'
                      }`}>
                        {log.method}
                      </span>
                      <span className="text-zinc-300">{log.url}</span>
                    </div>
                    
                    <div className="flex items-center gap-4 text-xs">
                      {log.status !== null ? (
                        <div className={`flex items-center gap-1.5 ${
                          log.status >= 200 && log.status < 300 ? 'text-green-400' :
                          log.status >= 400 ? 'text-red-400' : 'text-zinc-400'
                        }`}>
                          {log.status >= 200 && log.status < 300 ? <CheckCircle2 className="w-3.5 h-3.5" /> : 
                           log.status >= 400 ? <XCircle className="w-3.5 h-3.5" /> : <Activity className="w-3.5 h-3.5" />}
                          {log.status}
                        </div>
                      ) : (
                        <div className="text-red-400 flex items-center gap-1.5">
                          <XCircle className="w-3.5 h-3.5" />
                          Failed
                        </div>
                      )}
                      <div className="flex items-center gap-1.5 text-zinc-500">
                        <Clock className="w-3.5 h-3.5" />
                        {log.duration}ms
                      </div>
                      <div className="text-zinc-600 hidden sm:block">{log.time}</div>
                    </div>
                  </div>
                  
                  <div className="p-4 flex flex-col gap-3">
                    {log.requestBody && (
                      <div>
                        <div className="text-xs text-zinc-500 mb-1.5 flex items-center gap-1.5">
                          <ArrowRight className="w-3 h-3" /> Request Payload
                        </div>
                        <pre className="bg-black/40 rounded border border-zinc-800 p-3 text-zinc-300 overflow-x-auto">
                          {JSON.stringify(log.requestBody, null, 2)}
                        </pre>
                      </div>
                    )}
                    
                    {(log.responseBody || log.error) && (
                      <div>
                        <div className="text-xs text-zinc-500 mb-1.5 flex items-center gap-1.5">
                          <FileJson className="w-3 h-3" /> Response
                        </div>
                        <pre className={`bg-black/40 rounded border border-zinc-800 p-3 overflow-x-auto ${log.error ? 'text-red-400' : 'text-zinc-300'}`}>
                          {log.error || (typeof log.responseBody === 'string' ? log.responseBody : JSON.stringify(log.responseBody, null, 2))}
                        </pre>
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

      </main>
    </div>
  );
}

function Router() {
  return (
    <Switch>
      <Route path="/" component={AuthLab} />
      <Route component={NotFound} />
    </Switch>
  );
}

function RoutedErrorBoundary({ children }: { children: ReactNode }) {
  const [location] = useLocation();
  return <ErrorBoundary resetKey={location}>{children}</ErrorBoundary>;
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <WouterRouter base={import.meta.env.BASE_URL.replace(/\/$/, '')}>
          <RoutedErrorBoundary>
            <Router />
          </RoutedErrorBoundary>
        </WouterRouter>
        <Toaster />
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;
