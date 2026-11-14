import React, { useEffect, useId, useRef, useState } from "react";
import { DialogCloseIcon } from "../icon-pack.jsx";

function Dialog({ title, children, footer, onClose, size = "md", busy = false, initialFocus, returnFocus }) {
  const titleId = useId();
  const panelRef = useRef(null);
  const closeRef = useRef(onClose);
  const busyRef = useRef(busy);
  const [previousFocus] = useState(() => returnFocus || document.activeElement);
  closeRef.current = onClose;
  busyRef.current = busy;

  useEffect(() => {
    const panel = panelRef.current;
    const focusable = () => [...panel.querySelectorAll('button:not(:disabled), input:not(:disabled), select:not(:disabled), textarea:not(:disabled), a[href], [tabindex="0"]')].filter((node) => node.getClientRects().length);
    const focusTimer = window.requestAnimationFrame(() => {
      const initialControl = initialFocus && panel.querySelector(initialFocus);
      if (initialControl) initialControl.focus();
      else if (!panel.contains(document.activeElement)) (focusable()[0] || panel).focus();
    });
    function onKeyDown(event) {
      const dialogs = document.querySelectorAll('[role="dialog"]');
      if (dialogs[dialogs.length - 1] !== panel) return;
      if (event.key === "Escape") {
        event.preventDefault();
        event.stopPropagation();
        if (!busyRef.current) closeRef.current?.();
      }
      if (event.key === "Tab") {
        const controls = focusable();
        const first = controls[0] || panel;
        const last = controls[controls.length - 1] || panel;
        if (!controls.length || !panel.contains(document.activeElement) || (event.shiftKey && document.activeElement === first) || (!event.shiftKey && document.activeElement === last)) {
          event.preventDefault();
          (event.shiftKey ? last : first).focus();
        }
      }
    }
    window.addEventListener("keydown", onKeyDown, true);
    return () => {
      window.cancelAnimationFrame(focusTimer);
      window.removeEventListener("keydown", onKeyDown, true);
      if (previousFocus?.isConnected) previousFocus.focus();
    };
  }, [initialFocus, previousFocus]);

  function onBackdropMouseDown(event) {
    if (event.target === event.currentTarget && !busy) {
      closeRef.current?.();
    }
  }

  return (
    <div className="dialog-backdrop" onMouseDown={onBackdropMouseDown}>
      <section
        ref={panelRef}
        tabIndex={-1}
        className={`dialog-panel dialog-${size}`}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-busy={busy}
        onMouseDown={(event) => event.stopPropagation()}
      >
        <header className="dialog-header">
          <h3 id={titleId} className="dialog-title">{title}</h3>
          <button type="button" className="dialog-close" onClick={onClose} disabled={busy} aria-label="Close dialog">
            <DialogCloseIcon />
          </button>
        </header>
        <div className="dialog-content">{children}</div>
        {footer ? <footer className="dialog-actions">{footer}</footer> : null}
      </section>
    </div>
  );
}

export default Dialog;
