import { useCallback, useRef, useState } from "react";
import * as SpeechSDK from "microsoft-cognitiveservices-speech-sdk";
import { getSpeechToken, getSupportedLanguages } from "../api/assistantApi";

export function useVoiceRecognizer() {
  const [status, setStatus] = useState("idle");
  const [transcript, setTranscript] = useState("");
  const [detectedLanguage, setDetectedLanguage] = useState(null);
  const [error, setError] = useState(null);

  const recognizerRef = useRef(null);
  const browserRecognizerRef = useRef(null);

  const start = useCallback(async (onFinalResult, preferredLanguage = "en-US") => {
    try {
      setError(null);
      setTranscript("");
      setDetectedLanguage(null);
      setStatus("listening");

      // Attempt Azure Speech SDK first
      let token = null;
      let region = null;
      try {
        const speechAuth = await getSpeechToken();
        token = speechAuth?.token;
        region = speechAuth?.region;
      } catch (authErr) {
        console.warn("Could not retrieve Azure Speech token, will try browser fallback:", authErr);
      }

      if (token && region) {
        const speechConfig = SpeechSDK.SpeechConfig.fromAuthorizationToken(token, region);
        const audioConfig = SpeechSDK.AudioConfig.fromDefaultMicrophoneInput();

        let recognizer = null;
        if (!preferredLanguage || preferredLanguage === "auto") {
          // Azure Speech SDK allows AT MOST 4 candidate languages for auto-detection
          const topCandidates = ["en-US", "hi-IN", "pa-IN", "es-ES"];
          const autoDetect = SpeechSDK.AutoDetectSourceLanguageConfig.fromLanguages(topCandidates);
          recognizer = SpeechSDK.SpeechRecognizer.FromConfig(speechConfig, autoDetect, audioConfig);
        } else {
          speechConfig.speechRecognitionLanguage = preferredLanguage;
          recognizer = SpeechSDK.SpeechRecognizer.FromConfig(speechConfig, audioConfig);
        }

        recognizerRef.current = recognizer;

        // Real-time live transcript
        recognizer.recognizing = (_sender, event) => {
          if (event?.result?.text) {
            setTranscript(event.result.text);
          }
        };

        // Final speech recognition result
        recognizer.recognized = (_sender, event) => {
          if (event.result.reason === SpeechSDK.ResultReason.RecognizedSpeech) {
            const text = event.result.text?.trim();
            if (!text) return;

            let lang = preferredLanguage && preferredLanguage !== "auto" ? preferredLanguage : "en-US";
            try {
              const langRes = SpeechSDK.AutoDetectSourceLanguageResult.fromResult(event.result);
              if (langRes?.language) lang = langRes.language;
            } catch {
              // Ignore if auto-detect result not present
            }

            setTranscript(text);
            setDetectedLanguage(lang);

            recognizer.stopContinuousRecognitionAsync(
              () => {
                setStatus("processing");
                if (recognizerRef.current) {
                  recognizer.close();
                  recognizerRef.current = null;
                }
                onFinalResult?.(text, lang);
              },
              () => {
                setStatus("processing");
                if (recognizerRef.current) {
                  recognizer.close();
                  recognizerRef.current = null;
                }
                onFinalResult?.(text, lang);
              }
            );
          }
        };

        recognizer.canceled = (_sender, event) => {
          console.warn("Azure speech recognition canceled or encountered notice:", event);
          if (event?.reason === SpeechSDK.CancellationReason.Error) {
            setError(event.errorDetails || "Speech recognition error");
            setStatus("error");
          } else {
            setStatus("idle");
          }
          if (recognizerRef.current) {
            recognizer.close();
            recognizerRef.current = null;
          }
        };

        recognizer.sessionStopped = () => {
          if (recognizerRef.current) {
            recognizerRef.current.close();
            recognizerRef.current = null;
          }
          setStatus((prev) => (prev === "listening" ? "idle" : prev));
        };

        recognizer.startContinuousRecognitionAsync(
          () => console.log("Azure Speech recognition started successfully"),
          (err) => {
            console.error("Could not start Azure Speech:", err);
            recognizer.close();
            recognizerRef.current = null;
            startBrowserFallback(onFinalResult, preferredLanguage);
          }
        );
        return;
      }

      // If no token or Azure fails, use browser Web Speech API fallback
      startBrowserFallback(onFinalResult, preferredLanguage);
    } catch (err) {
      console.warn("Azure Speech init failed, trying browser Web Speech API:", err);
      startBrowserFallback(onFinalResult, preferredLanguage);
    }
  }, []);

  const startBrowserFallback = (onFinalResult, preferredLanguage) => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setError("Microphone recognition is not supported in this browser. Please use text input.");
      setStatus("error");
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = (!preferredLanguage || preferredLanguage === "auto") ? "en-US" : preferredLanguage;

      browserRecognizerRef.current = recognition;

      recognition.onresult = (event) => {
        let interim = "";
        let final = "";
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            final += event.results[i][0].transcript;
          } else {
            interim += event.results[i][0].transcript;
          }
        }
        const currentText = final || interim;
        setTranscript(currentText);

        if (final.trim()) {
          setStatus("processing");
          onFinalResult?.(final.trim(), recognition.lang);
        }
      };

      recognition.onerror = (event) => {
        console.warn("Browser SpeechRecognition error:", event.error);
        if (event.error !== "no-speech") {
          setError(`Speech recognition: ${event.error}`);
          setStatus("error");
        } else {
          setStatus("idle");
        }
      };

      recognition.onend = () => {
        browserRecognizerRef.current = null;
        setStatus((prev) => (prev === "listening" ? "idle" : prev));
      };

      recognition.start();
      setStatus("listening");
    } catch (err) {
      console.error("Browser speech recognition failed to start:", err);
      setError("Could not access microphone. Please check browser permissions.");
      setStatus("error");
    }
  };

  const stop = useCallback(() => {
    if (recognizerRef.current) {
      recognizerRef.current.stopContinuousRecognitionAsync(
        () => {
          if (recognizerRef.current) {
            recognizerRef.current.close();
            recognizerRef.current = null;
          }
          setStatus("idle");
        },
        () => {
          if (recognizerRef.current) {
            recognizerRef.current.close();
            recognizerRef.current = null;
          }
          setStatus("idle");
        }
      );
    }

    if (browserRecognizerRef.current) {
      try {
        browserRecognizerRef.current.stop();
      } catch {
        // Ignore if already stopped
      }
      browserRecognizerRef.current = null;
      setStatus("idle");
    }

    if (!recognizerRef.current && !browserRecognizerRef.current) {
      setStatus("idle");
    }
  }, []);

  return {
    start,
    stop,
    status,
    transcript,
    detectedLanguage,
    error,
  };
}