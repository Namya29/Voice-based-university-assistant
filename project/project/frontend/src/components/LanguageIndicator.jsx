const NAMES = {
  "en-US": "English",
  "hi-IN": "Hindi",
  "es-ES": "Spanish",
  "fr-FR": "French",
  "ar-SA": "Arabic",
  "zh-CN": "Chinese",
};

export default function LanguageIndicator({ language, verified }) {
  return (
    <span className={`lang-badge ${verified ? "lang-badge--verified" : "lang-badge--unverified"}`}>
      {NAMES[language] || language} {verified ? "· Verified source" : "· Unverified"}
    </span>
  );
}
