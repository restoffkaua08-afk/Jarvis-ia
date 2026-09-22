import React, { useEffect, useState, useRef } from 'react';
import { motion } from 'motion/react';

export type VoiceAgentState = 'Idle' | 'Listening' | 'Thinking' | 'Speaking';

interface ReactiveSphereProps {
  state: VoiceAgentState;
  amplitude?: number;
}

export function ReactiveSphere({ state, amplitude = 0 }: ReactiveSphereProps) {
  const [scale, setScale] = useState(1);
  const requestRef = useRef<number>();

  useEffect(() => {
    const animate = () => {
      if (state === 'Listening') {
        // Contract when user speaks: scale decreases as amplitude increases
        // Base 1.0, drops toward 0.7 as amplitude hits 1.0
        const targetScale = 1 - amplitude * 0.3;
        setScale(targetScale);
      } else if (state === 'Speaking') {
        // Expand/Pulse when AI speaks: scale increases with amplitude
        const targetScale = 1 + amplitude * 0.5;
        setScale(targetScale);
      } else if (state === 'Thinking') {
        // Subtle pulse while thinking
        const pulse = 1 + Math.sin(Date.now() / 500) * 0.05;
        setScale(pulse);
      } else {
        setScale(1);
      }
      requestRef.current = requestAnimationFrame(animate);
    };

    requestRef.current = requestAnimationFrame(animate);
    return () => {
      if (requestRef.current) cancelAnimationFrame(requestRef.current);
    };
  }, [state, amplitude]);

  const getColor = () => {
    switch (state) {
      case 'Listening': return 'bg-blue-500';
      case 'Thinking': return 'bg-purple-500';
      case 'Speaking': return 'bg-green-500';
      default: return 'bg-slate-400';
    }
  };

  return (
    <div className="relative flex items-center justify-center w-64 h-64">
      <motion.div
        animate={{ scale }}
        transition={{ type: 'spring', stiffness: 300, damping: 20 }}
        className={`w-32 h-32 rounded-full blur-xl opacity-50 absolute ${getColor()}`}
      />
      <motion.div
        animate={{ scale }}
        transition={{ type: 'spring', stiffness: 300, damping: 20 }}
        className={`w-24 h-24 rounded-full shadow-2xl ${getColor()} border-4 border-white/20`}
      />
    </div>
  );
}
