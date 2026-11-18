// QuizMaster Pro - Interactive Quiz Engine

let quizState = {
    categoryId: 'all',
    categoryName: 'General',
    difficulty: 'all',
    mode: 'standard',
    limit: 10,
    questions: [],
    currentIndex: 0,
    userAnswers: {}, // { qid: { selected_option: null, time_spent: 0 } }
    flaggedQuestions: new Set(),
    timeRemaining: 30,
    timerHandle: null,
    totalQuizTime: 0,
    totalQuizTimerHandle: null,
    isSubmitting: false
};

document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('quizContainer');
    if (!container) return;

    quizState.categoryId = container.dataset.categoryId || 'all';
    quizState.categoryName = container.dataset.categoryName || 'General';
    quizState.difficulty = container.dataset.difficulty || 'all';
    quizState.mode = container.dataset.mode || 'standard';
    quizState.limit = parseInt(container.dataset.limit || '10');

    initQuiz();
    setupKeyboardShortcuts();
});

async function initQuiz() {
    try {
        const queryParams = new URLSearchParams({
            category: quizState.categoryId,
            difficulty: quizState.difficulty,
            mode: quizState.mode,
            limit: quizState.limit
        });

        const res = await fetch(`/api/quiz/questions?${queryParams.toString()}`);
        const data = await res.json();

        if (data.success && data.questions && data.questions.length > 0) {
            quizState.questions = data.questions;
            // Initialize answers state
            quizState.questions.forEach(q => {
                quizState.userAnswers[q.id] = {
                    question_id: q.id,
                    selected_option: null,
                    time_spent: 0
                };
            });

            document.getElementById('quizLoading').classList.add('hidden');
            document.getElementById('quizCard').classList.remove('hidden');

            renderPalette();
            renderQuestion(0);
            startTotalQuizTimer();
        } else {
            document.getElementById('quizLoading').innerHTML = `
                <div class="text-center py-12 space-y-4">
                    <i class="fa-solid fa-folder-open text-4xl text-slate-500"></i>
                    <h3 class="text-lg font-bold text-white">No Questions Found</h3>
                    <p class="text-xs text-slate-400">There are no questions matching this specific filter combination.</p>
                    <a href="/dashboard" class="inline-block px-5 py-2.5 rounded-xl bg-brand-600 text-white font-bold text-xs">
                        Back to Dashboard
                    </a>
                </div>
            `;
        }
    } catch (err) {
        console.error('Failed to load quiz questions:', err);
    }
}

function startTotalQuizTimer() {
    quizState.totalQuizTimerHandle = setInterval(() => {
        quizState.totalQuizTime++;
    }, 1000);
}

function renderQuestion(index) {
    if (index < 0 || index >= quizState.questions.length) return;
    quizState.currentIndex = index;
    const q = quizState.questions[index];

    // Update Progress
    const total = quizState.questions.length;
    const currentNum = index + 1;
    const pct = Math.round((currentNum / total) * 100);

    document.getElementById('questionProgressText').textContent = `Question ${currentNum} of ${total}`;
    document.getElementById('progressPercentageText').textContent = `${pct}%`;
    document.getElementById('progressBar').style.width = `${pct}%`;

    // Metadata
    document.getElementById('qPointsBadge').textContent = `+${q.points || 10} Points`;
    document.getElementById('qDifficultyLabel').textContent = q.difficulty || 'Medium';

    // Question Text
    document.getElementById('questionText').textContent = q.question_text;

    // Code Snippet Box
    const codeBox = document.getElementById('codeSnippetBox');
    const codeContent = document.getElementById('codeSnippetContent');
    if (q.code_snippet && q.code_snippet.trim() !== '') {
        codeContent.textContent = q.code_snippet;
        codeBox.classList.remove('hidden');
    } else {
        codeBox.classList.add('hidden');
    }

    // Flag Status
    updateFlagButton();

    // Render 4 Options
    const optionsContainer = document.getElementById('optionsContainer');
    optionsContainer.innerHTML = '';

    const options = [
        { key: 'A', text: q.option_a },
        { key: 'B', text: q.option_b },
        { key: 'C', text: q.option_c },
        { key: 'D', text: q.option_d }
    ];

    const currentSelected = quizState.userAnswers[q.id]?.selected_option;

    options.forEach(opt => {
        const isSelected = (currentSelected === opt.key);
        const card = document.createElement('div');
        card.className = `p-4 rounded-2xl border transition-all cursor-pointer flex items-center justify-between select-none ${
            isSelected 
                ? 'bg-brand-600/20 border-brand-500 text-white shadow-lg shadow-brand-500/20 ring-1 ring-brand-500' 
                : 'bg-slate-950/70 border-slate-800 text-slate-200 hover:bg-slate-800/80 hover:border-slate-700'
        }`;

        card.onclick = () => selectOption(q.id, opt.key);

        card.innerHTML = `
            <div class="flex items-center gap-3.5">
                <div class="w-8 h-8 rounded-xl flex items-center justify-center font-bold text-xs uppercase ${
                    isSelected ? 'bg-brand-500 text-white' : 'bg-slate-800 text-slate-400 border border-slate-700'
                }">
                    ${opt.key}
                </div>
                <span class="text-sm font-medium leading-relaxed">${escapeHtml(opt.text)}</span>
            </div>
            <div class="text-sm ${isSelected ? 'text-brand-400' : 'text-transparent'}">
                <i class="fa-solid fa-circle-check"></i>
            </div>
        `;

        optionsContainer.appendChild(card);
    });

    // Update Bottom Nav Buttons
    document.getElementById('prevBtn').disabled = (index === 0);

    const nextBtn = document.getElementById('nextBtn');
    const submitBtn = document.getElementById('submitBtn');

    if (index === total - 1) {
        nextBtn.classList.add('hidden');
        submitBtn.classList.remove('hidden');
    } else {
        nextBtn.classList.remove('hidden');
        submitBtn.classList.add('hidden');
    }

    // Start Question Timer
    startQuestionTimer(q.time_limit_seconds || 30);
    renderPalette();
}

function startQuestionTimer(durationSeconds) {
    clearInterval(quizState.timerHandle);
    quizState.timeRemaining = durationSeconds;
    updateTimerDisplay();

    quizState.timerHandle = setInterval(() => {
        const qid = quizState.questions[quizState.currentIndex].id;
        if (quizState.userAnswers[qid]) {
            quizState.userAnswers[qid].time_spent++;
        }

        quizState.timeRemaining--;
        updateTimerDisplay();

        if (quizState.timeRemaining <= 5 && quizState.timeRemaining > 0) {
            playTickSound();
        }

        if (quizState.timeRemaining <= 0) {
            clearInterval(quizState.timerHandle);
            handleQuestionTimeout();
        }
    }, 1000);
}

function updateTimerDisplay() {
    const mins = Math.floor(quizState.timeRemaining / 60);
    const secs = quizState.timeRemaining % 60;
    const formatted = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    const display = document.getElementById('timerDisplay');
    const box = document.getElementById('timerBox');
    const icon = document.getElementById('timerIcon');

    if (display) display.textContent = formatted;

    if (box && icon) {
        if (quizState.timeRemaining <= 5) {
            box.className = 'flex items-center gap-2 bg-rose-950/60 px-4 py-2 rounded-xl border border-rose-500/50 shadow-inner animate-pulse';
            display.className = 'text-lg font-extrabold text-rose-400 font-mono';
            icon.className = 'fa-solid fa-hourglass-end text-rose-400 text-sm';
        } else if (quizState.timeRemaining <= 12) {
            box.className = 'flex items-center gap-2 bg-amber-950/40 px-4 py-2 rounded-xl border border-amber-500/40 shadow-inner';
            display.className = 'text-lg font-extrabold text-amber-400 font-mono';
            icon.className = 'fa-solid fa-clock text-amber-400 text-sm';
        } else {
            box.className = 'flex items-center gap-2 bg-slate-950 px-4 py-2 rounded-xl border border-slate-800 shadow-inner';
            display.className = 'text-lg font-extrabold text-white font-mono';
            icon.className = 'fa-solid fa-clock text-indigo-400 text-sm';
        }
    }
}

function handleQuestionTimeout() {
    playTimeoutSound();
    // Auto advance if more questions remain
    if (quizState.currentIndex < quizState.questions.length - 1) {
        nextQuestion();
    } else {
        // Last question timed out -> auto confirm submit
        confirmSubmitQuiz();
    }
}

function selectOption(qid, optionKey) {
    if (!quizState.userAnswers[qid]) {
        quizState.userAnswers[qid] = { question_id: qid, selected_option: optionKey, time_spent: 0 };
    } else {
        quizState.userAnswers[qid].selected_option = optionKey;
    }

    playSelectSound();
    renderQuestion(quizState.currentIndex);
}

function toggleFlagCurrentQuestion() {
    const qid = quizState.questions[quizState.currentIndex].id;
    if (quizState.flaggedQuestions.has(qid)) {
        quizState.flaggedQuestions.delete(qid);
    } else {
        quizState.flaggedQuestions.add(qid);
    }
    updateFlagButton();
    renderPalette();
}

function updateFlagButton() {
    const qid = quizState.questions[quizState.currentIndex]?.id;
    const isFlagged = quizState.flaggedQuestions.has(qid);
    const flagBtn = document.getElementById('flagBtn');
    const flagIcon = document.getElementById('flagIcon');
    const flagText = document.getElementById('flagText');

    if (isFlagged) {
        flagBtn.className = 'flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold text-amber-400 bg-amber-500/10 border border-amber-500/30 transition-colors';
        flagIcon.className = 'fa-solid fa-bookmark text-amber-400';
        flagText.textContent = 'Flagged';
    } else {
        flagBtn.className = 'flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold text-slate-400 hover:text-amber-400 bg-slate-800/80 hover:bg-slate-800 border border-slate-700 transition-colors';
        flagIcon.className = 'fa-regular fa-bookmark';
        flagText.textContent = 'Review Later';
    }
}

function nextQuestion() {
    if (quizState.currentIndex < quizState.questions.length - 1) {
        renderQuestion(quizState.currentIndex + 1);
    }
}

function prevQuestion() {
    if (quizState.currentIndex > 0) {
        renderQuestion(quizState.currentIndex - 1);
    }
}

function jumpToQuestion(index) {
    renderQuestion(index);
}

function toggleQuestionPalette() {
    const drawer = document.getElementById('questionPaletteDrawer');
    drawer.classList.toggle('hidden');
}

function renderPalette() {
    const grid = document.getElementById('paletteGrid');
    if (!grid) return;
    grid.innerHTML = '';

    quizState.questions.forEach((q, idx) => {
        const isAnswered = Boolean(quizState.userAnswers[q.id]?.selected_option);
        const isFlagged = quizState.flaggedQuestions.has(q.id);
        const isCurrent = (idx === quizState.currentIndex);

        const btn = document.createElement('button');
        btn.onclick = () => jumpToQuestion(idx);

        let bgClass = 'bg-slate-800 text-slate-400 border border-slate-700';
        if (isCurrent) {
            bgClass = 'ring-2 ring-indigo-400 bg-indigo-600 text-white font-bold';
        } else if (isFlagged) {
            bgClass = 'bg-amber-500/20 text-amber-300 border border-amber-500/40 font-bold';
        } else if (isAnswered) {
            bgClass = 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 font-bold';
        }

        btn.className = `h-9 rounded-xl text-xs flex items-center justify-center transition-all hover:scale-105 relative ${bgClass}`;
        btn.innerHTML = `
            ${idx + 1}
            ${isFlagged ? '<span class="absolute top-1 right-1 w-1.5 h-1.5 rounded-full bg-amber-400"></span>' : ''}
        `;
        grid.appendChild(btn);
    });
}

function confirmSubmitQuiz() {
    let answered = 0;
    let unanswered = 0;

    quizState.questions.forEach(q => {
        if (quizState.userAnswers[q.id]?.selected_option) {
            answered++;
        } else {
            unanswered++;
        }
    });

    document.getElementById('modalAnsweredCount').textContent = answered;
    document.getElementById('modalUnansweredCount').textContent = unanswered;
    document.getElementById('modalFlaggedCount').textContent = quizState.flaggedQuestions.size;

    document.getElementById('submitModal').classList.remove('hidden');
}

function closeSubmitModal() {
    document.getElementById('submitModal').classList.add('hidden');
}

async function finalizeAndSubmit() {
    if (quizState.isSubmitting) return;
    quizState.isSubmitting = true;

    clearInterval(quizState.timerHandle);
    clearInterval(quizState.totalQuizTimerHandle);

    const btn = document.getElementById('finalizeSubmitBtn');
    btn.innerHTML = `<i class="fa-solid fa-spinner animate-spin mr-1"></i> Calculating Score...`;
    btn.disabled = true;

    const payload = {
        category_id: quizState.categoryId,
        category_name: quizState.categoryName,
        difficulty: quizState.difficulty,
        answers: Object.values(quizState.userAnswers),
        time_taken_seconds: quizState.totalQuizTime
    };

    try {
        const res = await fetch('/api/quiz/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (data.success && data.redirect_url) {
            playFanfareSound();
            window.location.href = data.redirect_url;
        } else {
            alert('Failed to submit quiz: ' + (data.message || 'Unknown error'));
            quizState.isSubmitting = false;
            btn.innerHTML = 'Confirm & Submit';
            btn.disabled = false;
        }
    } catch (err) {
        console.error('Submission error:', err);
        alert('Connection error submitting quiz.');
        quizState.isSubmitting = false;
        btn.innerHTML = 'Confirm & Submit';
        btn.disabled = false;
    }
}

function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // Ignore if user is typing in an input
        if (['INPUT', 'TEXTAREA'].includes(e.target.tagName)) return;

        const currentQ = quizState.questions[quizState.currentIndex];
        if (!currentQ) return;

        if (['1', 'a', 'A'].includes(e.key)) {
            selectOption(currentQ.id, 'A');
        } else if (['2', 'b', 'B'].includes(e.key)) {
            selectOption(currentQ.id, 'B');
        } else if (['3', 'c', 'C'].includes(e.key)) {
            selectOption(currentQ.id, 'C');
        } else if (['4', 'd', 'D'].includes(e.key)) {
            selectOption(currentQ.id, 'D');
        } else if (['f', 'F'].includes(e.key)) {
            toggleFlagCurrentQuestion();
        } else if (e.key === 'ArrowRight') {
            nextQuestion();
        } else if (e.key === 'ArrowLeft') {
            prevQuestion();
        } else if (e.key === 'Enter') {
            if (quizState.currentIndex === quizState.questions.length - 1) {
                confirmSubmitQuiz();
            } else {
                nextQuestion();
            }
        }
    });
}

function escapeHtml(text) {
    if (!text) return '';
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
