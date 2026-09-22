import { ChatArea } from '../components/Chat/ChatArea';
import { SystemPanel } from '../components/Chat/SystemPanel';
import { useAppStore } from '../lib/store';
import { ReactiveSphere } from '../components/ReactiveSphere';
import { useVoiceAgent } from '../hooks/useVoiceAgent';
import { Mic } from 'lucide-react';

export function ChatPage() {
  const systemPanelOpen = useAppStore((s) => s.systemPanelOpen);
  const { state, amplitude, startListening, stopListening } = useVoiceAgent();

  return (
    <div className="flex h-full overflow-hidden relative">
      <div className="flex-1 min-w-0">
        <ChatArea />
      </div>
      {systemPanelOpen && <SystemPanel />}

      {/* Voice OS Overlay */}
      <div className="absolute inset-0 pointer-events-none flex flex-col items-center justify-center z-10">
        <div className="pointer-events-auto">
          <ReactiveSphere state={state} amplitude={amplitude} />
        </div>
      </div>

      {/* Mic Indicator */}
      <div className="absolute top-4 right-4 z-20">
        <button
          onClick={state === 'Idle' ? startListening : stopListening}
          className={`p-3 rounded-full transition-colors ${
            state === 'Listening' ? 'bg-red-500 text-white animate-pulse' : 'bg-slate-800 text-slate-300'
          }`}
        >
          <Mic size={20} />
        </button>
      </div>
    </div>
  );
}
