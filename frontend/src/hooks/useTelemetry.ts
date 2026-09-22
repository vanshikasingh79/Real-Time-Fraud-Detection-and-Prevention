"use client";

import { useEffect, useRef, useState, type RefObject } from "react";

export interface BrowserTelemetry {
  typing_speed_wpm: number;
  paste_event_count: number;
  mouse_jitter_score: number;
  session_duration_seconds: number;
}

const MOUSE_SAMPLE_INTERVAL_MS = 50;
const MAX_TYPING_SPEED_WPM = 300;

function clamp(value: number, minimum: number, maximum: number): number {
  return Math.min(Math.max(value, minimum), maximum);
}

function calculateTypingSpeed(keystrokes: number, startedAt: number | null): number {
  if (keystrokes === 0 || startedAt === null) {
    return 0;
  }

  const elapsedMinutes = (Date.now() - startedAt) / 60000;
  if (elapsedMinutes <= 0) {
    return 0;
  }

  return clamp(keystrokes / 5 / elapsedMinutes, 0, MAX_TYPING_SPEED_WPM);
}

export function useTelemetry<T extends HTMLElement>(): {
  formRef: RefObject<T | null>;
  telemetry: BrowserTelemetry;
  getTelemetry: () => BrowserTelemetry;
} {
  const formRef = useRef<T | null>(null);
  const sessionStartedAt = useRef<number | null>(null);
  const typingStartedAt = useRef<number | null>(null);
  const keystrokeCount = useRef(0);
  const pasteEventCount = useRef(0);
  const lastMouseSampleAt = useRef(0);
  const lastMousePosition = useRef<{ x: number; y: number } | null>(null);
  const previousMouseAngle = useRef<number | null>(null);
  const mouseSampleCount = useRef(0);
  const mouseDirectionChanges = useRef(0);
  const [telemetry, setTelemetry] = useState<BrowserTelemetry>({
    typing_speed_wpm: 0,
    paste_event_count: 0,
    mouse_jitter_score: 0,
    session_duration_seconds: 0,
  });

  useEffect(() => {
    const element = formRef.current;
    if (!element) {
      return;
    }

    sessionStartedAt.current = Date.now();

    const readTelemetry = (): BrowserTelemetry => {
      const sessionDuration = sessionStartedAt.current
        ? Math.max(0, (Date.now() - sessionStartedAt.current) / 1000)
        : 0;
      const movementSegments = mouseSampleCount.current - 1;
      const directionChangeRate =
        movementSegments > 0
          ? mouseDirectionChanges.current / movementSegments
          : 0;

      return {
        typing_speed_wpm: calculateTypingSpeed(
          keystrokeCount.current,
          typingStartedAt.current,
        ),
        paste_event_count: pasteEventCount.current,
        // This is the proportion of sampled movement segments that changed
        // direction by more than 30 degrees, normalized to the backend range.
        mouse_jitter_score: clamp(directionChangeRate, 0, 1),
        session_duration_seconds: sessionDuration,
      };
    };

    const publishTelemetry = () => {
      setTelemetry(readTelemetry());
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.ctrlKey || event.metaKey || event.altKey || event.key.length !== 1) {
        return;
      }

      if (typingStartedAt.current === null) {
        typingStartedAt.current = Date.now();
      }
      keystrokeCount.current += 1;
      publishTelemetry();
    };

    const handlePaste = () => {
      // Count the event only; clipboard contents are intentionally never read.
      pasteEventCount.current += 1;
      publishTelemetry();
    };

    const handleMouseMove = (event: MouseEvent) => {
      const now = Date.now();
      if (now - lastMouseSampleAt.current < MOUSE_SAMPLE_INTERVAL_MS) {
        return;
      }
      lastMouseSampleAt.current = now;

      const previousPosition = lastMousePosition.current;
      lastMousePosition.current = { x: event.clientX, y: event.clientY };
      if (!previousPosition) {
        publishTelemetry();
        return;
      }

      const deltaX = event.clientX - previousPosition.x;
      const deltaY = event.clientY - previousPosition.y;
      if (deltaX === 0 && deltaY === 0) {
        return;
      }

      const angle = Math.atan2(deltaY, deltaX);
      if (previousMouseAngle.current !== null) {
        let angleDelta = Math.abs(angle - previousMouseAngle.current);
        if (angleDelta > Math.PI) {
          angleDelta = 2 * Math.PI - angleDelta;
        }
        if (angleDelta > Math.PI / 6) {
          mouseDirectionChanges.current += 1;
        }
      }
      previousMouseAngle.current = angle;
      mouseSampleCount.current += 1;
      publishTelemetry();
    };

    const durationTimer = window.setInterval(publishTelemetry, 1000);
    element.addEventListener("keydown", handleKeyDown);
    element.addEventListener("paste", handlePaste);
    element.addEventListener("mousemove", handleMouseMove);

    return () => {
      window.clearInterval(durationTimer);
      element.removeEventListener("keydown", handleKeyDown);
      element.removeEventListener("paste", handlePaste);
      element.removeEventListener("mousemove", handleMouseMove);
    };
  }, []);

  const getTelemetry = (): BrowserTelemetry => {
    const sessionDuration = sessionStartedAt.current
      ? Math.max(0, (Date.now() - sessionStartedAt.current) / 1000)
      : 0;
    const movementSegments = mouseSampleCount.current - 1;
    const directionChangeRate =
      movementSegments > 0
        ? mouseDirectionChanges.current / movementSegments
        : 0;

    return {
      typing_speed_wpm: calculateTypingSpeed(
        keystrokeCount.current,
        typingStartedAt.current,
      ),
      paste_event_count: pasteEventCount.current,
      mouse_jitter_score: clamp(directionChangeRate, 0, 1),
      session_duration_seconds: sessionDuration,
    };
  };

  return { formRef, telemetry, getTelemetry };
}
