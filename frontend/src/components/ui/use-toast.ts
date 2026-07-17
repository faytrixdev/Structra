"use client"

import { useState, useCallback } from "react"

const TOAST_LIMIT = 1
const TOAST_REMOVE_DELAY = 1000000

type ToasterToast = {
  id: string
  title?: string
  description?: string
  action?: React.ReactNode
  variant?: "default" | "destructive"
}

let count = 0
function genId() {
  count = (count + 1) % Number.MAX_SAFE_INTEGER
  return count.toString()
}

type Toast = ToasterToast

const toasts: Toast[] = []

type Action =
  | { type: "ADD_TOAST"; toast: ToasterToast }
  | { type: "UPDATE_TOAST"; toast: Partial<ToasterToast> }
  | { type: "DISMISS_TOAST"; toastId?: ToasterToast["id"] }
  | { type: "REMOVE_TOAST"; toastId?: ToasterToast["id"] }

let listeners: Array<(state: Toast[]) => void> = []

function dispatch(action: Action) {
  switch (action.type) {
    case "ADD_TOAST":
      toasts.push(action.toast)
      break
    case "DISMISS_TOAST":
    case "REMOVE_TOAST":
      break
  }
  listeners.forEach((listener) => listener([...toasts]))
}

function toast({ title, description, variant, ...props }: Omit<ToasterToast, "id">) {
  const id = genId()
  dispatch({ type: "ADD_TOAST", toast: { ...props, id, title, description, variant } })
  return { id, dismiss: () => dispatch({ type: "DISMISS_TOAST", toastId: id }), update: (p: Toast) => dispatch({ type: "UPDATE_TOAST", toast: { ...p, id } }) }
}

function useToast() {
  const [state, setState] = useState<Toast[]>(toasts)

  const toastFn = useCallback((props: Omit<ToasterToast, "id">) => {
    const t = toast(props)
    return t
  }, [])

  return { toasts: state, toast: toastFn, dismiss: (toastId?: string) => dispatch({ type: "DISMISS_TOAST", toastId }) }
}

export { useToast, toast }
