import React, { useState, useRef, useEffect } from "react";

export interface TooltipProps {
  content: React.ReactNode;
  title?: string;
  code?: string;
  children: React.ReactNode;
  position?: "top" | "bottom" | "left" | "right";
  className?: string;
  delayMs?: number;
}

export const Tooltip: React.FC<TooltipProps> = ({
  content,
  title,
  code,
  children,
  position = "top",
  className = "",
  delayMs = 100,
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const timeoutRef = useRef<any>(null);

  const show = () => {
    timeoutRef.current = setTimeout(() => {
      setIsVisible(true);
    }, delayMs);
  };

  const hide = () => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    setIsVisible(false);
  };

  useEffect(() => {
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, []);

  // Position coordinates & arrows
  const positionClasses = {
    top: "bottom-full left-1/2 -translate-x-1/2 mb-2.5",
    bottom: "top-full left-1/2 -translate-x-1/2 mt-2.5",
    left: "right-full top-1/2 -translate-y-1/2 mr-2.5",
    right: "left-full top-1/2 -translate-y-1/2 ml-2.5",
  }[position];

  const arrowClasses = {
    top: "top-full left-1/2 -translate-x-1/2 border-t-[#1B2540] border-l-transparent border-r-transparent border-b-transparent border-[5px]",
    bottom: "bottom-full left-1/2 -translate-x-1/2 border-b-[#1B2540] border-l-transparent border-r-transparent border-t-transparent border-[5px]",
    left: "left-full top-1/2 -translate-y-1/2 border-l-[#1B2540] border-t-transparent border-b-transparent border-r-transparent border-[5px]",
    right: "right-full top-1/2 -translate-y-1/2 border-r-[#1B2540] border-t-transparent border-b-transparent border-l-transparent border-[5px]",
  }[position];

  return (
    <div
      className={`relative inline-flex items-center ${className}`}
      onMouseEnter={show}
      onMouseLeave={hide}
      onFocus={show}
      onBlur={hide}
    >
      {children}

      {isVisible && (
        <div
          role="tooltip"
          className={`absolute z-50 pointer-events-none transition-all duration-150 animate-in fade-in zoom-in-95 ${positionClasses}`}
          style={{ minWidth: "160px", maxWidth: "280px" }}
        >
          <div className="p-2.5 rounded-lg bg-[#1B2540] border border-[#3FC7D4]/30 shadow-2xl backdrop-blur-xl text-left">
            {(title || code) && (
              <div className="flex items-center justify-between gap-2 pb-1 mb-1 border-b border-[#3FC7D4]/15">
                {title && (
                  <span className="font-display font-bold text-[11px] text-[#E7ECF5] tracking-wide uppercase">
                    {title}
                  </span>
                )}
                {code && (
                  <span className="font-mono text-[10px] text-[#3FC7D4] bg-[#3FC7D4]/15 px-1.5 py-0.5 rounded border border-[#3FC7D4]/30 font-semibold">
                    {code}
                  </span>
                )}
              </div>
            )}
            <div className="text-[11px] font-sans text-[#C2CCD9] leading-relaxed">
              {content}
            </div>
          </div>
          <div className={`absolute w-0 h-0 ${arrowClasses}`} />
        </div>
      )}
    </div>
  );
};
