"use client";

import { useState, type ReactNode } from "react";
import { useDraggable } from "./useDraggable";

let zTop = 30;

/**
 * Wraps any desktop object so it can be picked up and dropped anywhere.
 * Keeps the element's existing CSS position and applies a translate delta,
 * and raises it above its siblings when grabbed.
 */
export default function Draggable({
  children,
  className = "",
  clamp = false,
  title = "drag me",
  onGrab,
}: {
  children: ReactNode;
  className?: string;
  clamp?: boolean;
  title?: string;
  /** fired when the object is touched — used to hand it the keyboard */
  onGrab?: () => void;
}) {
  const { dragging, handlers, style } = useDraggable({ clampToViewport: clamp });
  const [z, setZ] = useState<number | undefined>();

  return (
    <div
      {...handlers}
      onPointerDownCapture={() => {
        setZ(++zTop);
        onGrab?.();
      }}
      title={title}
      className={`select-none ${dragging ? "cursor-grabbing" : "cursor-grab"} ${className}`}
      style={{
        ...style,
        zIndex: z,
        transition: dragging ? "none" : "box-shadow .18s ease",
        filter: dragging
          ? "drop-shadow(0 24px 34px rgba(0,0,0,.34))"
          : undefined,
      }}
    >
      {children}
    </div>
  );
}
