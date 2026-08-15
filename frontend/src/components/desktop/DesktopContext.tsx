"use client";

import { createContext, useCallback, useContext, useMemo, useState } from "react";

export type AppId = "ipod" | "gameboy";

type Ctx = {
  open: Record<AppId, boolean>;
  /** which app owns the keyboard — only one at a time */
  focused: AppId | null;
  toggle: (id: AppId) => void;
  close: (id: AppId) => void;
  launch: (id: AppId) => void;
  focus: (id: AppId) => void;
};

const DesktopCtx = createContext<Ctx | null>(null);

export function DesktopProvider({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = useState<Record<AppId, boolean>>({
    ipod: false,
    gameboy: false,
  });
  const [focused, setFocused] = useState<AppId | null>(null);

  /* Opening or touching an app gives it the keyboard. Without this both
     devices listen on window at once, so steering Snake with the arrows also
     scrubs the iPod playlist and Space pauses the music. */
  const toggle = useCallback((id: AppId) => {
    setOpen((o) => {
      const next = !o[id];
      setFocused((f) => (next ? id : f === id ? null : f));
      return { ...o, [id]: next };
    });
  }, []);

  const close = useCallback((id: AppId) => {
    setOpen((o) => ({ ...o, [id]: false }));
    setFocused((f) => (f === id ? null : f));
  }, []);

  const launch = useCallback((id: AppId) => {
    setOpen((o) => ({ ...o, [id]: true }));
    setFocused(id);
  }, []);

  const focus = useCallback((id: AppId) => setFocused(id), []);

  const value = useMemo(
    () => ({ open, focused, toggle, close, launch, focus }),
    [open, focused, toggle, close, launch, focus],
  );

  return <DesktopCtx.Provider value={value}>{children}</DesktopCtx.Provider>;
}

export function useDesktop() {
  const c = useContext(DesktopCtx);
  if (!c) throw new Error("useDesktop must be used inside <DesktopProvider>");
  return c;
}
