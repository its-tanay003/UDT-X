import React, { useEffect, useRef, useState } from "react";
import { motion, useSpring, useTransform } from "framer-motion";

interface AnimatedNumberProps {
  value: number;
  decimals?: number;
  formatter?: (val: number) => string;
  className?: string;
  flashOnUpdate?: boolean;
}

export const AnimatedNumber: React.FC<AnimatedNumberProps> = ({
  value,
  decimals = 0,
  formatter,
  className = "",
  flashOnUpdate = true,
}) => {
  const prevValueRef = useRef(value);
  const [isFlashing, setIsFlashing] = useState(false);

  // Smooth spring physics for counting up/down
  const spring = useSpring(value, {
    stiffness: 75,
    damping: 15,
    restDelta: 0.001,
  });

  const display = useTransform(spring, (current) => {
    if (formatter) {
      return formatter(current);
    }
    return decimals > 0
      ? current.toFixed(decimals)
      : Math.round(current).toLocaleString();
  });

  useEffect(() => {
    spring.set(value);

    if (flashOnUpdate && prevValueRef.current !== value) {
      setIsFlashing(true);
      const timer = setTimeout(() => setIsFlashing(false), 600);
      prevValueRef.current = value;
      return () => clearTimeout(timer);
    }
    prevValueRef.current = value;
  }, [value, spring, flashOnUpdate]);

  return (
    <motion.span
      className={`inline-block transition-colors duration-300 ${
        isFlashing ? "text-[#3FC7D4] drop-shadow-[0_0_8px_rgba(63,199,212,0.8)]" : ""
      } ${className}`}
    >
      <motion.span>{display}</motion.span>
    </motion.span>
  );
};
