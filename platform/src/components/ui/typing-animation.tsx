"use client";

import { useEffect, useState } from "react";

import { cn } from "@/lib/utils";

interface TypingAnimationProps {
  text: string;
  duration?: number;
  className?: string;
  /** When true, renders as inline span for use within sentences */
  inline?: boolean;
}

export function TypingAnimation({
  text,
  duration = 200,
  className,
  inline = false,
}: TypingAnimationProps) {
  const [displayedText, setDisplayedText] = useState<string>("");
  const [i, setI] = useState<number>(0);

  useEffect(() => {
    setDisplayedText("");
    setI(0);
  }, [text]);

  useEffect(() => {
    let typingEffect: ReturnType<typeof setInterval>;
    typingEffect = setInterval(() => {
      setI((prev) => {
        if (prev < text.length) {
          setDisplayedText(text.substring(0, prev + 1));
          return prev + 1;
        }
        clearInterval(typingEffect);
        return prev;
      });
    }, duration);

    return () => {
      clearInterval(typingEffect);
    };
  }, [duration, text]);

  const content = displayedText;

  if (inline) {
    return (
      <span className={cn("inline", className)}>
        {content}
      </span>
    );
  }

  return (
    <h1
      className={cn(
        "font-display text-center text-4xl font-bold leading-[5rem] tracking-[-0.02em] drop-shadow-sm",
        className,
      )}
    >
      {content}
    </h1>
  );
}
