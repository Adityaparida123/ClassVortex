"use client";

import { useCallback, useEffect, useRef } from "react";
import type { JSAnimation } from "animejs";
import { prefersReducedMotion } from "@/lib/utils";

/**
 * Returns a helper to run anime.js animations tied to the component lifecycle.
 * All animations are cleaned up on unmount and disabled under reduced-motion.
 */
export function useAnime() {
  const active = useRef<JSAnimation[]>([]);

  useEffect(() => {
    const current = active.current;
    return () => {
      current.forEach((anim) => anim.revert?.());
    };
  }, []);

  const track = useCallback((anim: JSAnimation) => {
    active.current.push(anim);
    anim.then?.(() => {
      active.current = active.current.filter((a) => a !== anim);
    });
    return anim;
  }, []);

  const disabled = prefersReducedMotion();

  return { track, disabled };
}
