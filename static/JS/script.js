/* ================================================================
   script.js  —  مشروع مسار  |  JavaScript فقط بدون أي CSS
   كل الـ styles موجودة في ملف  masar-components.css
───────────────────────────────────────────── */


/* ─────────────────────────────────────────────
   1. رسائل التحفيز  (Toast)
───────────────────────────────────────────── */

const MOTIVATION = {
  ar: [
    "💪 أنت على الطريق الصح، استمر!",
    "🌟 كل خطوة صغيرة تقربك من هدفك!",
    "🚀 المعرفة قوة — واصل التعلم!",
    "🎯 ركّز على هدفك، النجاح قادم!",
    "🏆 الأبطال لا يستسلمون، وأنت منهم!",
    "✨ يوم جديد، فرصة جديدة للتميز!",
    "📚 كل درس تتعلمه يفتح باباً جديداً!",
    "🔥 شغفك هو وقود نجاحك!",
    "⚡ لا تتوقف — النجاح يحب المثابرين!",
    "🌈 أنت أقرب مما تظن من حلمك!",
  ],
  en: [
    "💪 You're on the right track, keep going!",
    "🌟 Every small step brings you closer to your goal!",
    "🚀 Knowledge is power — keep learning!",
    "🎯 Stay focused, success is coming!",
    "🏆 Champions never quit — and neither do you!",
    "✨ New day, new chance to shine!",
    "📚 Every lesson opens a new door!",
    "🔥 Your passion is the fuel of your success!",
    "⚡ Don't stop — success loves the persistent!",
    "🌈 You're closer to your dream than you think!",
  ],
};

function getCurrentLang() {
  return localStorage.getItem("masar_lang") || "ar";
}

function showToast(msg) {
  const old = document.getElementById("masar-toast");
  if (old) old.remove();

  const t       = document.createElement("div");
  t.id          = "masar-toast";
  t.className   = "masar-toast";
  t.setAttribute("dir", getCurrentLang() === "ar" ? "rtl" : "ltr");
  t.textContent = msg;
  document.body.appendChild(t);

  requestAnimationFrame(() => t.classList.add("masar-toast--show"));
  setTimeout(() => {
    t.classList.remove("masar-toast--show");
    setTimeout(() => t.remove(), 600);
  }, 4200);
}

function startMotivation() {
  setTimeout(() => {
    const pool = MOTIVATION[getCurrentLang()];
    showToast(pool[Math.floor(Math.random() * pool.length)]);
  }, 2000);

  setInterval(() => {
    const pool = MOTIVATION[getCurrentLang()];
    showToast(pool[Math.floor(Math.random() * pool.length)]);
  }, 35000);
}


/* ─────────────────────────────────────────────
   2. اختبار الميول  (quiz.html)
───────────────────────────────────────────── */

function setupQuizSave() {
  const form = document.querySelector("form[action='tracks.html']");
  if (!form) return;

  form.addEventListener("submit", () => {
    const answers = {};
    ["q1", "q2", "q3"].forEach((name) => {
      document.querySelectorAll(`input[name="${name}"]`).forEach((opt, i) => {
        if (opt.checked) answers[name] = ["a", "b", "c"][i];
      });
    });
    localStorage.setItem("quizAnswers", JSON.stringify(answers));
  });
}


/* ─────────────────────────────────────────────
   3. صفحة المسارات  (tracks.html)
───────────────────────────────────────────── */

function calcRecommendedTrack() {
  const ans    = JSON.parse(localStorage.getItem("quizAnswers") || "{}");
  const scores = { web: 0, mobile: 0, data: 0 };
  const map    = { a: "web", b: "mobile", c: "data" };
  ["q1", "q2", "q3"].forEach((q) => { if (map[ans[q]]) scores[map[ans[q]]]++; });
  return Object.keys(scores).reduce((a, b) => (scores[a] >= scores[b] ? a : b));
}

function renderTrackRecommendation() {
  if (!document.querySelector(".choices-container")) return;

  const track = calcRecommendedTrack();
  const lang  = getCurrentLang();

  /* بنر التوصية */
  const banner      = document.createElement("div");
  banner.id         = "track-rec-banner";
  banner.className  = "track-rec-banner";
  const { h, p }    = INFO[track][lang];
  banner.innerHTML  = `<h2 class="track-rec-title">${h}</h2><p class="track-rec-desc">${p}</p>`;

  const container = document.querySelector(".choices-container");
  container.parentNode.insertBefore(banner, container);

  /* تمييز الكارد الأنسب */
  const KEYWORDS = {
    web:    ["ويب", "Web"],
    mobile: ["جوال", "Mobile", "تطبيق"],
    data:   ["بيانات", "Data"],
  };

  document.querySelectorAll(".option-circle").forEach((card) => {
    const txt = card.textContent;
    if (KEYWORDS[track].some((kw) => txt.includes(kw))) {
      card.classList.add("recommended-card");
      const badge       = document.createElement("span");
      badge.className   = `recommended-badge ${lang === "ar" ? "badge--rtl" : "badge--ltr"}`;
      badge.textContent = lang === "ar" ? "🎯 الأنسب لك" : "🎯 Best for you";
      card.appendChild(badge);
    }
  });
}
const quizForm = document.querySelector(".quiz-container form");
if (quizForm) {
    quizForm.addEventListener("submit", function (e) {
        const q1 = document.querySelector('input[name="q1"]:checked');
        const q2 = document.querySelector('input[name="q2"]:checked');
        const q3 = document.querySelector('input[name="q3"]:checked');
        if (!q1 || !q2 || !q3) {
            e.preventDefault();
            alert("من فضلك أجب على كل الأسئلة 😊");
        }
        // لو الإجابات موجودة، الفورم بيتبعت لـ Flask تلقائياً
    });
}

/* ─────────────────────────────────────────────
   4. الامتحانات النهائية
      final-exam.html / app_q.html / data_q.html
───────────────────────────────────────────── */

function setupExamScoring() {
  const form =
    document.querySelector("form[action='result.html']") ||
    document.querySelector("form[action='payment.html']");
  if (!form) return;

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const keys    = ["q1", "q2", "q3", "q8", "q9", "q10", "q15", "q16"];
    let   correct = 0;
    keys.forEach((k) => {
      const el = form.querySelector(`input[name="${k}"]:checked`);
      if (el && el.value === "1") correct++;
    });
    const total   = keys.length;
    const percent = Math.round((correct / total) * 100);
    localStorage.setItem("examResult", JSON.stringify({ correct, total, percent }));
    /* تسجيل النتيجة في البروفايل فوراً */
    var examName = document.title || "اختبار";
    recordExamResult(examName, percent);
    window.location.href = form.getAttribute("action");
  });
}


/* ─────────────────────────────────────────────
   5. صفحة النتيجة  (result.html)
───────────────────────────────────────────── */

function renderExamResult() {
  const scoreEl = document.querySelector(".stat__number");
  if (!scoreEl) return;

  const data = JSON.parse(localStorage.getItem("examResult") || "null");
  const lang = getCurrentLang();

  if (!data) {
    scoreEl.textContent = lang === "ar" ? "لا توجد نتيجة محفوظة" : "No saved result";
    return;
  }

  const { correct, total, percent } = data;
  scoreEl.textContent = lang === "ar"
    ? `درجتك: ${correct} / ${total}  (${percent}%)`
    : `Your Score: ${correct} / ${total}  (${percent}%)`;

  let msg = "";
  if (lang === "ar") {
    if      (percent >= 90) msg = "🏆 ممتاز! أداء استثنائي!";
    else if (percent >= 75) msg = "🌟 جيد جداً! استمر في التقدم!";
    else if (percent >= 60) msg = "👍 جيد، راجع بعض المفاهيم وستصل!";
    else                    msg = "📚 لا تيأس، راجع المحتوى وحاول مرة أخرى!";
  } else {
    if      (percent >= 90) msg = "🏆 Excellent! Outstanding performance!";
    else if (percent >= 75) msg = "🌟 Very Good! Keep progressing!";
    else if (percent >= 60) msg = "👍 Good — review a few concepts!";
    else                    msg = "📚 Don't give up — review and try again!";
  }

  let evalEl = document.getElementById("masar-eval-msg");
  if (!evalEl) {
    evalEl           = document.createElement("p");
    evalEl.id        = "masar-eval-msg";
    evalEl.className = "eval-message";
    scoreEl.insertAdjacentElement("afterend", evalEl);
  }
  evalEl.textContent = msg;

  if (!document.getElementById("masar-score-bar")) {
    const bar       = document.createElement("div");
    bar.id          = "masar-score-bar";
    bar.className   = "score-bar";
    const fill      = document.createElement("div");
    fill.id         = "masar-score-fill";
    fill.className  = "score-fill";
    bar.appendChild(fill);
    evalEl.insertAdjacentElement("afterend", bar);
    setTimeout(() => (fill.style.width = percent + "%"), 200);
  }
}
/* ─────────────────────────────────────────────
   7. Chat Bot — مدعوم بالذكاء الاصطناعي (Claude AI)
───────────────────────────────────────────── */

function toggleChat() {
  const box = document.getElementById("ai-chat-container");
  if (!box) return;
  const isOpen = box.style.display === "flex";
  box.style.display = isOpen ? "none" : "flex";
  if (!isOpen) {
    const input = document.getElementById("user-query");
    if (input) input.focus();
  }
}

/* سجل المحادثة لإرساله مع كل طلب (ذاكرة المحادثة) */
const chatHistory = [];

async function getAIReply(userMessage) {
  const lang = getCurrentLang();

  const systemPrompt = lang === "ar"
    ? `أنت "بوت مسار الذكي"، مساعد ذكاء اصطناعي لمنصة مسار التعليمية المتخصصة في البرمجة والتكنولوجيا.
المنصة تحتوي على ثلاثة مسارات رئيسية:
1. تطوير الويب: HTML، CSS، JavaScript، React، NodeJS، PHP، SQL، Firebase
2. تطبيقات الجوال: Flutter، React Native، Kotlin، Java، Swift
3. تحليل البيانات: Python، Pandas، SQL، Power BI، Tableau

مهمتك: مساعدة الطلاب في اختيار المسار المناسب، شرح المفاهيم التقنية، وتحفيزهم على التعلم.
أجب دائماً بالعربية، بأسلوب ودود ومشجع، وبشكل مختصر وواضح (لا تزيد عن 3-4 جمل).`
    : `You are "Masar Smart Bot", an AI assistant for Masar educational platform specializing in programming and technology.
The platform has three main tracks:
1. Web Development: HTML, CSS, JavaScript, React, NodeJS, PHP, SQL, Firebase
2. Mobile Apps: Flutter, React Native, Kotlin, Java, Swift
3. Data Analysis: Python, Pandas, SQL, Power BI, Tableau

Your job: help students choose the right track, explain technical concepts, and motivate them to learn.
Always reply in English, in a friendly and encouraging tone, concisely (3-4 sentences max).`;

  /* إضافة رسالة المستخدم للتاريخ */
  chatHistory.push({ role: "user", content: userMessage });

  /* نحتفظ بآخر 10 رسائل فقط لتفادي تجاوز حد التوكنز */
  const recentHistory = chatHistory.slice(-10);

  const response = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: "claude-sonnet-4-20250514",
      max_tokens: 1000,
      system: systemPrompt,
      messages: recentHistory,
    }),
  });

  if (!response.ok) throw new Error("API error: " + response.status);

  const data = await response.json();
  const replyText = data.content.find(b => b.type === "text")?.text || "عذراً، لم أفهم سؤالك.";

  /* إضافة رد المساعد للتاريخ */
  chatHistory.push({ role: "assistant", content: replyText });

  return replyText;
}

function setupChat() {
  const sendBtn = document.getElementById("send-btn");
  const input   = document.getElementById("user-query");
  const output  = document.getElementById("chat-output");
  if (!sendBtn || !input || !output) return;

  /* ربط زر فتح/إغلاق الشات */
  const chatIcon = document.getElementById("chat-icon");
  if (chatIcon) chatIcon.addEventListener("click", toggleChat);

  async function sendMsg() {
    const q = input.value.trim();
    if (!q) return;
    const lang = getCurrentLang();
    const dir  = lang === "ar" ? "rtl" : "ltr";

    /* فقاعة المستخدم */
    const userBubble     = document.createElement("p");
    userBubble.className = "chat-bubble chat-bubble--user";
    userBubble.setAttribute("dir", dir);
    userBubble.innerHTML = `<b>${lang === "ar" ? "أنت" : "You"}:</b> ${q}`;
    output.appendChild(userBubble);
    input.value = "";
    output.scrollTop = output.scrollHeight;

    /* فقاعة "جاري الكتابة..." */
    const typingBubble     = document.createElement("p");
    typingBubble.className = "chat-bubble chat-bubble--bot chat-bubble--typing";
    typingBubble.setAttribute("dir", dir);
    typingBubble.innerHTML = `<b>🤖 ${lang === "ar" ? "مسار AI" : "Masar AI"}:</b> <span class="typing-dots">●●●</span>`;
    output.appendChild(typingBubble);
    output.scrollTop = output.scrollHeight;

    /* إلغاء تفعيل الإرسال أثناء الانتظار */
    sendBtn.disabled = true;
    input.disabled   = true;

    try {
      const reply = await getAIReply(q);
      typingBubble.innerHTML = `<b>🤖 ${lang === "ar" ? "مسار AI" : "Masar AI"}:</b> ${reply}`;
      typingBubble.classList.remove("chat-bubble--typing");
    } catch (err) {
      typingBubble.innerHTML = `<b>🤖 ${lang === "ar" ? "مسار AI" : "Masar AI"}:</b> ${
        lang === "ar" ? "عذراً، حدث خطأ. حاول مرة أخرى 🙏" : "Sorry, an error occurred. Please try again 🙏"
      }`;
      typingBubble.classList.remove("chat-bubble--typing");
      console.error("AI Chat error:", err);
    } finally {
      sendBtn.disabled = false;
      input.disabled   = false;
      input.focus();
      output.scrollTop = output.scrollHeight;
    }
  }

  sendBtn.addEventListener("click", sendMsg);
  input.addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.shiftKey) sendMsg(); });
}


/* ─────────────────────────────────────────────
   7b. أدوات فحص السيرة الذاتية  (cv-check.html)
───────────────────────────────────────────── */

function setupCvPage() {
  if (!document.getElementById("uploadZone")) return;

  /* ── Checklist ── */
  document.querySelectorAll(".check-item").forEach(function (item) {
    item.addEventListener("click", function () {
      item.classList.toggle("done");
      updateCvProgress();
    });
  });

  function updateCvProgress() {
    var items = document.querySelectorAll(".check-item");
    var done  = document.querySelectorAll(".check-item.done").length;
    var pct   = items.length ? Math.round((done / items.length) * 100) : 0;
    var fill  = document.getElementById("progressFill");
    var text  = document.getElementById("progressText");
    if (fill) fill.style.width = pct + "%";
    if (text) text.textContent = done + " / " + items.length;
    if (done === items.length && items.length > 0) {
      showToast("🎉 أحسنت! قائمة التحقق مكتملة — سيرتك جاهزة!");
    }
  }

  /* ── CV Mock bar animation ── */
  function animateBars() {
    document.querySelectorAll(".cv-mock-fill").forEach(function (fill) {
      if (fill.dataset.w) fill.style.width = fill.dataset.w + "%";
    });
  }
  var cvMock = document.getElementById("cvMock");
  if (cvMock) {
    var barObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { animateBars(); barObserver.disconnect(); }
      });
    }, { threshold: 0.3 });
    barObserver.observe(cvMock);
  }

  /* ── ATS ring animation ── */
  var targetScore    = 85;
  var circumference  = 314;
  var atsRingWrap    = document.getElementById("atsRingWrap");
  if (atsRingWrap) {
    var atsObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          var offset  = circumference - (targetScore / 100) * circumference;
          var ringFill = document.getElementById("atsRingFill");
          var scoreNum = document.getElementById("atsScoreNum");
          if (ringFill) ringFill.style.strokeDashoffset = offset;
          var current = 0;
          var step    = targetScore / 60;
          var interval = setInterval(function () {
            current = Math.min(current + step, targetScore);
            if (scoreNum) scoreNum.textContent = Math.round(current);
            if (current >= targetScore) clearInterval(interval);
          }, 25);
          atsObserver.disconnect();
        }
      });
    }, { threshold: 0.4 });
    atsObserver.observe(atsRingWrap);
  }

  /* ── Upload zone: drag & drop ── */
  var zone = document.getElementById("uploadZone");
  if (zone) {
    zone.addEventListener("dragover", function (e) {
      e.preventDefault();
      zone.classList.add("dragover");
    });
    zone.addEventListener("dragleave", function () {
      zone.classList.remove("dragover");
    });
    zone.addEventListener("drop", function (e) {
      e.preventDefault();
      zone.classList.remove("dragover");
      var file = e.dataTransfer.files[0];
      if (file && file.type === "application/pdf") {
        var fileInput = document.getElementById("cvFileInput");
        if (fileInput) {
          /* نعيّن الملف عبر DataTransfer */
          var dt = new DataTransfer();
          dt.items.add(file);
          fileInput.files = dt.files;
        }
        var fileNameEl = document.getElementById("fileName");
        var fileChosen = document.getElementById("fileChosen");
        if (fileNameEl) fileNameEl.textContent = file.name;
        if (fileChosen) fileChosen.style.display = "block";
        showToast("📄 تم اختيار: " + file.name);
      } else {
        showToast("⚠️ من فضلك ارفع ملف PDF فقط");
      }
    });
  }

  /* ── AI CV Analyzer ── */
  setupCvAiAnalyzer();
}

/* تحليل السيرة الذاتية بالـ AI */
function setupCvAiAnalyzer() {
  var fileInput    = document.getElementById("cvFileInput");
  var analyzeBtn   = document.getElementById("ai-analyze-btn");
  var analyzeResult = document.getElementById("ai-analyze-result");

  if (!fileInput || !analyzeBtn || !analyzeResult) return;

  analyzeBtn.addEventListener("click", async function () {
    var file = fileInput.files[0];
    if (!file) {
      showToast("📎 من فضلك ارفع ملف PDF أولاً");
      return;
    }

    analyzeBtn.disabled  = true;
    analyzeBtn.textContent = "⏳ جاري التحليل...";
    analyzeResult.style.display = "block";
    analyzeResult.innerHTML = '<div class="ai-thinking">🤖 جاري تحليل سيرتك الذاتية...</div>';

    try {
      /* قراءة الـ PDF كـ base64 */
      var base64 = await fileToBase64(file);

      var response = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: "claude-sonnet-4-20250514",
          max_tokens: 1000,
          messages: [{
            role: "user",
            content: [
              {
                type: "document",
                source: {
                  type: "base64",
                  media_type: "application/pdf",
                  data: base64,
                }
              },
              {
                type: "text",
                text: `أنت خبير في تقييم السير الذاتية للوظائف التقنية في مجال البرمجة.
حلل هذه السيرة الذاتية وأعطِني:

1. **النقاط القوية** (2-3 نقاط)
2. **نقاط تحتاج تحسين** (2-3 نقاط)
3. **تقييم ATS** (من 100) مع تبرير
4. **أهم توصية** واحدة لتحسين السيرة فوراً

أجب بالعربية، بأسلوب مختصر وعملي ومباشر. استخدم إيموجي للتوضيح.`
              }
            ]
          }],
        }),
      });

      if (!response.ok) throw new Error("API error " + response.status);

      var data = await response.json();
      var reply = data.content.find(function (b) { return b.type === "text"; })?.text || "لم يتمكن من التحليل.";

      /* تحويل Markdown بسيط لـ HTML */
      var formatted = reply
        .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
        .replace(/\n\n/g, "<br><br>")
        .replace(/\n/g, "<br>");

      analyzeResult.innerHTML = '<div class="ai-cv-result">' + formatted + '</div>';
      showToast("✅ اكتمل تحليل سيرتك الذاتية!");

    } catch (err) {
      analyzeResult.innerHTML = '<div class="ai-cv-error">⚠️ حدث خطأ أثناء التحليل. تأكد من رفع ملف PDF صحيح وحاول مجدداً.</div>';
      console.error("CV AI Error:", err);
    } finally {
      analyzeBtn.disabled    = false;
      analyzeBtn.textContent = "🤖 تحليل بالذكاء الاصطناعي";
    }
  });
}

/* مساعد: تحويل ملف لـ base64 */
function fileToBase64(file) {
  return new Promise(function (resolve, reject) {
    var reader = new FileReader();
    reader.onload  = function (e) { resolve(e.target.result.split(",")[1]); };
    reader.onerror = function ()  { reject(new Error("فشل قراءة الملف")); };
    reader.readAsDataURL(file);
  });
}

/* دالة fileChosen المستخدَمة في cv-check.html */
function fileChosen(input) {
  if (input.files[0]) {
    var fileName  = document.getElementById("fileName");
    var fileChosen = document.getElementById("fileChosen");
    if (fileName)  fileName.textContent = input.files[0].name;
    if (fileChosen) fileChosen.style.display = "block";
  }
}


/* ─────────────────────────────────────────────
   8. صفحة الأدمن  (admin.html)
───────────────────────────────────────────── */

function setupAdminPage() {
  if (!document.getElementById("students-tbody")) return;

  /* ── chat icon click ── */
  const chatIcon = document.getElementById("chat-icon");
  if (chatIcon) chatIcon.addEventListener("click", toggleChat);

  /* ── chat send ── */
  const sendBtn = document.getElementById("send-btn");
  const input   = document.getElementById("user-query");
  const output  = document.getElementById("chat-output");

  function sendMsg() {
    const q = input.value.trim();
    if (!q) return;
    output.innerHTML += '<p class="chat-bubble chat-bubble--user"><b>أنت:</b> ' + q + "</p>";
    input.value = "";
    fetch("/api/chat", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ message: q, lang: "ar" }),
    })
      .then((r) => r.json())
      .then((d) => {
        output.innerHTML += '<p class="chat-bubble chat-bubble--bot"><b>🤖 البوت:</b> ' + d.reply + "</p>";
        output.scrollTop = output.scrollHeight;
      })
      .catch(() => {
        output.innerHTML += '<p class="chat-bubble chat-bubble--bot"><b>🤖 البوت:</b> حدث خطأ، حاول مرة أخرى.</p>';
      });
  }

  if (sendBtn) sendBtn.addEventListener("click", sendMsg);
  if (input)   input.addEventListener("keydown", (e) => { if (e.key === "Enter") sendMsg(); });

  /* ── تحميل بيانات الأدمن من الـ API ── */
  fetch("/api/admin-stats")
    .then((r) => r.json())
    .then((d) => {
      document.getElementById("stat-total").textContent   = d.stats.total;
      document.getElementById("stat-paid").textContent    = d.stats.paid;
      document.getElementById("stat-pending").textContent = d.stats.pending;
      document.getElementById("stat-exams").textContent   = d.stats.exams;
      document.getElementById("stat-avg").textContent     = d.stats.avg + "%";
      document.getElementById("stat-revenue").textContent = (d.stats.paid * 50) + " ج";

      const tbody = document.getElementById("students-tbody");
      tbody.innerHTML = "";
      d.students.forEach((s) => {
        const badge  = s.is_paid
          ? '<span class="badge badge-paid">مدفوع</span>'
          : '<span class="badge badge-free">مجاني</span>';
        const btnTxt = s.is_paid ? "إلغاء" : "تفعيل";
        tbody.innerHTML += `
          <tr>
            <td>${s.id}</td>
            <td>${s.full_name}</td>
            <td style="font-size:.85rem">${s.email}</td>
            <td style="font-size:.8rem;color:#888">${s.joined_at.slice(0, 10)}</td>
            <td>${badge}</td>
            <td>
              <button class="btn-modern" style="padding:4px 12px;font-size:.78rem"
                data-uid="${s.id}">${btnTxt}</button>
            </td>
          </tr>`;
      });

      /* تفعيل أزرار تغيير الحالة بعد ما الجدول يتملى */
      tbody.addEventListener("click", (e) => {
        const btn = e.target.closest("button[data-uid]");
        if (!btn) return;
        togglePayment(btn.dataset.uid, btn);
      });
    })
    .catch(() => console.warn("تعذّر تحميل بيانات الأدمن"));
}

function togglePayment(uid, btn) {
  fetch("/admin/toggle-payment/" + uid, { method: "POST" })
    .then(() => {
      const isPaid    = btn.textContent.trim() === "إلغاء";
      const row       = btn.closest("tr");
      const badgeCell = row.querySelector("td:nth-child(5)");
      if (isPaid) {
        badgeCell.innerHTML = '<span class="badge badge-free">مجاني</span>';
        btn.textContent = "تفعيل";
      } else {
        badgeCell.innerHTML = '<span class="badge badge-paid">مدفوع</span>';
        btn.textContent = "إلغاء";
      }
    })
    .catch(() => alert("حدث خطأ أثناء تغيير الحالة"));
}


/* ─────────────────────────────────────────────
   9. نظام البروفايل الكامل  (profile.html)
   — كل حاجة بتعملها في الموقع تتعكس هنا
───────────────────────────────────────────── */

/* ── قراءة وحفظ بيانات البروفايل ── */
function getProfileStats() {
  var def = { videos: 0, exams: 0, scores: [], streak: 0, lastLogin: "", activities: [] };
  try { return Object.assign(def, JSON.parse(localStorage.getItem("masar_stats") || "{}")); }
  catch (_) { return def; }
}

function saveProfileStats(st) {
  localStorage.setItem("masar_stats", JSON.stringify(st));
}

function calcAvgScore(scores) {
  if (!scores || scores.length === 0) return null;
  return Math.round(scores.reduce(function (a, b) { return a + b; }, 0) / scores.length);
}

/* ── إضافة نشاط للسجل ── */
function addActivity(name, type, score) {
  var st  = getProfileStats();
  var now = new Date();
  var timeStr = now.getHours() + ":" + String(now.getMinutes()).padStart(2, "0");
  st.activities.unshift({ name: name, type: type, score: score, time: timeStr, date: now.toDateString() });
  if (st.activities.length > 20) st.activities = st.activities.slice(0, 20);
  saveProfileStats(st);
}

/* ── streak: يوم جديد يزيد العداد ── */
function updateStreak() {
  var st      = getProfileStats();
  var today   = new Date().toDateString();
  if (st.lastLogin === today) return;
  var yesterday = new Date(Date.now() - 86400000).toDateString();
  st.streak     = (st.lastLogin === yesterday) ? st.streak + 1 : 1;
  st.lastLogin  = today;
  saveProfileStats(st);
}

/* ── فحص وتفعيل الشارات ── */
function checkBadges(st) {
  var earned = [];

  function unlock(id) {
    var el = document.getElementById(id);
    if (el && !el.classList.contains("earned")) {
      el.classList.add("earned");
      earned.push(el.querySelector(".badge-name").textContent);
    }
  }

  if (st.videos  >= 1)  unlock("badge-first-video");
  if (st.videos  >= 5)  unlock("badge-five-videos");
  if (st.exams   >= 1)  unlock("badge-first-exam");
  if (st.streak  >= 3)  unlock("badge-streak3");
  if (st.streak  >= 7)  unlock("badge-streak7");

  var avg = calcAvgScore(st.scores);
  if (avg !== null && avg >= 90) unlock("badge-highavg");
  if (st.scores.some(function (s) { return s === 100; })) unlock("badge-perfect");

  /* عدّ الشارات المكتسبة */
  var earnedCount = document.querySelectorAll(".badge-item.earned").length;
  var badgesEl = document.getElementById("badges-count");
  if (badgesEl) badgesEl.textContent = earnedCount;

  /* Toast لو في شارة جديدة */
  earned.forEach(function (name) {
    showToast("🏅 شارة جديدة: " + name + "!");
  });
}

/* ── تحديث واجهة البروفايل ── */
function refreshProfileUI() {
  var videosEl = document.getElementById("card__desc");
  if (!videosEl) return;

  var st  = getProfileStats();
  var avg = calcAvgScore(st.scores);

  videosEl.textContent                             = st.videos;
  document.getElementById("exam-done").textContent = st.exams;
  document.getElementById("avg-score").textContent = avg !== null ? avg + "%" : "—";
  document.getElementById("streak-days").textContent = st.streak;

  /* الأنشطة الأخيرة */
  var list = document.getElementById("activity-list");
  if (list) {
    if (st.activities.length > 0) {
      list.innerHTML = "";
      st.activities.forEach(function (act) {
        var icon      = act.type === "video" ? "🎬" : "📝";
        var scoreText = act.score !== null
          ? act.score + (act.type === "exam" ? "%" : "")
          : "✅";
        list.innerHTML +=
          '<div class="activity-item">' +
            '<div class="activity-dot">' + icon + '</div>' +
            '<div class="activity-text"><strong>' + act.name + '</strong></div>' +
            '<span class="activity-time">' + act.time + ' &nbsp; ' + scoreText + '</span>' +
          '</div>';
      });
    } else {
      list.innerHTML = '<div class="empty-state">لا توجد أنشطة بعد — ابدأ التعلم الآن! 🚀</div>';
    }
  }

  /* تحريك شرائط التقدم */
  setTimeout(function () {
    document.querySelectorAll(".track-fill").forEach(function (bar) {
      if (bar.dataset.value) bar.style.width = bar.dataset.value + "%";
    });
  }, 300);

  /* الشارات */
  checkBadges(st);
}

/* ── قراءة نتيجة الامتحان من examResult ── */
function syncExamToProfile() {
  var raw = localStorage.getItem("examResult");
  if (!raw) return;
  try {
    var data     = JSON.parse(raw);
    var recorded = JSON.parse(localStorage.getItem("masar_recorded_exams") || "[]");
    var key      = data.percent + "_" + data.correct + "_" + data.total;
    if (recorded.indexOf(key) !== -1) return;
    recorded.push(key);
    localStorage.setItem("masar_recorded_exams", JSON.stringify(recorded));

    var st = getProfileStats();
    st.exams += 1;
    st.scores.push(data.percent);
    saveProfileStats(st);
    addActivity("اختبار", "exam", data.percent);
  } catch (_) {}
}

/* ── صورة البروفايل ── */
function setupProfileAvatar() {
  var avatarImg   = document.getElementById("profile-avatar");
  var avatarInput = document.getElementById("avatar-input");
  if (!avatarImg || !avatarInput) return;

  avatarImg.addEventListener("click", function () { avatarInput.click(); });
  avatarInput.addEventListener("change", function () {
    var file = this.files[0];
    if (!file) return;

    /* عرض مؤقت فوري */
    var reader = new FileReader();
    reader.onload = function (e) { avatarImg.src = e.target.result; };
    reader.readAsDataURL(file);

    /* رفع للسيرفر */
    var formData = new FormData();
    formData.append("avatar", file);
    fetch("/upload-avatar", { method: "POST", body: formData })
      .then(function(r) { return r.json(); })
      .then(function(data) {
        if (data.ok) {
          avatarImg.src = "/static/uploads/" + data.filename + "?t=" + Date.now();
        }
      })
      .catch(function() { console.warn("فشل رفع الصورة"); });
  });
}

/* ── فيديوهات: عداد + منع التشغيل المتزامن ── */
function setupProfileVideos() {
  var videos  = document.querySelectorAll("video");
  if (!videos.length) return;

  var watched = JSON.parse(localStorage.getItem("masar_watched_videos") || "[]");

  videos.forEach(function (vid) {

    /* منع التشغيل المتزامن */
    vid.addEventListener("play", function () {
      videos.forEach(function (other) {
        if (other !== vid && !other.paused) other.pause();
      });
    });

    /* عدّ الفيديو لما يوصل 80% */
    vid.addEventListener("timeupdate", function () {
      if (!vid.duration) return;
      var vidId = vid.id || vid.currentSrc;
      if (watched.indexOf(vidId) !== -1) return;
      if (vid.currentTime / vid.duration >= 0.8) {
        watched.push(vidId);
        localStorage.setItem("masar_watched_videos", JSON.stringify(watched));

        var st = getProfileStats();
        st.videos += 1;
        saveProfileStats(st);

        /* اسم الفيديو من العنصر اللي فوقيه */
        var titleEl = vid.closest(".video-item") && vid.closest(".video-item").querySelector("p");
        var title   = titleEl ? titleEl.textContent : "فيديو";
        addActivity(title, "video", null);
        refreshProfileUI();
        showToast("🎬 أحسنت! أكملت مشاهدة: " + title);
      }
    });
  });
}

/* ── تشغيل كل حاجة في البروفايل ── */
function setupProfilePage() {
  if (!document.getElementById("card__desc")) return;
  updateStreak();
  syncExamToProfile();
  setupProfileAvatar();
  setupProfileVideos();
  refreshProfileUI();
}

/* دالة عامة تُستدعى من أي صفحة امتحان بعد الإنهاء */
function recordExamResult(examName, percent) {
  var st = getProfileStats();
  st.exams += 1;
  st.scores.push(percent);
  saveProfileStats(st);
  addActivity(examName || "اختبار", "exam", percent);
}

/* دالة عامة تُستدعى من أي صفحة دروس لما الطالب يكمل فيديو */
function recordVideoWatch(videoTitle) {
  var watched = JSON.parse(localStorage.getItem("masar_watched_videos") || "[]");
  var key = videoTitle || "فيديو";
  if (watched.indexOf(key) !== -1) return;
  watched.push(key);
  localStorage.setItem("masar_watched_videos", JSON.stringify(watched));
  var st = getProfileStats();
  st.videos += 1;
  saveProfileStats(st);
  addActivity(key, "video", null);
  showToast("🎬 أحسنت! أكملت مشاهدة: " + key);
}


/* ─────────────────────────────────────────────
   INIT
───────────────────────────────────────────── */

document.addEventListener("DOMContentLoaded", () => {
  startMotivation();
  setupQuizSave();
  renderTrackRecommendation();
  setupExamScoring();
  renderExamResult();
  if (getCurrentLang() === "en") applyLang("en");
  setupChat();
  setupAdminPage();
  setupProfilePage();
  setupCvPage();
});

/* ─────────────────────────────────────────────
   10. مودال تعديل الملف الشخصي
───────────────────────────────────────────── */

function setupEditModal() {
  var openBtn  = document.getElementById("open-edit-modal");
  var modal    = document.getElementById("edit-modal");
  var closeBtn = document.getElementById("close-edit-modal");
  var closeBtn2= document.getElementById("close-edit-modal-2");
  if (!openBtn || !modal) return;

  /* فتح المودال */
  openBtn.addEventListener("click", function () {
    modal.style.display = "flex";
    document.body.style.overflow = "hidden";
  });

  /* إغلاق بالزر */
  function closeModal() {
    modal.style.display = "none";
    document.body.style.overflow = "";
  }
  if (closeBtn)  closeBtn.addEventListener("click",  closeModal);
  if (closeBtn2) closeBtn2.addEventListener("click", closeModal);

  /* إغلاق بالضغط خارج الصندوق */
  modal.addEventListener("click", function (e) {
    if (e.target === modal) closeModal();
  });

  /* زر المشاركة */
  var shareBtn = document.getElementById("btn-share-profile");
  if (shareBtn) {
    shareBtn.addEventListener("click", function () {
      if (navigator.share) {
        navigator.share({ title: "ملفي الشخصي على مسار", url: window.location.href });
      } else {
        navigator.clipboard.writeText(window.location.href);
        showToast("🔗 تم نسخ رابط الملف الشخصي!");
      }
    });
  }
}

/* ─────────────────────────────────────────────
   11. قائمة المتصدّرين من localStorage
───────────────────────────────────────────── */

function renderLeaderboard() {
  var container = document.getElementById("leaderboard-list");
  if (!container) return;

  /* بنجمع كل الطلاب من الـ localStorage — كل طالب بيحفظ باسمه */
  var st     = getProfileStats();
  var myName = document.getElementById("student-name");
  var name   = myName ? myName.textContent.trim() : "أنت";
  var myAvg  = calcAvgScore(st.scores) || 0;

  /* نعرض الطالب الحالي فوق */
  container.innerHTML =
    '<div class="info-row" style="font-weight:700">' +
      '<span>🥇</span>' +
      '<span>' + name + '</span>' +
      '<span style="margin-right:auto;color:#5ce1e6;font-weight:700;">' + myAvg + ' نقطة</span>' +
    '</div>' +
    '<div style="color:#555;font-size:0.75rem;text-align:center;margin-top:8px">سيظهر باقي المتصدّرين قريباً</div>';
}

/* ─────────────────────────────────────────────
   تشغيل الإضافات الجديدة ضمن DOMContentLoaded
───────────────────────────────────────────── */
document.addEventListener("DOMContentLoaded", function () {
  setupEditModal();
  renderLeaderboard();
});


/* ─────────────────────────────────────────────
   12. صفحة السيرة الذاتية  (cv-check.html)
───────────────────────────────────────────── */

/* دالة عامة يستدعيها onclick في cv-check.html */
function toggleCheck(el) {
  el.classList.toggle("done");
  updateCvProgress();
}

/* ── Checklist progress ── */
function setupCvChecklist() {
  var items = document.querySelectorAll(".check-item");
  if (!items.length) return;
  updateCvProgress();
}

function updateCvProgress() {
  var items = document.querySelectorAll(".check-item");
  var done  = document.querySelectorAll(".check-item.done").length;
  var pct   = items.length ? (done / items.length) * 100 : 0;
  var fill  = document.getElementById("progressFill");
  var text  = document.getElementById("progressText");
  if (fill) fill.style.width = pct + "%";
  if (text) text.textContent = done + " / " + items.length;
}

/* ── CV Mock bars animation ── */
function setupCvMockBars() {
  var mock = document.getElementById("cvMock");
  if (!mock) return;
  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) {
        document.querySelectorAll(".cv-mock-fill").forEach(function (fill) {
          fill.style.width = (fill.dataset.w || 0) + "%";
        });
        observer.disconnect();
      }
    });
  }, { threshold: 0.3 });
  observer.observe(mock);
}

/* ── ATS ring animation ── */
function setupAtsRing() {
  var wrap = document.getElementById("atsRingWrap");
  if (!wrap) return;
  var targetScore  = 85;
  var circumference = 314;
  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) {
        var fill = document.getElementById("atsRingFill");
        var num  = document.getElementById("atsScoreNum");
        if (fill) fill.style.strokeDashoffset = circumference - (targetScore / 100) * circumference;
        var current = 0;
        var step = targetScore / 60;
        var interval = setInterval(function () {
          current = Math.min(current + step, targetScore);
          if (num) num.textContent = Math.round(current);
          if (current >= targetScore) clearInterval(interval);
        }, 25);
        observer.disconnect();
      }
    });
  }, { threshold: 0.4 });
  observer.observe(wrap);
}

/* ── ATS ring animation — نتيجة التحليل بعد رفع السيرة ── */
function setupAtsRingResult() {
  var wrap = document.getElementById("atsRingWrapResult");
  if (!wrap) return;
  var targetScore   = 88;
  var circumference = 314;
  var fill = document.getElementById("atsRingFillResult");
  var num  = document.getElementById("atsScoreNumResult");
  if (fill) {
    fill.style.strokeDasharray  = circumference;
    fill.style.strokeDashoffset = circumference;
  }
  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) {
        if (fill) fill.style.strokeDashoffset = circumference - (targetScore / 100) * circumference;
        var current = 0;
        var step = targetScore / 60;
        var interval = setInterval(function () {
          current = Math.min(current + step, targetScore);
          if (num) num.textContent = Math.round(current);
          if (current >= targetScore) clearInterval(interval);
        }, 25);
        observer.disconnect();
      }
    });
  }, { threshold: 0.3 });
  observer.observe(wrap);
}

/* ── Upload zone drag & drop ── */
function setupUploadZone() {
  var zone  = document.getElementById("uploadZone");
  var input = document.getElementById("cvFileInput");
  var chosen = document.getElementById("fileChosen");
  var nameEl = document.getElementById("fileName");
  if (!zone || !input) return;

  zone.addEventListener("click", function () { input.click(); });
  input.addEventListener("change", function () {
    if (input.files[0]) {
      if (nameEl)  nameEl.textContent = input.files[0].name;
      if (chosen)  chosen.style.display = "block";
    }
  });
  zone.addEventListener("dragover", function (e) {
    e.preventDefault();
    zone.classList.add("dragover");
  });
  zone.addEventListener("dragleave", function () {
    zone.classList.remove("dragover");
  });
  zone.addEventListener("drop", function (e) {
    e.preventDefault();
    zone.classList.remove("dragover");
    var file = e.dataTransfer.files[0];
    if (file && file.type === "application/pdf") {
      try {
        var dt = new DataTransfer();
        dt.items.add(file);
        input.files = dt.files;
      } catch (_) {}
      if (nameEl)  nameEl.textContent = file.name;
      if (chosen)  chosen.style.display = "block";
    }
  });
}

/* ─────────────────────────────────────────────
   13. AI Chat — نسخة ذكاء اصطناعي حقيقي
       تستخدم Claude API مباشرةً
───────────────────────────────────────────── */

/**
 * setupAiChat()
 * يُفعّل الشات بوت في صفحة cv-check باستخدام Claude API.
 * يعمل بدلاً من getBotReply() الذي يستخدم ردوداً ثابتة.
 *
 * المتطلبات في HTML:
 *   #chat-icon          → زرار فتح الشات
 *   #ai-chat-container  → صندوق الشات
 *   #chat-output        → منطقة الرسائل
 *   #user-query         → حقل الإدخال
 *   #send-btn           → زرار الإرسال
 */

var cvChatHistory = [];   /* سجل المحادثة لإرساله لـ Claude */

var CV_SYSTEM_PROMPT = [
  "أنت مساعد السيرة الذاتية الذكي لمنصة مسار التعليمية.",
  "تخصصك: مساعدة الطلاب والخريجين في:",
  "- كتابة سيرة ذاتية احترافية وفق معايير ATS",
  "- مراجعة وتحسين ملخصاتهم المهني",
  "- تنسيق الخبرات والمهارات بطريقة مؤثرة",
  "- تخصيص السيرة لكل وظيفة",
  "- اجتياز فلاتر التوظيف الآلي",
  "أجب دائماً بالعربية ما لم يكتب المستخدم بالإنجليزية.",
  "كن مشجعاً وعملياً — أعط أمثلة ملموسة عندما يكون ذلك مفيداً.",
  "لا تتجاوز 200 كلمة في كل رد.",
].join("\n");

function setupAiChat() {
  var chatIcon  = document.getElementById("chat-icon");
  var container = document.getElementById("ai-chat-container");
  var output    = document.getElementById("chat-output");
  var input     = document.getElementById("user-query");
  var sendBtn   = document.getElementById("send-btn");

  /* إذا لم تكن العناصر موجودة في هذه الصفحة نخرج فوراً */
  if (!sendBtn || !input || !output) return;

  /* فتح/إغلاق الشات */
  if (chatIcon) {
    chatIcon.onclick = function () {
      if (!container) return;
      container.style.display =
        container.style.display === "flex" ? "none" : "flex";
    };
  }

  /* إرسال رسالة */
  function sendAiMsg() {
    var q = input.value.trim();
    if (!q) return;

    /* عرض رسالة المستخدم */
    var lang = getCurrentLang();
    appendBubble(output, "user", lang === "ar" ? "أنت" : "You", q, lang);
    input.value = "";

    /* إضافة الرسالة لسجل المحادثة */
    cvChatHistory.push({ role: "user", content: q });

    /* مؤشر التحميل */
    var loadingId = "cv-loading-" + Date.now();
    appendBubble(output, "bot", "🤖 مسار AI", "...", lang, loadingId);

    /* استدعاء Claude API */
    fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model:      "claude-sonnet-4-20250514",
        max_tokens: 1000,
        system:     CV_SYSTEM_PROMPT,
        messages:   cvChatHistory,
      }),
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var reply = "";
        if (data.content && data.content.length > 0) {
          data.content.forEach(function (block) {
            if (block.type === "text") reply += block.text;
          });
        } else if (data.error) {
          reply = "⚠️ " + (data.error.message || "حدث خطأ في الاتصال بالذكاء الاصطناعي");
        }

        /* تحديث فقاعة التحميل */
        var loadingEl = document.getElementById(loadingId);
        if (loadingEl) {
          loadingEl.querySelector(".bubble-text").textContent = reply;
        } else {
          appendBubble(output, "bot", "🤖 مسار AI", reply, lang);
        }

        /* حفظ رد المساعد في السجل */
        cvChatHistory.push({ role: "assistant", content: reply });

        /* الاحتفاظ بآخر 10 رسائل فقط لتجنب تجاوز حد التوكن */
        if (cvChatHistory.length > 10) {
          cvChatHistory = cvChatHistory.slice(cvChatHistory.length - 10);
        }

        output.scrollTop = output.scrollHeight;
      })
      .catch(function (err) {
        var loadingEl = document.getElementById(loadingId);
        var errMsg = "⚠️ تعذّر الاتصال بالذكاء الاصطناعي. تحقق من الاتصال وحاول مجدداً.";
        if (loadingEl) {
          loadingEl.querySelector(".bubble-text").textContent = errMsg;
        } else {
          appendBubble(output, "bot", "🤖 مسار AI", errMsg, lang);
        }
        console.error("CV AI Chat error:", err);
      });
  }

  sendBtn.addEventListener("click", sendAiMsg);
  input.addEventListener("keydown", function (e) {
    if (e.key === "Enter") sendAiMsg();
  });
}

/* مساعدة: إضافة فقاعة رسالة */
function appendBubble(output, who, label, text, lang, id) {
  var dir = (lang === "ar") ? "rtl" : "ltr";
  var cls = who === "user" ? "chat-bubble--user" : "chat-bubble--bot";
  var p   = document.createElement("p");
  p.className = "chat-bubble " + cls;
  p.setAttribute("dir", dir);
  if (id) p.id = id;
  p.innerHTML = "<b>" + label + ":</b> <span class='bubble-text'>" + text + "</span>";
  output.appendChild(p);
  output.scrollTop = output.scrollHeight;
  return p;
}

/* ─────────────────────────────────────────────
   تشغيل كل مكونات صفحة cv-check
───────────────────────────────────────────── */
document.addEventListener("DOMContentLoaded", function () {
  setupCvChecklist();
  setupCvMockBars();
  setupAtsRing();
  setupAtsRingResult();   /* ATS ring لقسم نتيجة التحليل بعد الرفع */
  setupUploadZone();
  setupAiChat();    /* الشات الذكي — يعمل فقط في الصفحات التي تحتوي على عناصر الشات */
});