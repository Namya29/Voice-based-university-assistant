const LOCALIZED_EXAMPLES = {
  "hi-IN": [
    { icon: "📚", label: "लाइब्रेरी टाइमिंग", question: "लाइब्रेरी कितने बजे से कितने बजे तक खुलती है?" },
    { icon: "📋", label: "अटेंडेंस नियम", question: "परीक्षा के लिए अनिवार्य उपस्थिति (अटेंडेंस) कितनी होनी चाहिए?" },
    { icon: "🏢", label: "हॉस्टल कर्फ्यू", question: "हॉस्टल में इन-टाइम कर्फ्यू का समय क्या है?" },
    { icon: "💳", label: "फीस की अंतिम तिथि", question: "सम सेमेस्टर की ट्यूशन फीस जमा करने की लास्ट डेट क्या है?" },
    { icon: "📝", label: "पासिंग मार्क्स", question: "परीक्षा पास करने के लिए न्यूनतम कितने प्रतिशत अंक चाहिए?" },
    { icon: "🔄", label: "ब्रांच चेंज", question: "फर्स्ट ईयर के बाद ब्रांच बदलने के लिए क्या नियम हैं?" },
  ],
  "pa-IN": [
    { icon: "📚", label: "ਲਾਇਬ੍ਰੇਰੀ ਸਮਾਂ", question: "ਸੈਂਟਰਲ ਲਾਇਬ੍ਰੇਰੀ ਕਦੋਂ ਖੁੱਲ੍ਹਦੀ ਹੈ ਅਤੇ ਕਦੋਂ ਬੰਦ ਹੁੰਦੀ ਹੈ?" },
    { icon: "📋", label: "ਹਾਜ਼ਰੀ ਨਿਯਮ", question: "ਇਮਤਿਹਾਨ ਲਈ ਕਿੰਨੇ ਪ੍ਰਤੀਸ਼ਤ ਹਾਜ਼ਰੀ ਲਾਜ਼ਮੀ ਹੈ?" },
    { icon: "🏢", label: "ਹੋਸਟਲ ਕਰਫਿਊ", question: "ਹੋਸਟਲ ਵਿਦਿਆਰਥੀਆਂ ਲਈ ਇਨ-ਟਾਈਮ ਕਰਫਿਊ ਕੀ ਹੈ?" },
    { icon: "💳", label: "ਫੀਸ ਦੀ ਮਿਤੀ", question: "ਈਵਨ ਸਮੈਸਟਰ ਦੀ ਟਿਊਸ਼ਨ ਫੀਸ ਦੀ ਆਖਰੀ ਮਿਤੀ ਕੀ ਹੈ?" },
    { icon: "📝", label: "ਪਾਸਿੰਗ ਮਾਰਕਸ", question: "ਇਮਤਿਹਾਨ ਪਾਸ ਕਰਨ ਲਈ ਕਿੰਨੇ ਅੰਕ ਚਾਹੀਦੇ ਹਨ?" },
  ],
  "default": [
    { icon: "📚", label: "Library Timings", question: "What are the operating hours of the Central Library?" },
    { icon: "📋", label: "Attendance Rule", question: "What is the mandatory attendance requirement and what happens if it falls below 75%?" },
    { icon: "🏢", label: "Hostel Curfew", question: "What is the in-time curfew for hostel students?" },
    { icon: "💳", label: "Fee Deadline", question: "What is the last date to pay even semester tuition fee?" },
    { icon: "📝", label: "Passing Criteria", question: "What is the minimum passing marks required in end semester examinations?" },
    { icon: "🔄", label: "Branch Change", question: "What is the minimum CGPA required for branch change after 1st year?" },
  ]
};

export default function ExampleQuestions({ onPick, currentLang = "en-US" }) {
  const examples = LOCALIZED_EXAMPLES[currentLang] || LOCALIZED_EXAMPLES["default"];

  return (
    <div className="example-questions">
      <div className="example-questions__header">
        <span className="example-questions__label">Official Document Questions</span>
        <span className="example-questions__sub">Tap to ask</span>
      </div>
      <div className="example-questions__chips">
        {examples.map((item) => (
          <button
            key={item.question}
            className="example-chip"
            onClick={() => onPick(item.question)}
            title={item.question}
          >
            <span className="chip-icon">{item.icon}</span>
            <span className="chip-text">{item.question}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
