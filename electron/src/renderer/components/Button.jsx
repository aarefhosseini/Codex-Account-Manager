import React, { useRef, useState } from "react";
import { useToast } from "./ToastProvider.jsx";

const variantClassByName = {
  primary: "btn-primary",
  secondary: "btn-secondary",
  danger: "btn-danger",
  dangerOutline: "btn-danger-outline",
  ghost: "btn-ghost",
  icon: "btn-icon",
  warning: "btn-warning",
};

function Button({
  children,
  variant = "secondary",
  loading = false,
  disabled = false,
  disabledReason = "",
  className = "",
  type = "button",
  onClick,
  ...props
}) {
  const [pending, setPending] = useState(false);
  const pendingRef = useRef(false);
  const { showToast } = useToast();
  async function handleClick(event) {
    if (pendingRef.current || loading || disabled) return;
    try {
      const result = onClick?.(event);
      if (result && typeof result.then === "function") {
        pendingRef.current = true;
        setPending(true);
        await result;
      }
    } catch (error) {
      showToast({ tone: "error", title: "Action failed", description: error?.message || String(error) });
    } finally {
      pendingRef.current = false;
      setPending(false);
    }
  }
  const variantClass = variantClassByName[variant] || "";
  const classes = [
    "btn",
    variantClass,
    loading || pending ? "btn-progress" : "",
    className,
  ].filter(Boolean).join(" ");
  const title = disabled && disabledReason ? disabledReason : props.title;

  return (
    <button
      {...props}
      type={type}
      className={classes}
      disabled={disabled || loading || pending}
      aria-busy={loading || pending}
      onClick={handleClick}
      title={title}
    >
      {children}
    </button>
  );
}

export default Button;
